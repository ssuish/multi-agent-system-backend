from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.auth import deps as deps_mod
from app.fast_api_app import app


def test_create_conversation_returns_core_fields() -> None:
    now = datetime.now()
    conv_id = uuid4()
    profile_id = uuid4()

    class FakeConn:
        async def fetchrow(self, query: str, *args: object):
            if "FROM profiles" in query and "clerk_user_id" in query:
                return {"id": profile_id, "clerk_user_id": "user_a"}
            if "INSERT INTO conversations" in query:
                return {
                    "id": conv_id,
                    "user_id": profile_id,
                    "title": "First",
                    "created_at": now,
                    "updated_at": now,
                }
            return None

        async def fetch(self, query: str, *args: object):
            return []

    async def fake_conn_dep():
        yield FakeConn()

    app.dependency_overrides[deps_mod.get_current_clerk_user_id] = lambda: "user_a"
    app.dependency_overrides[deps_mod.get_db_conn] = fake_conn_dep
    client = TestClient(app)
    res = client.post("/api/v1/conversations", json={"title": "First"})
    app.dependency_overrides.clear()

    assert res.status_code == 201
    assert set(res.json().keys()) == {"id", "title", "created_at", "updated_at"}


def test_get_conversation_returns_404_when_not_owned() -> None:
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
    client = TestClient(app)
    missing_id = UUID("00000000-0000-4000-8000-000000000042")
    res = client.get(f"/api/v1/conversations/{missing_id}")
    app.dependency_overrides.clear()

    assert res.status_code == 404


def test_delete_conversation_returns_204() -> None:
    profile_id = uuid4()
    conversation_id = uuid4()

    class FakeConn:
        async def fetchrow(self, query: str, *args: object):
            if "FROM profiles" in query:
                return {"id": profile_id, "clerk_user_id": "user_a"}
            if "FROM conversations" in query and "WHERE id" in query:
                return {"id": conversation_id, "user_id": profile_id}
            if "DELETE FROM conversations" in query:
                return {"id": conversation_id}
            return None

        async def fetch(self, query: str, *args: object):
            return []

    async def fake_conn_dep():
        yield FakeConn()

    app.dependency_overrides[deps_mod.get_current_clerk_user_id] = lambda: "user_a"
    app.dependency_overrides[deps_mod.get_db_conn] = fake_conn_dep
    client = TestClient(app)
    res = client.delete(f"/api/v1/conversations/{conversation_id}")
    app.dependency_overrides.clear()
    assert res.status_code == 204


def test_list_messages_returns_ordered_history_for_owner() -> None:
    now = datetime.now(tz=UTC)
    profile_id = uuid4()
    conversation_id = uuid4()

    class FakeConn:
        async def fetchrow(self, query: str, *args: object):
            if "FROM profiles" in query:
                return {"id": profile_id, "clerk_user_id": "user_a"}
            if "FROM conversations" in query:
                return {"id": conversation_id, "user_id": profile_id}
            return None

        async def fetch(self, query: str, *args: object):
            if "FROM messages" in query:
                return [
                    {
                        "id": uuid4(),
                        "conversation_id": conversation_id,
                        "role": "user",
                        "content": "hello",
                        "created_at": now,
                    },
                    {
                        "id": uuid4(),
                        "conversation_id": conversation_id,
                        "role": "assistant",
                        "content": "hi",
                        "created_at": now,
                    },
                ]
            return []

    async def fake_conn_dep():
        yield FakeConn()

    app.dependency_overrides[deps_mod.get_current_clerk_user_id] = lambda: "user_a"
    app.dependency_overrides[deps_mod.get_db_conn] = fake_conn_dep
    client = TestClient(app)
    res = client.get(f"/api/v1/conversations/{conversation_id}/messages")
    app.dependency_overrides.clear()

    assert res.status_code == 200
    assert [m["role"] for m in res.json()] == ["user", "assistant"]
