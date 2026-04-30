# Tech debt

**Last reviewed:** 2026-04-30

Tracked gaps around conversations, chat, persistence, and PRD guardrails. Align with [prd.md](prd.md) for intended MVP behavior.

## Conversations / messages / API contracts

1. **DB nullability drift** — `jd_text`, `cv_reference`, and message `role` / `content` are nullable in Postgres while the API assumes required values; no NOT NULL / CHECK alignment (`app/db/migrations/migration.sql`).
2. **Unconstrained status and role in DB** — `conversations.status` and `messages.role` are plain `text`; no CHECK or enum mirroring `ConversationStatus` and `MessageRole` in `app/api/v1/schemas/conversations.py`.
3. **Message listing semantics** — `list_messages_for_conversation` uses `ORDER BY created_at ASC` with a fixed `LIMIT`, so long threads return the **oldest** window, not the latest tail (`app/repositories/messages.py`). Cursor or reverse pagination would match typical chat UX.

## Chat runtime and observability

4. **Partial persistence on agent failure** — `ChatService.send_user_message_and_run` inserts the user row before the agent runs; failure yields **502** with a persisted user message and no assistant row (`app/services/chat_service.py`). `get_db_conn` does not wrap requests in an explicit `transaction()`, so there is no atomic multi-statement boundary for chat writes (`app/auth/deps.py`).
5. **Opaque chat errors** — `POST …/messages` maps non-404 exceptions to a generic **502** without structured logging, tracing, or error classification (`app/api/v1/chat.py`).
6. **`ChatMessageOut.role` typing** — response model uses plain `str` while `MessageRole` exists; weaker OpenAPI/client contract (`app/api/v1/schemas/conversations.py`).
7. **No deadline on agent execution** — the ADK `Runner.run` path runs inside `asyncio.to_thread` with no timeout or cancellation; slow or stuck LLM calls consume threadpool capacity indefinitely (`app/services/chat_service.py`).
8. **Chat response omits user message id** — `ChatReplyOut` returns only `reply` and `assistant_message_id`; callers cannot attach correlation to the persisted user row without `GET …/messages` (`app/api/v1/schemas/conversations.py`, `app/api/v1/chat.py`).

## Product / PRD / platform

9. **Stale PRD “As-Is”** — `docs/prd.md` still describes older API gaps in places (e.g. conversation lifecycle vs current `/api/v1`); reconcile As-Is with the codebase.
10. **Missing PRD guardrails on chat path** — no Redis per-user LLM budgets (**429**) or bounded timeouts around LLM/agent execution (`docs/prd.md` P0).
11. **Delete vs append-only narrative** — `DELETE /conversations` cascades and removes message history, which can conflict with “append-only history” unless deleting an entire thread is an explicit product escape hatch (`app/db/migrations/migration.sql` FK `ON DELETE CASCADE`).
12. **ADK / A2A debt** — in-memory ADK sessions (non-durable across restarts) and unauthenticated **A2A** surface remain separate durability and security gaps outside the Clerk-protected `/api/v1` contract (`app/agent_runtime.py`, `app/fast_api_app.py`).
