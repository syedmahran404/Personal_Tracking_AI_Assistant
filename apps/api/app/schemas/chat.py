from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.chat import ChatRole


class ChatSendRequest(BaseModel):
    session_id: uuid.UUID | None = None
    message: str = Field(min_length=1, max_length=4000)


class ChatMessagePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: ChatRole
    content: str
    created_at: datetime


class ChatSessionPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime


class ChatSessionDetail(ChatSessionPublic):
    messages: list[ChatMessagePublic] = []


class ChatSendResponse(BaseModel):
    session: ChatSessionPublic
    message: ChatMessagePublic
