from pydantic import BaseModel
from typing import Optional, List, Any

class AuthIn(BaseModel):
    idToken: str
    yeti_code: Optional[str] = None

class UserOut(BaseModel):
    uid: str
    phone: str
    display_name: Optional[str] = None

class ConversationCreate(BaseModel):
    type: str
    participant_uids: List[str]
    title: Optional[str] = None

class MessageIn(BaseModel):
    conversation_id: str
    message_compressed_b64: str
    iv: Optional[str] = None
    message_type: Optional[str] = "text"
    size_bytes: Optional[int] = 0
    attachment: Optional[dict] = None

class RetractIn(BaseModel):
    conversation_id: str
    message_id: str

class ExportOut(BaseModel):
    data: Any
