# MVP product requirements (PRD)

This document defines the **To-Be** MVP, summarizes **As-Is** behavior from the current codebase, and lists the **backlog** required to close the gap.

---

## To-Be MVP requirements

### Product constraints

- **Auth / identity:** Clerk is the system of record. The backend verifies a Clerk JWT on every protected request.
- **LLM route protection:** Every HTTP route that invokes an LLM requires auth. Unauthenticated requests are rejected.
- **Tenancy model:** Many users in one app; no org/workspace admin in MVP.
- **Agent execution:** Synchronous.
- **Session model:** One conversation is bound to exactly one selected CV and one JD for its lifetime. A new JD requires a new conversation.
- **Conversation model:** Keep chat history for each conversation as read-only/append-only. Past messages cannot be edited or deleted in-app.
- **CV ingestion:** Frontend uploads one PDF CV per conversation. Backend parses via Marker (PDF to Markdown) and stores parsed markdown in the database.
- **Input limits:** CV upload max size is 5 MB. Refinement chat input is limited to 500 characters per user message. JD input has a separate, larger cap (for example 16,000 chars; finalized in API contract).
- **Per-user usage limits:** Enforce Redis-based per-user LLM call limits (default target: 200 calls per rolling 24 hours, configurable). Exceeded limits return 429.
- **Timeouts:** LLM and parsing calls use bounded timeouts. No explicit max-token cap is required in this MVP.
- **Gap analysis contract:** Gap analysis output is strict JSON with a fixed schema shape (for example `gap_analysis_v1`) including requirement, match status, resume evidence bullet, suggested change, and confidence.
- **Gap analysis failure behavior:** If model output fails schema validation, return a clear failure response; no automatic repair pass and no partial `errors[]` contract in MVP.
- **Resume assembly:** Refined resume is assembled server-side in strict order: Skills, Experience, Projects, Education, Others.
- **Export semantics:** Export endpoint is idempotent and reads latest persisted refined output only (no on-demand LLM re-generation).
- **Output persistence:** Refined output is stored as Markdown and rendered HTML for preview and print.
- **PDF approach:** MVP PDF is frontend/browser-based (HTML + CSS in new tab, then print/save PDF), plus copy-as-text action.
- **Cover letter scope:** Optional feature (P1): generate cover letter using JD + resume context + lightweight company/role research.
- **Out of scope in this MVP:** Google Calendar and Google Maps integration.
- **Deferred from full PRD scope:** Conversation auto-retention/eviction policy, multi-CV library + primary CV rules, post-analysis CV lock, malformed-output repair pipeline, export length warning.

### User stories (MVP)

#### Authentication & profile

| Story | Acceptance |
|--------|--------------|
| **Login / logout** | As a user, I want to log in and log out of the system. Backend accepts and verifies Clerk bearer JWT; logout is handled client-side. |
| **Update user info** | As a user, I want to update my profile fields needed by the MVP experience. |
| **Protected LLM routes** | As a user, I want my LLM-triggering actions protected so only authenticated users can run analysis/refinement endpoints. |

#### Session setup (single CV + JD)

| Story | Acceptance |
|--------|--------------|
| **Start JD-specific conversation** | As a user, I want each conversation tied to exactly one JD and one CV, and I must start a new conversation for a different JD. |
| **Upload single CV (5 MB max)** | As a user, I want to upload one PDF CV to a conversation, and uploads above 5 MB are rejected with a clear error. |
| **Parse CV** | As a user, I want the uploaded PDF parsed into markdown and stored so analysis can run on structured text. |
| **Provide JD text** | As a user, I want to provide JD text for the conversation, with a documented cap separate from chat message limits. |

#### Gap analysis & refinement

| Story | Acceptance |
|--------|--------------|
| **Run strict gap analysis** | As a user, I want a structured gap analysis between selected CV and JD. Output follows fixed schema and includes requirement, match status, resume evidence bullet, suggested change, and confidence. |
| **Schema failure returns clear error** | As a user, I want a clear failure response when model output is invalid, instead of silently returning malformed data. |
| **Refine through chat** | As a user, I want to iteratively refine the resume through conversation until acceptable, without in-app rich-text editing. |
| **500-char chat cap** | As a user, I want each refinement message validated so overlong messages are rejected predictably. |
| **Read-only history** | As a user, I want message history preserved as append-only records so I can track what changed over time. |
| **Template-ordered final draft** | As a user, I want the final refined resume assembled in strict section order: Skills, Experience, Projects, Education, Others. |

#### Preview & export

| Story | Acceptance |
|--------|--------------|
| **Preview refined output** | As a user, I want preview-ready rendered output for the latest refined resume. |
| **Export idempotently** | As a user, I want export to return the latest persisted refined output consistently without extra model processing. |
| **Copy and print** | As a user, I want copy-as-text and browser print/save-as-PDF options from rendered HTML. |

#### Optional cover letter (P1)

| Story | Acceptance |
|--------|--------------|
| **Generate cover letter** | As a user, I want optional cover-letter generation using JD, resume details, and lightweight company/role research. |
| **Cover letter export actions** | As a user, I want separate copy-as-text and browser print/save-as-PDF actions for cover letters. |

---

## As-Is MVP (codebase analysis + backlog)

Summary of what the backend currently supports versus what is missing for the resume-refiner MVP, based on repository implementation and ADK documentation constraints.

### What exists today (implemented or partially implemented)

#### 1) Backend framework and deployment skeleton

FastAPI app currently includes:

- CORS and lifespan startup/shutdown (`app/fast_api_app.py`)
- Async Postgres pool create/close on lifespan (`create_pool` / `close_pool`)
- `/api/v1` router (`app/api/v1/router.py`)
- A2A server under `/a2a/app` (dynamic agent card + RPC routes) (`app/fast_api_app.py`)
- ADK runner wiring (`app/agent_runtime.py`)
- Telemetry setup (`setup_telemetry()` on import)

Current gap:

- `/a2a/app` is mounted without Clerk auth checks today, A2A is explicitly treated as non-product/dev-only surface.

**As-Is requirement:** Backend runs with FastAPI, connects to Postgres, and exposes API v1 plus A2A RPC.

#### 2) Clerk JWT authentication (backend verification)

Protected API endpoints use dependencies that:

- Read Bearer token
- Verify JWT via Clerk JWKS / issuer / optional audience (`app/auth/deps.py`)
- Return `clerk_user_id`

**As-Is requirement:** Backend authenticates protected API requests with Clerk JWT and derives current user id.

#### 3) Minimal profile

- `GET` / `PUT` `/api/v1/me` exists (`app/api/v1/profiles.py`)
- Profile is upserted on first access (`app/repositories/profiles.py`)
- Current profile fields are minimal (`display_name` only plus ids/timestamps)

**As-Is requirement:** User profile read/update exists but does not include resume-product preferences.

#### 4) Conversations and messages (repo support vs HTTP surface)

Repository layer exists:

- Conversations repository supports fetch/create/list (`app/repositories/conversations.py`)
- Messages repository supports insert/list (`app/repositories/messages.py`)

HTTP layer currently exposes:

- `POST /api/v1/conversations/{conversation_id}/messages` only (`app/api/v1/chat.py`)
- API router currently mounts only `chat` and `profiles` routers (`app/api/v1/router.py`)

Current gaps:

- No HTTP create/list/get/delete conversation lifecycle endpoints in API v1.
- No CV/JD fields bound to conversation.
- No resume-domain entities for parsed CV, gap-analysis snapshots, refined outputs, or export artifacts.

**As-Is requirement:** Given an existing conversation, a user can send messages and receive synchronous assistant replies with persisted user/assistant message rows.

#### 5) ADK runtime and current agent domain

- Runner uses `InMemorySessionService` (`app/agent_runtime.py`), so session context is in-memory and not durable across restarts.
- Artifact service is `GcsArtifactService` when `LOGS_BUCKET_NAME` is set, else `InMemoryArtifactService` (`app/agent_runtime.py`).
- Root agent is still event-concierge oriented (`TravelCoordinator` -> `FullPipeline`) (`app/agent.py`), not resume-refiner domain.

ADK documentation checks used for scope validation:

- ADK sessions documentation states that in-memory session/state data is for local testing and is lost on restart; persistent session services are needed for durable continuity (`https://adk.dev/sessions/index.md`).
- Existing architecture notes remain valid: split tooling and strict schema formatting into separate agents when needed.

**As-Is requirement:** Backend has a working synchronous ADK chat path, but domain logic and session durability do not yet match resume-refiner product goals.

#### 6) Guardrails As-Is (for MVP)

- No Redis settings for rate limiting in current settings surface (`app/settings.py`)
- No per-user LLM call limiter in API dependencies/middleware
- No 5 MB CV upload validation path yet (CV upload endpoint not implemented)
- No 500-char chat input validation in `ChatMessageIn`
- No explicit timeout wrapper around model execution in `ChatService` (`app/services/chat_service.py`)

---

### Backlog to reach To-Be MVP

#### P0 — must-have to match the To-Be MVP loop

| Area | Work |
|------|------|
| **Conversation lifecycle API (HTTP)** | Add authenticated create/list/get endpoints for conversations and ownership checks; keep delete optional for MVP. |
| **Conversation payload model** | Add persistent conversation binding fields for JD text and one CV reference/parsed markdown; enforce one-JD/one-CV-per-conversation rule. |
| **CV ingestion pipeline** | Add upload endpoint and storage path, enforce 5 MB cap, parse PDF to markdown with Marker, and persist parse result/errors. |
| **Gap analysis schema contract (`gap_analysis_v1`)** | Define fixed JSON response schema and validator for structured gap analysis fields. |
| **Gap analysis failure behavior** | On invalid model output, return explicit failure response without repair pipeline or partial `errors[]` semantics. |
| **Resume refinement pipeline (domain rewrite)** | Replace travel-concierge root and sub-agent instructions/IO contracts with resume refinement flow (analyze gaps -> draft/refine resume -> finalize output). |
| **Message validation + history behavior** | Enforce 500-char max for user refinement messages; keep conversation message history append-only/read-only. |
| **Server-side final resume assembler** | Implement deterministic ordered assembly: Skills, Experience, Projects, Education, Others, with stable omission rules for empty sections. |
| **Output persistence + preview artifacts** | Store latest refined resume as markdown plus rendered HTML and expose preview retrieval contract for frontend. |
| **Idempotent export endpoint** | Add export endpoint that returns latest persisted refined output only (no fresh generation). Include metadata needed for copy and browser print workflow. |
| **Auth on all HTTP LLM routes** | Ensure every LLM-triggering HTTP endpoint is protected by Clerk JWT dependency and ownership checks where applicable. |
| **Redis per-user LLM limits** | Add Redis integration for configurable per-user LLM call budget (default 200/rolling 24h), return stable 429 response on limit exceeded. |
| **Timeout policy** | Add bounded timeouts around LLM/parse calls and map timeout failures to clear API errors. |
| **A2A auth policy decision** | Choose and implement one policy: protect A2A entrypoint, disable it for product deployment, or mark it as dev-only and keep product LLM traffic on `/api/v1` only. |
| **Storage schema and migrations** | Add schema/migration path for conversation JD, CV parse output, gap snapshots, refined outputs, and export metadata (or document external schema ownership if migrations are managed outside repo). |

#### P1 — recommended but not strictly required to ship

- **Optional cover-letter flow:** Add cover-letter generation and separate copy/export actions.
- **Session persistence upgrade:** Move ADK session backing from in-memory to persistent service strategy aligned with production durability needs.
- **Observability for schema and limits:** Track schema validation failures, timeout rates, 429 rate-limit events, and export usage metrics.
- **Export length warning:** Add warning signal for page-length target (1 page preferred, 2 max) without blocking export.
- **Refined artifact versioning:** Keep revision history/snapshots for refined outputs and expose rollback-ready metadata when needed.
- **Deferred full-scope product features:** Multi-CV library (max-3 + primary rule), post-analysis CV lock, conversation retention auto-eviction, malformed-output repair and partial responses.
