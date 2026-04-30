from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    user = "user"
    assistant = "assistant"


class ConversationStatus(str, Enum):
    active = "active"


class ConversationCreateIn(BaseModel):
    title: str | None = None
    status: str
    jd_text: str = Field(min_length=1, max_length=16000)
    cv_reference: str = Field(min_length=1, max_length=255)
    cv_markdown: str | None = None


class ConversationOut(BaseModel):
    id: UUID
    title: str | None
    status: ConversationStatus
    jd_text: str
    cv_reference: str
    cv_markdown: str | None
    created_at: datetime
    updated_at: datetime


class ChatMessageIn(BaseModel):
    text: str = Field(min_length=1, max_length=500)


class ChatMessageOut(BaseModel):
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    created_at: datetime
