from datetime import datetime
from typing import Annotated
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.deps import get_current_clerk_user_id, get_db_conn
from app.repositories import profiles as profiles_repo

router = APIRouter(tags=["profiles"])


class ProfileOut(BaseModel):
    id: UUID
    clerk_user_id: str
    display_name: str | None
    created_at: datetime
    updated_at: datetime


class ProfileUpdate(BaseModel):
    display_name: str | None = None


@router.get("/me", response_model=ProfileOut)
async def get_me(
    clerk_user_id: Annotated[str, Depends(get_current_clerk_user_id)],
    conn: Annotated[asyncpg.Connection, Depends(get_db_conn)],
) -> ProfileOut:
    row = await profiles_repo.get_profile_by_clerk_id(conn, clerk_user_id)

    if row is None:
        row = await profiles_repo.upsert_profile(conn, clerk_user_id, None)
        return ProfileOut.model_validate(dict(row))


@router.put("/me", response_model=ProfileOut)
async def put_me(
    body: ProfileUpdate,
    clerk_user_id: Annotated[str, Depends(get_current_clerk_user_id)],
    conn: Annotated[asyncpg.Connection, Depends(get_db_conn)],
) -> ProfileOut:
    row = await profiles_repo.upsert_profile(conn, clerk_user_id, body.display_name)
    return ProfileOut.model_validate(dict(row))
