from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.services.chat_service import ChatService


@pytest.mark.asyncio
async def test_send_user_message_and_run_returns_assistant_message() -> None:
    profile_id = uuid4()
    conv_id = uuid4()
    assistant_msg_id = uuid4()

    mock_runner = MagicMock()

    fake_event = MagicMock()
    fake_event.content.parts = [MagicMock(text="hello from model")]

    mock_runner.run.return_value = iter([fake_event])

    svc = ChatService(runner=mock_runner)

    class FakeConn:
        async def fetchrow(self, query: str, *params: object):
            if "FROM profiles" in query and "clerk_user_id" in query:
                return {
                    "id": profile_id,
                    "clerk_user_id": "u1",
                    "display_name": None,
                }
            if "FROM conversations" in query and "WHERE id" in query:
                return {"id": conv_id, "user_id": profile_id}
            if "INSERT INTO messages" in query and "RETURNING" in query:
                role = params[1] if len(params) > 1 else ""
                if role == "assistant":
                    return {
                        "id": assistant_msg_id,
                        "conversation_id": conv_id,
                        "role": "assistant",
                        "content": "hello from model",
                    }
                return {
                    "id": uuid4(),
                    "conversation_id": conv_id,
                    "role": "user",
                    "content": "hi",
                }
            return None

        async def fetch(self, *args: object, **kwargs: object):
            return []

    conn = FakeConn()
    reply, mid = await svc.send_user_message_and_run(
        conn,
        clerk_user_id="u1",
        conversation_id=conv_id,
        text="hi",
    )
    assert reply == "hello from model"
    assert mid == assistant_msg_id
