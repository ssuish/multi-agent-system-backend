# Modules

## Layout (high level)

| Path | Role |
|------|------|
| [`app/fast_api_app.py`](../app/fast_api_app.py) | FastAPI app, CORS, lifespan (DB pool + A2A routes), `/feedback`, includes `api_v1_router` |
| [`app/agent.py`](../app/agent.py) | ADK `App`, travel-concierge `root_agent` (`TravelCoordinator`) delegating to a sequential `FullPipeline` of `ResearchAgent → PlacesFormatter → InterestCheckAgent → SelectionFormatter → CalendarAgent → RoutingAgent` |
| [`app/agent_runtime.py`](../app/agent_runtime.py) | Shared ADK `Runner`, session service, artifact service |
| [`app/settings.py`](../app/settings.py) | `pydantic-settings`: `database_url`, Clerk URLs/issuer/audience, CORS, MCP flags |
| [`app/db/pool.py`](../app/db/pool.py) | Global asyncpg pool: `create_pool`, `close_pool`, `get_pool` |
| [`app/auth/clerk_jwt.py`](../app/auth/clerk_jwt.py) | JWT verification against Clerk JWKS |
| [`app/auth/deps.py`](../app/auth/deps.py) | `HTTPBearer` → `get_current_clerk_user_id`, `get_db_conn` |
| [`app/api/v1/router.py`](../app/api/v1/router.py) | `/api/v1` router; includes `profiles` and `chat` |
| [`app/api/v1/profiles.py`](../app/api/v1/profiles.py) | `GET`/`PUT` `/me` profile CRUD |
| [`app/api/v1/chat.py`](../app/api/v1/chat.py) | `POST` `/conversations/{conversation_id}/messages` via `ChatService` |
| [`app/services/chat_service.py`](../app/services/chat_service.py) | Persists messages, runs `Runner` for assistant reply |
| [`app/repositories/profiles.py`](../app/repositories/profiles.py) | Profile rows |
| [`app/repositories/conversations.py`](../app/repositories/conversations.py) | Conversation ownership / lookup |
| [`app/repositories/messages.py`](../app/repositories/messages.py) | Message insert/list |
| [`app/mcp/mcp_client.py`](../app/mcp/mcp_client.py) | Stdio MCP client primitives (`configure_stdio_server`, `call_tool`); currently not wired into the active `root_agent` tools |
| [`app/mcp/__init__.py`](../app/mcp/__init__.py) | Re-exports for MCP client helpers |
| [`app/app_utils/telemetry.py`](../app/app_utils/telemetry.py) | OpenTelemetry / observability setup |
| [`app/app_utils/typing.py`](../app/app_utils/typing.py) | Shared Pydantic types (e.g. `Feedback`) |
| [`app/app_utils/eval_context.py`](../app/app_utils/eval_context.py) | Evaluation helpers (ADK eval flows) |

## A2A URL shape

The ADK `App` name is `app` ([`app/agent.py`](../app/agent.py)), so A2A routes are under `/a2a/app/` (see [`Makefile`](../Makefile) inspector hints for the well-known agent card URL).

## Notes

- Re-run this analysis after large additions under `app/` (e.g. new routers or packages).
