from datetime import datetime
from typing import Annotated
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.auth.deps import get_current_clerk_user_id, get_db_conn
from app.services.conversation_service import (
    ConversationNotFoundError,
    ConversationService,
)

router = APIRouter(tags=["conversation"])
_svc = ConversationService()


class ConversationCreateIn(BaseModel):
    title: str | None = None


class ConversationOut(BaseModel):
    id: UUID
    title: str | None
    created_at: datetime
    updated_at: datetime


class MessageOut(BaseModel):
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    created_at: datetime


@router.post(
    "/conversations",
    response_model=ConversationOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    body: ConversationCreateIn,
    clerk_user_id: Annotated[str, Depends(get_current_clerk_user_id)],
    conn: Annotated[asyncpg.Connection, Depends(get_db_conn)],
) -> ConversationOut:
    row = await _svc.create_conversation(
        conn, clerk_user_id=clerk_user_id, title=body.title
    )
    return ConversationOut.model_validate(dict(row))


@router.get("/conversations", response_model=list[ConversationOut])
async def list_conversations(
    clerk_user_id: Annotated[str, Depends(get_current_clerk_user_id)],
    conn: Annotated[asyncpg.Connection, Depends(get_db_conn)],
    limit: int = Query(default=50, ge=1, le=200),
) -> list[ConversationOut]:
    rows = await _svc.list_conversations(conn, clerk_user_id=clerk_user_id, limit=limit)
    return [ConversationOut.model_validate(dict(row)) for row in rows]


@router.get("/conversations/{conversation_id}", response_model=ConversationOut)
async def get_conversation(
    conversation_id: UUID,
    clerk_user_id: Annotated[str, Depends(get_current_clerk_user_id)],
    conn: Annotated[asyncpg.Connection, Depends(get_db_conn)],
) -> ConversationOut:
    try:
        row = await _svc.get_conversation(
            conn, clerk_user_id=clerk_user_id, conversation_id=conversation_id
        )
    except ConversationNotFoundError:
        raise HTTPException(status_code=404, detail="Conversation not found") from None
    return ConversationOut.model_validate(dict(row))


@router.delete(
    "/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_conversation(
    conversation_id: UUID,
    clerk_user_id: Annotated[str, Depends(get_current_clerk_user_id)],
    conn: Annotated[asyncpg.Connection, Depends(get_db_conn)],
) -> None:
    try:
        await _svc.delete_conversation(
            conn, clerk_user_id=clerk_user_id, conversation_id=conversation_id
        )
    except ConversationNotFoundError:
        raise HTTPException(status_code=404, detail="Conversation not found") from None


@router.get(
    "/conversations/{conversation_id}/messages", response_model=list[MessageOut]
)
async def list_messages(
    conversation_id: UUID,
    clerk_user_id: Annotated[str, Depends(get_current_clerk_user_id)],
    conn: Annotated[asyncpg.Connection, Depends(get_db_conn)],
    limit: int = Query(default=200, ge=1, le=500),
) -> list[MessageOut]:
    try:
        rows = await _svc.list_messages(
            conn,
            clerk_user_id=clerk_user_id,
            conversation_id=conversation_id,
            limit=limit,
        )
    except ConversationNotFoundError:
        raise HTTPException(status_code=404, detail="Conversation not found") from None
    return [MessageOut.model_validate(dict(row)) for row in rows]
