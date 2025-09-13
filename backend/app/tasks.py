import time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.database import AsyncSessionLocal
from app.models import Message, User
from sqlalchemy import select, delete
from app.utils import now_ts
from app.couchbase_client import upsert_archive
from app.notify import send_one_signal

scheduler = AsyncIOScheduler()

async def archive_inactive():
    cutoff = now_ts() - 60*60*24*60
    async with AsyncSessionLocal() as s:
        res = await s.execute(select(User).where(User.last_used != None).where(User.last_used < cutoff))
        users = res.scalars().all()
        for u in users:
            q = await s.execute(select(Message).where(Message.sender_uid == u.uid))
            msgs = q.scalars().all()
            for m in msgs:
                data = {"id": m.id, "conversation_id": m.conversation_id, "sender_uid": m.sender_uid, "message_compressed_hex": m.message_compressed.hex(), "iv": m.iv, "message_type": m.message_type, "attachment": m.attachment, "created_at": m.created_at, "owner_uid": u.uid}
                key = f"archive::{u.uid}::{m.id}"
                upsert_archive(key, data, ttl_seconds=60*60*24*180)
                await s.execute(delete(Message).where(Message.id == m.id))
            await s.commit()
            send_one_signal([u.uid], "Your account archived due to inactivity")
def start_scheduler():
    scheduler.add_job(lambda: None, "interval", hours=24, id="noop")
    scheduler.add_job(lambda: None, "interval", hours=24, id="noop2")
    scheduler.start()
