from sqlalchemy import Column, Integer, String, Boolean, BigInteger, Text, JSON, ForeignKey, Enum, ARRAY, LargeBinary
from app.database import Base
import enum
import uuid

def gen_uuid():
    return str(uuid.uuid4())

class UserType(enum.Enum):
    user = "user"
    moderator = "moderator"
    admin = "admin"
    oa = "oa"

class ConversationType(enum.Enum):
    pair = "pair"
    group = "group"
    group_plus = "group_plus"
    community = "community"

class Plan(Base):
    __tablename__ = "plans"
    plan_id = Column(Integer, primary_key=True)
    name = Column(String(32), unique=True, nullable=False)
    quotas_mb = Column(Integer, nullable=False)
    groups = Column(String, nullable=False)

class User(Base):
    __tablename__ = "users"
    uid = Column(String, primary_key=True, default=gen_uuid)
    firebase_uid = Column(String, unique=True, index=True)
    phone = Column(String, unique=True, index=True)
    email = Column(String, unique=True, nullable=True)
    email_verified = Column(Boolean, default=False)
    display_name = Column(String(128), default="")
    avatar_url = Column(String(512), nullable=True)
    user_type = Column(Enum(UserType), default=UserType.user)
    plan_id = Column(Integer, ForeignKey("plans.plan_id"), nullable=False)
    public_key = Column(Text, nullable=True)
    encrypted_private_key = Column(LargeBinary, nullable=True)
    last_used = Column(BigInteger, nullable=True)
    created_at = Column(BigInteger, nullable=False)
    updated_at = Column(BigInteger, nullable=False)

class YetiCode(Base):
    __tablename__ = "yeti_codes"
    code = Column(String, primary_key=True)
    used = Column(Boolean, default=False)
    created_at = Column(BigInteger, nullable=False)

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(String, primary_key=True, default=gen_uuid)
    type = Column(Enum(ConversationType), nullable=False)
    uids = Column(ARRAY(String))
    title = Column(String(255), nullable=True)
    leader_uid = Column(String, ForeignKey("users.uid"), nullable=True)
    deputy_uids = Column(ARRAY(String), nullable=True)
    last_message = Column(Text, nullable=True)
    last_used = Column(BigInteger, nullable=True)
    created_at = Column(BigInteger, nullable=False)

class Message(Base):
    __tablename__ = "messages"
    id = Column(String, primary_key=True, default=gen_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id"))
    sender_uid = Column(String, ForeignKey("users.uid"))
    message_compressed = Column(LargeBinary, nullable=False)
    iv = Column(String, nullable=True)
    message_type = Column(String, default="text")
    attachment = Column(JSON, nullable=True)
    size_bytes = Column(Integer, default=0)
    created_at = Column(BigInteger, nullable=False)

class Friend(Base):
    __tablename__ = "friends"
    id = Column(String, primary_key=True, default=gen_uuid)
    uid = Column(String, ForeignKey("users.uid"))
    friend_uid = Column(String, ForeignKey("users.uid"))
    status = Column(String, nullable=False)
    created_at = Column(BigInteger, nullable=False)

class Archive(Base):
    __tablename__ = "archives"
    id = Column(String, primary_key=True, default=gen_uuid)
    original_message_id = Column(String)
    owner_uid = Column(String)
    data = Column(JSON)
    created_at = Column(BigInteger, nullable=False)
    expires_at = Column(BigInteger, nullable=True)
    preserve = Column(Boolean, default=False)
