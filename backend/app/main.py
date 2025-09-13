import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from app.database import Base, engine, AsyncSessionLocal
from app.models import User, Plan, Conversation, Message, Friend, YetiCode, Archive
from app.schemas import AuthIn, UserOut, ConversationCreate, MessageIn, RetractIn
from app.auth import verify_id_token
from app.utils import now_ts, b64_to_bytes, bytes_to_b64, compress_bytes
from sqlalchemy import select
from app.socket_app import asgi_app, sio
from app.tasks import start_scheduler
app = FastAPI()
app.mount("/socket.io", asgi_app)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as s:
        r = await s.execute(select(Plan).where(Plan.name=="none"))
        p = r.scalars().first()
        if not p:
            s.add_all([Plan(name="none", quotas_mb=15, groups="pair,group"), Plan(name="mini", quotas_mb=30, groups="pair,group,group_plus"), Plan(name="plus", quotas_mb=50, groups="pair,group,group_plus,community")])
            await s.commit()
    start_scheduler()

async def get_db():
    async with AsyncSessionLocal() as s:
        yield s

@app.post("/auth/firebase", response_model=UserOut)
async def auth_firebase(body: AuthIn, db=Depends(get_db)):
    decoded = verify_id_token(body.idToken)
    firebase_uid = decoded.get("uid")
    phone = decoded.get("phone_number")
    if not phone:
        raise HTTPException(status_code=400, detail="phone_required")
    q = await db.execute(select(User).where(User.phone==phone))
    user = q.scalars().first()
    if not user:
        r = await db.execute(select(Plan).where(Plan.name=="none"))
        plan = r.scalars().first()
        ts = now_ts()
        user = User(firebase_uid=firebase_uid, phone=phone, plan_id=plan.plan_id, created_at=ts, updated_at=ts, last_used=ts)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        if body.yeti_code:
            r2 = await db.execute(select(YetiCode).where(YetiCode.code==body.yeti_code, YetiCode.used==False))
            yc = r2.scalars().first()
            if yc:
                yc.used = True
                await db.commit()
    return UserOut(uid=user.uid, phone=user.phone, display_name=user.display_name)

@app.post("/conversations/create")
async def create_conversation(req: ConversationCreate, db=Depends(get_db)):
    types_allowed = {"pair":2, "group":20, "group_plus":50, "community":1000}
    maxp = types_allowed.get(req.type, 20)
    if len(req.participant_uids) > maxp:
        raise HTTPException(status_code=400, detail="participant_limit")
    ts = now_ts()
    conv = Conversation(type=req.type, uids=req.participant_uids, title=req.title or "", leader_uid=req.participant_uids[0], created_at=ts, last_used=ts)
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return {"conversation_id": conv.id}

@app.post("/messages/send")
async def api_send_message(inp: MessageIn, db=Depends(get_db)):
    raw = b64_to_bytes(inp.message_compressed_b64)
    ts = now_ts()
    m = Message(conversation_id=inp.conversation_id, sender_uid="unknown", message_compressed=raw, iv=inp.iv or "", message_type=inp.message_type, attachment=inp.attachment, size_bytes=inp.size_bytes or 0, created_at=ts)
    db.add(m)
    await db.commit()
    await db.refresh(m)
    await sio.emit("message_received", {"id":m.id, "conversation_id":m.conversation_id, "sender_uid":m.sender_uid, "message_compressed_b64":inp.message_compressed_b64, "iv":inp.iv, "message_type":inp.message_type, "attachment":inp.attachment, "created_at":ts}, room=f"conversation_{m.conversation_id}")
    return {"ok":True, "message_id": m.id}

@app.post("/messages/retract")
async def api_retract(inp: RetractIn, db=Depends(get_db)):
    await db.execute("DELETE FROM messages WHERE id=:id", {"id": inp.message_id})
    await db.commit()
    await sio.emit("message_retracted", {"message_id": inp.message_id, "conversation_id": inp.conversation_id}, room=f"conversation_{inp.conversation_id}")
    return {"ok":True}

@app.post("/drive/list")
async def drive_list():
    return {"ok": True, "files": []}

@app.post("/giphy/search")
async def giphy_search(q: str):
    gif = search_gif(q)
    if not gif:
        raise HTTPException(status_code=404)
    return gif

@app.post("/restore/user/{user_uid}")
async def restore_user(user_uid: str, db=Depends(get_db)):
    from app.couchbase_client import query_archives_by_owner, remove_archive
    docs = query_archives_by_owner(user_uid, limit=1000)
    restored = 0
    async with AsyncSessionLocal() as s:
        for r in docs:
            d = dict(r)
            cbid = d.get('cbid')
            data = d
            mid = data.get('id') or data.get('original_message_id')
            conv = data.get('conversation_id')
            sender = data.get('sender_uid')
            raw_hex = data.get('message_compressed_hex')
            raw_bytes = bytes.fromhex(raw_hex) if raw_hex else b''
            iv = data.get('iv') or ''
            mtype = data.get('message_type') or 'text'
            attachment = data.get('attachment')
            ts = data.get('created_at') or now_ts()
            msg = Message(id=mid, conversation_id=conv, sender_uid=sender, message_compressed=raw_bytes, iv=iv, message_type=mtype, attachment=attachment, size_bytes=0, created_at=ts)
            s.add(msg)
            restored += 1
            remove_archive(cbid)
        await s.commit()
    return {"restored": restored}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)