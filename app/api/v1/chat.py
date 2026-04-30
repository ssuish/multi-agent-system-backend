from typing import Annotated
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status

from app.agent_runtime import runner
from app.api.v1.schemas.conversations import ChatMessageIn, ChatMessageOut
from app.auth.deps import get_current_clerk_user_id, get_db_conn
from app.services.chat_service import ChatService, ConversationNotFoundError

router = APIRouter(tags=["chat"])
_chat_service = ChatService(runner=runner)


@router.post("/conversations/{conversation_id}/messages", response_model=ChatMessageOut)
async def post_message(
    conversation_id: UUID,
    body: ChatMessageIn,
    clerk_user_id: Annotated[str, Depends(get_current_clerk_user_id)],
    conn: Annotated[asyncpg.Connection, Depends(get_db_conn)],
) -> ChatMessageOut:
    try:
        reply, mid = await _chat_service.send_user_message_and_run(
            conn,
            clerk_user_id=clerk_user_id,
            conversation_id=conversation_id,
            text=body.text,
        )
    except ConversationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        ) from None
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Agent failed to respond",
        ) from None
    return ChatMessageOut(reply=reply, assistant_message_id=mid)
