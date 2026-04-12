import asyncpg

from app.settings import Settings, get_settings

_pool: asyncpg.Pool | None = None

async def create_pool(settings: Settings | None = None) -> asyncpg.Pool:
    global _pool
    if _pool is not None:
        return _pool
    s = settings or get_settings()
    _pool = await asyncpg.create_pool(dsn=s.database_url, min_size=1, max_size=10)
    return _pool

async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None

def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Database pool not initialized")
    return _pool

