from uuid import UUID

import asyncpg


async def get_profile_by_clerk_id(
    conn: asyncpg.Connection, clerk_user_id: str
) -> asyncpg.Record | None:
    return await conn.fetchrow(
        """
        SELECT id, clerk_user_id, display_name, created_at, updated_at
        FROM profiles WHERE clerk_user_id = $1
        """,
        clerk_user_id
    )

async def upsert_profile(
    conn: asyncpg.Connection, clerk_user_id: str, display_name: str | None
) -> asyncpg.Record:
    return await conn.fetchrow(
        """
        INSERT INTO profiles (clerk_user_id, display_name)
        VALUES ($1, $2)
        ON CONFLICT (clerk_user_id) DO UPDATE
        SET display_name = COALESCE(EXCLUDED.display_name, profiles.display_name),
        updated_at = now()
        RETURNING id, clerk_user_id, display_name, created_at, updated_at
        """,
        clerk_user_id,
        display_name
    )

async def update_display_name(
    conn: asyncpg.Connection, profile_id: UUID, display_name: str
) -> asyncpg.Record | None:
    return await conn.fetchrow(
        """
        UPDATE profiles SET display_name = $2,
        updated_at = now()
        RETURNING id, clerk_user_id, display_name, created_at, updated_at
        """,
        profile_id,
        display_name
    )

