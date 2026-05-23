"""AI chat assistant — sessions + send-message turn."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import desc, select

from app.ai.agent import chat_complete
from app.api.deps import CurrentUser, DbSession
from app.models.chat import ChatMessage, ChatRole, ChatSession
from app.schemas.chat import (
    ChatMessagePublic,
    ChatSendRequest,
    ChatSendResponse,
    ChatSessionDetail,
    ChatSessionPublic,
)
from app.services.realtime import notify

router = APIRouter()


@router.get("/sessions", response_model=list[ChatSessionPublic])
async def list_sessions(user: CurrentUser, db: DbSession) -> list[ChatSessionPublic]:
    rows = (
        await db.scalars(
            select(ChatSession)
            .where(ChatSession.user_id == user.id)
            .order_by(desc(ChatSession.updated_at))
            .limit(50)
        )
    ).all()
    return [ChatSessionPublic.model_validate(r) for r in rows]


@router.get("/sessions/{session_id}", response_model=ChatSessionDetail)
async def get_session(
    session_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> ChatSessionDetail:
    sess = await db.get(ChatSession, session_id)
    if not sess or sess.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")

    messages = (
        await db.scalars(
            select(ChatMessage)
            .where(ChatMessage.session_id == sess.id)
            .order_by(ChatMessage.created_at.asc())
        )
    ).all()
    return ChatSessionDetail(
        **ChatSessionPublic.model_validate(sess).model_dump(),
        messages=[ChatMessagePublic.model_validate(m) for m in messages],
    )


@router.post("/send", response_model=ChatSendResponse)
async def send_message(
    payload: ChatSendRequest,
    user: CurrentUser,
    db: DbSession,
) -> ChatSendResponse:
    # Resolve / create session
    if payload.session_id is not None:
        sess = await db.get(ChatSession, payload.session_id)
        if not sess or sess.user_id != user.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    else:
        title = payload.message[:60] + ("…" if len(payload.message) > 60 else "")
        sess = ChatSession(user_id=user.id, title=title)
        db.add(sess)
        await db.flush()

    # Persist user message
    user_msg = ChatMessage(session_id=sess.id, role=ChatRole.USER, content=payload.message)
    db.add(user_msg)
    await db.flush()

    # Build LLM history
    prior = (
        await db.scalars(
            select(ChatMessage)
            .where(ChatMessage.session_id == sess.id)
            .order_by(ChatMessage.created_at.asc())
        )
    ).all()
    history = [
        {"role": m.role.value if m.role.value != "tool" else "assistant", "content": m.content}
        for m in prior
        if m.id != user_msg.id
    ]

    # Run LLM
    answer = await chat_complete(db, user.id, history, payload.message)

    asst = ChatMessage(session_id=sess.id, role=ChatRole.ASSISTANT, content=answer)
    db.add(asst)
    await db.commit()
    await db.refresh(asst)
    await db.refresh(sess)

    notify(user.id, "chat.message", {"session_id": str(sess.id)})

    return ChatSendResponse(
        session=ChatSessionPublic.model_validate(sess),
        message=ChatMessagePublic.model_validate(asst),
    )


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(
    session_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> None:
    sess = await db.get(ChatSession, session_id)
    if not sess or sess.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    await db.delete(sess)
    await db.commit()
