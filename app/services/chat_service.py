from __future__ import annotations

import asyncio
from uuid import UUID

import asyncpg
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.genai import types

from app.repositories import conversations as conv_repo
from app.repositories import messages as msg_repo
from app.repositories import profiles as profiles_repo


class ConversationNotFoundError(Exception):
    pass

def _extract_assistant_text(events: list[object]) -> str:
    for event in reversed(events):
        content = getattr(event, "content", None)
        if not content:
            continue
        parts = getattr(content, "parts", None)
        if not parts:
            continue
        texts: list[str] = []
        for part in parts:
            t = getattr(part, "text", None)
            if t:
                texts.append(t)
        if texts:
            return "".join(texts)
    return ""

class ChatService:
    def __init__(self, runner: Runner) -> None:
        self._runner = runner

    def _run_agent_sync(
        self,
        *,
        profile_id: UUID,
        conversation_id: UUID,
        text: str,
    ) -> str:
        message = types.Content(
            role="user", parts=[types.Part.from_text(text=text)]
        )
        events = list(
            self._runner.run(
                new_message=message,
                user_id=str(profile_id),
                session_id=str(conversation_id),
                run_config=RunConfig(streaming_mode=StreamingMode.SSE),
            )
        )
        return _extract_assistant_text(events)

    async def send_user_message_and_run(
        self,
        conn: asyncpg.Connection,
        *,
        clerk_user_id: str,
        conversation_id: UUID,
        text: str,
    ) -> tuple[str, UUID]:
        profile = await profiles_repo.get_profile_by_clerk_id(conn, clerk_user_id)
        if profile is None:
            profile = await profiles_repo.upsert_profile(conn, clerk_user_id, None)
        profile_id: UUID = profile["id"]

        conv = await conv_repo.get_conversation_for_user(conn, conversation_id, profile_id)

        if conv is None:
                raise ConversationNotFoundError()

        await msg_repo.insert_message(
            conn, conversation_id, role="user", content=text
        )

        reply_text = await asyncio.to_thread(
            self._run_agent_sync,
            profile_id=profile_id,
            conversation_id=conversation_id,
            text=text,
        )

        assistant_row = await msg_repo.insert_message(
            conn, conversation_id, role="assistant", content=reply_text
        )

        assistant_id: UUID = assistant_row["id"]
        return reply_text, assistant_id
