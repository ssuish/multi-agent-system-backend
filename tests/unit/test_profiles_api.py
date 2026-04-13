from datetime import UTC, datetime
from uuid import UUID

from fastapi.testclient import TestClient

from app.auth import deps as deps_mod
from app.fast_api_app import app


def test_get_me_override_db() -> None:
    fixed_id = UUID("00000000-0000-4000-8000-000000000001")
    now = datetime.now(tz=UTC)

    class FakeConn:
        async def fetchrow(self, query: str, *args: object):
            if (
                "FROM profiles" in query
                and "WHERE" in query
                and "clerk_user_id" in query
            ):
                return None
            return {
                "id": fixed_id,
                "clerk_user_id": args[0],
                "display_name": None,
                "created_at": now,
                "updated_at": now,
            }

    async def fake_conn_dep():
        yield FakeConn()

    app.dependency_overrides[deps_mod.get_current_clerk_user_id] = lambda: "user_x"
    app.dependency_overrides[deps_mod.get_db_conn] = fake_conn_dep

    client = TestClient(app)
    r = client.get("/api/v1/me")
    app.dependency_overrides.clear()
    assert r.status_code == 200
    assert r.json()["clerk_user_id"] == "user_x"
