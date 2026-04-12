from uuid import UUID

import asyncpg

async def insert_message(
    conn: asyncpg.Connection,
    conversation_id: UUID,
    role: str,
    content: str,
) -> asyncpg.Record:
    return await conn.fetchrow(
        """
        INSERT INTO messages (conversation_id, role, content)
        VALUES ($1, $2, $3)
        RETURNING id, conversation_id, role, content, created_at
        """,
        conversation_id,
        role,
        content,
    )

async def list_messages_for_conversation(
    conn: asyncpg.Connection,
    conversation_id: UUID,
    *,
    limit: int = 200,
) -> list[asyncpg.Record]:
    return await conn.fetch(
        """
        SELECT id, conversation_id, role, content, created_at
        FROM messages
        WHERE conversation_id = $1
        ORDER BY created_at ASC
        LIMIT $2
        """,
        conversation_id,
        limit,
    )