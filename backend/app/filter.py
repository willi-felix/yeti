from app.database import AsyncSessionLocal
from sqlalchemy import text
async def load_bad_words():
    async with AsyncSessionLocal() as s:
        q = await s.execute(text("SELECT word FROM bad_words"))
        rows = q.fetchall()
        return [r[0] for r in rows]
async def is_inappropriate(content: str):
    words = await load_bad_words()
    lower = content.lower()
    for w in words:
        if w and w in lower:
            return True
    return False
