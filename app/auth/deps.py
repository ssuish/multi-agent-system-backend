from collections.abc import AsyncIterator
from typing import Annotated

import asyncpg
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.clerk_jwt import verify_clerk_jwt
from app.db.pool import get_pool
from app.settings import get_settings

_bearer = HTTPBearer(auto_error=False)


async def get_db_conn() -> AsyncIterator[asyncpg.Connection]:
    pool = get_pool()
    async with pool.acquire() as conn:
        yield conn


async def get_current_clerk_user_id(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> str:
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )

    settings = get_settings()

    try:
        return verify_clerk_jwt(
            creds.credentials,
            clerk_jwks_url=settings.clerk_jwks_url,
            clerk_issuer=settings.clerk_issuer,
            clerk_audience=settings.clerk_audience,
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from None
