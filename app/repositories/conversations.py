from uuid import UUID

import asyncpg


async def get_conversation_for_user(
    conn: asyncpg.Connection,
    conversation_id: UUID,
    profile_id: UUID,
) -> asyncpg.Record | None:
    return await conn.fetchrow(
        """
        SELECT id, user_id, title, created_at, updated_at
        FROM conversations
        WHERE id = $1 AND user_id = $2
        """,
        conversation_id,
        profile_id,
    )


async def create_conversation(
    conn: asyncpg.Connection,
    profile_id: UUID,
    title: str | None,
) -> asyncpg.Record:
    return await conn.fetchrow(
        """
        INSERT INTO conversations (user_id, title)
        VALUES ($1, $2)
        RETURNING id, user_id, title, created_at, updated_at
        """,
        profile_id,
        title,
    )


async def list_conversations_for_user(
    conn: asyncpg.Connection,
    profile_id: UUID,
    *,
    limit: int = 50,
) -> list[asyncpg.Record]:
    return await conn.fetch(
        """
        SELECT id, user_id, title, created_at, updated_at
        FROM conversations
        WHERE user_id = $1
        ORDER BY updated_at DESC
        LIMIT $2
        """,
        profile_id,
        limit,
    )
