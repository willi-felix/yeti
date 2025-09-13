import socketio
from fastapi import FastAPI
from app.database import AsyncSessionLocal
from app.utils import now_ts, b64_to_bytes, bytes_to_b64, decompress_bytes
from app.filter import is_inappropriate
from app.giphy import search_gif
from app.drive import upload_bytes_to_drive, build_drive_service, list_files_in_drive
from app.notify import send_one_signal
from app.couchbase_client import upsert_archive, get_archive
import asyncio, base64, mimetypes, time
from app.models import Message, Conversation, User
from sqlalchemy import select
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
app = FastAPI()
asgi_app = socketio.ASGIApp(sio, app)

@sio.event
async def connect(sid, environ, auth):
    return

@sio.event
async def join_conversation(sid, data):
    conversation_id = data.get("conversation_id")
    sio.enter_room(sid, f"conversation_{conversation_id}")

@sio.event
async def leave_conversation(sid, data):
    conversation_id = data.get("conversation_id")
    sio.leave_room(sid, f"conversation_{conversation_id}")

@sio.event
async def send_message(sid, data):
    conversation_id = data.get("conversation_id")
    sender_uid = data.get("sender_uid")
    message_b64 = data.get("message_compressed_b64")
    iv = data.get("iv")
    mtype = data.get("message_type", "text")
    size_bytes = int(data.get("size_bytes", 0))
    attachment = data.get("attachment")
    if message_b64 is None and attachment is None:
        await sio.emit("message_blocked", {"reason":"empty_message"}, to=sid)
        return
    raw_bytes = b64_to_bytes(message_b64) if message_b64 else b""
    try:
        decompressed_for_filter = decompress_bytes(raw_bytes) if raw_bytes else b""
        text_for_filter = decompressed_for_filter.decode('utf-8', errors='ignore') if decompressed_for_filter else ""
    except Exception:
        text_for_filter = ""
    if await is_inappropriate(text_for_filter):
        await sio.emit("message_blocked", {"reason":"inappropriate_content"}, to=sid)
        return
    ts = now_ts()
    async with AsyncSessionLocal() as s:
        msg = Message(conversation_id=conversation_id, sender_uid=sender_uid, message_compressed=raw_bytes, iv=iv or "", message_type=mtype, attachment=attachment, size_bytes=size_bytes, created_at=ts)
        s.add(msg)
        await s.commit()
        await s.refresh(msg)
    await sio.emit("message_received", {"id":msg.id, "conversation_id":conversation_id, "sender_uid":sender_uid, "message_compressed_b64": base64.b64encode(raw_bytes).decode(), "iv":iv, "message_type":mtype, "attachment":attachment, "size_bytes":size_bytes, "created_at":ts}, room=f"conversation_{conversation_id}")
    send_one_signal([], f"New message in {conversation_id}", {"conversation_id":conversation_id})

@sio.event
async def send_giphy(sid, data):
    q = data.get("q")
    conv = data.get("conversation_id")
    sender = data.get("sender_uid")
    gif = search_gif(q)
    if not gif:
        await sio.emit("message_blocked", {"reason":"giphy_not_found"}, to=sid)
        return
    ts = now_ts()
    async with AsyncSessionLocal() as s:
        m = Message(conversation_id=conv, sender_uid=sender, message_compressed=b'', iv='', message_type='gif', attachment=gif, size_bytes=0, created_at=ts)
        s.add(m)
        await s.commit()
        await s.refresh(m)
    await sio.emit("message_received", {"id":m.id, "conversation_id":conv, "sender_uid":sender, "message_type":"gif", "attachment":gif, "created_at":ts}, room=f"conversation_{conv}")

@sio.event
async def retract_message(sid, data):
    message_id = data.get("message_id")
    sender = data.get("sender_uid")
    async with AsyncSessionLocal() as s:
        q = await s.execute(select(Message).where(Message.id==message_id))
        m = q.scalars().first()
        if not m or m.sender_uid != sender:
            return
        conv = m.conversation_id
        await s.execute("DELETE FROM messages WHERE id=:id", {"id":message_id})
        await s.commit()
    await sio.emit("message_retracted", {"message_id":message_id, "conversation_id":conv}, room=f"conversation_{conv}")

@sio.event
async def upload_file_to_drive(sid, data):
    sender = data.get("sender_uid")
    conversation_id = data.get("conversation_id")
    filename = data.get("filename")
    file_b64 = data.get("file_b64")
    if not (filename and file_b64):
        await sio.emit("message_blocked", {"reason":"no_file"}, to=sid)
        return
    file_bytes = base64.b64decode(file_b64)
    service = None
    attach = {"name": filename, "mime_type": mimetypes.guess_type(filename)[0] if filename else None, "size": len(file_bytes), "link": None}
    try:
        creds = None
        service = build_drive_service(creds) if creds else None
    except Exception:
        service = None
    if service:
        f = upload_bytes_to_drive(service, filename, file_bytes, mimetypes.guess_type(filename)[0] if filename else None)
        attach = {"name":f.get("name"), "mime_type":f.get("mimeType"), "size":int(f.get("size",0)), "link": f.get("webViewLink"), "drive_id": f.get("id")}
    ts = now_ts()
    async with AsyncSessionLocal() as s:
        m = Message(conversation_id=conversation_id, sender_uid=sender, message_compressed=b'', iv='', message_type='drive-link', attachment=attach, size_bytes=0, created_at=ts)
        s.add(m)
        await s.commit()
        await s.refresh(m)
    await sio.emit("message_received", {"id":m.id, "conversation_id":conversation_id, "sender_uid":sender, "message_type":"drive-link", "attachment":attach, "created_at":ts}, room=f"conversation_{conversation_id}")
