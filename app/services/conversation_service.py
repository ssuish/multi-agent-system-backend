from uuid import UUID

import asyncpg

from app.repositories import conversations as conv_repo
from app.repositories import messages as msg_repo
from app.repositories import profiles as profiles_repo


class ConversationNotFoundError(Exception):
    pass


class ConversationPayloadInvariantError(Exception):
    pass


class ConversationService:
    async def _get_or_create_profile_id(
        self, conn: asyncpg.Connection, clerk_user_id: str
    ) -> UUID:
        profile = await profiles_repo.get_profile_by_clerk_id(conn, clerk_user_id)
        if profile is None:
            profile = await profiles_repo.upsert_profile(conn, clerk_user_id, None)
        return profile["id"]

    async def create_conversation(
        self,
        conn: asyncpg.Connection,
        *,
        clerk_user_id: str,
        title: str | None,
        status: str,
        jd_text: str,
        cv_reference: str,
        cv_markdown: str | None,
    ) -> asyncpg.Record:
        profile_id = await self._get_or_create_profile_id(conn, clerk_user_id)

        if not jd_text.strip():
            raise ConversationPayloadInvariantError("jd_text is required")

        if not cv_reference.strip():
            raise ConversationPayloadInvariantError("cv_reference is required")

        return await conv_repo.create_conversation(
            conn,
            profile_id=profile_id,
            title=title,
            status=status,
            jd_text=jd_text,
            cv_reference=cv_reference,
            cv_markdown=cv_markdown,
        )

    async def list_conversations(
        self, conn: asyncpg.Connection, *, clerk_user_id: str, limit: int = 50
    ) -> list[asyncpg.Record]:
        profile_id = await self._get_or_create_profile_id(conn, clerk_user_id)
        return await conv_repo.list_conversations_for_user(
            conn, profile_id, limit=limit
        )

    async def get_conversation(
        self, conn: asyncpg.Connection, *, clerk_user_id: str, conversation_id: UUID
    ) -> asyncpg.Record:
        profile_id = await self._get_or_create_profile_id(conn, clerk_user_id)
        row = await conv_repo.get_conversation_for_user(
            conn, conversation_id, profile_id
        )
        if row is None:
            raise ConversationNotFoundError()
        return row

    async def delete_conversation(
        self, conn: asyncpg.Connection, *, clerk_user_id: str, conversation_id: UUID
    ) -> None:
        profile_id = await self._get_or_create_profile_id(conn, clerk_user_id)
        deleted = await conv_repo.delete_conversation_for_user(
            conn, conversation_id=conversation_id, profile_id=profile_id
        )

        if not deleted:
            raise ConversationNotFoundError()

    async def list_messages(
        self,
        conn: asyncpg.Connection,
        *,
        clerk_user_id: str,
        conversation_id: UUID,
        limit: int = 200,
    ) -> list[asyncpg.Record]:
        profile_id = await self._get_or_create_profile_id(conn, clerk_user_id)
        conv = await conv_repo.get_conversation_for_user(
            conn, conversation_id, profile_id
        )
        if conv is None:
            raise ConversationNotFoundError()
        return await msg_repo.list_messages_for_conversation(
            conn, conversation_id, limit=limit
        )
