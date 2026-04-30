from uuid import uuid4
from fastapi.testclient import TestClient
from app.fast_api_app import app
from app.auth import deps as deps_mod


def test_post_message_rejects_over_500_chars() -> None:
    client = TestClient(app)
    profile_id = uuid4()

    class FakeConn:
        async def fetchrow(self, query: str, *args: object):
            if "FROM profiles" in query and "clerk_user_id" in query:
                return {"id": profile_id, "clerk_user_id": "user_a"}
            if "FROM conversations" in query and "WHERE id" in query:
                return None
            return None

        async def fetch(self, query: str, *args: object):
            return []

    async def fake_conn_dep():
        yield FakeConn()

    app.dependency_overrides[deps_mod.get_current_clerk_user_id] = lambda: "user_a"
    app.dependency_overrides[deps_mod.get_db_conn] = fake_conn_dep
    res = client.post(
        "/api/v1/conversations/{conversation_id}/messages", json={"text": "x" * 501}
    )
    assert res.status_code == 422
