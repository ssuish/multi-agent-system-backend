# Integrations

## Overview

| System | Purpose | Configuration surface |
|--------|---------|-------------------------|
| **Postgres** (e.g. Supabase) | Profiles, conversations, messages | `database_url` in [`app/settings.py`](../app/settings.py) |
| **Clerk** | End-user JWT auth for REST | `clerk_jwks_url`, `clerk_issuer`, optional `clerk_audience` |
| **Google Cloud** | Default credentials, logging, Vertex AI for Gemini | `google.auth.default()`, env in [`app/agent.py`](../app/agent.py) / ADK |
| **MCP (stdio)** | Optional MCP client helpers present in codebase (not currently attached to active `root_agent`) | `mcp_enabled`, `mcp_server_command` (JSON array string) |
| **GCS** (optional) | ADK artifact storage when deployed | `LOGS_BUCKET_NAME` read in [`app/agent_runtime.py`](../app/agent_runtime.py) |

## Environment variables

**Pydantic Settings** ([`app/settings.py`](../app/settings.py)): loaded from process environment and optional `.env` in the project root. In environment variables, names are **uppercase** (pydantic-settings default). In `.env` files you may use the same uppercase names.

| Env name | Required | Default | Purpose |
|----------|----------|---------|---------|
| `DATABASE_URL` | Yes | — | Async Postgres DSN for asyncpg (e.g. Supabase). |
| `CLERK_JWKS_URL` | Yes | — | Clerk JWKS URL for JWT verification. |
| `CLERK_ISSUER` | Yes | — | Expected JWT `iss` claim. |
| `CLERK_AUDIENCE` | No | — | Optional `aud` / `azp` verification. |
| `CORS_ORIGINS` | No | `http://localhost:3000` | Comma-separated browser origins for CORS. |
| `MCP_ENABLED` | No | `false` | Settings flag for MCP stdio integration (client code exists, but active `root_agent` does not currently call it). |
| `MCP_SERVER_COMMAND` | When MCP enabled | — | JSON array string for MCP stdio server command used by `app/mcp/mcp_client.py`, e.g. `["npx","-y","@modelcontextprotocol/server-everything"]`. |
| `GOOGLE_MAPS_API_KEY` | No | — | Read in [`app/agent.py`](../app/agent.py); logs a warning if missing. Required only when the (currently commented-out) live Maps/MCP tools are re-enabled. |

**Direct `os.environ` / `os.getenv` (not in Settings)**

| Env name | Where read | Required (typical) | Default | Purpose |
|----------|------------|--------------------|---------|---------|
| `APP_URL` | [`app/fast_api_app.py`](../app/fast_api_app.py) `build_dynamic_agent_card` | Prod: yes for correct A2A card URL | `http://0.0.0.0:8000` | Public base URL of the API (no trailing slash); combined with A2A RPC path for `rpc_url`. |
| `AGENT_VERSION` | [`app/fast_api_app.py`](../app/fast_api_app.py) | No | `0.1.0` | Agent version string on the agent card. Dockerfile / `make deploy` may set this. |
| `LOGS_BUCKET_NAME` | [`app/agent_runtime.py`](../app/agent_runtime.py), [`app/app_utils/telemetry.py`](../app/app_utils/telemetry.py) | No | — | If set, enables GCS-backed ADK artifact service (`agent_runtime`) and may enable GenAI telemetry upload path setup (`telemetry`) when combined with capture settings (see below). Use a **bucket name** (no `gs://` prefix); paths like `gs://...` are built in code. |
| `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT` | [`app/app_utils/telemetry.py`](../app/app_utils/telemetry.py) | No | `false` | When set to a value other than `false` **and** `LOGS_BUCKET_NAME` is set, telemetry enables upload-related OTEL variables (code may normalize to `NO_CONTENT`). |
| `COMMIT_SHA` | [`app/app_utils/telemetry.py`](../app/app_utils/telemetry.py) | No | `dev` | Shipped in container via Dockerfile `ARG`/`ENV`; used in `OTEL_RESOURCE_ATTRIBUTES`. |
| `GENAI_TELEMETRY_PATH` | [`app/app_utils/telemetry.py`](../app/app_utils/telemetry.py) | No | `completions` | Path segment under the bucket for GenAI telemetry base path. |

**Set at import time in code (overrides / supplies SDK env)**

| Env name | Where set | Value | Purpose |
|----------|-----------|-------|---------|
| `GOOGLE_CLOUD_PROJECT` | [`app/agent.py`](../app/agent.py) | From `google.auth.default()` | Vertex / GenAI routing. |
| `GOOGLE_CLOUD_LOCATION` | [`app/agent.py`](../app/agent.py) | `global` | Vertex location. |
| `GOOGLE_GENAI_USE_VERTEXAI` | [`app/agent.py`](../app/agent.py) | `True` | Use Vertex for Gemini. |

**Set inside `setup_telemetry()` when bucket logging path is active** (callers do not set these manually unless overriding): `OTEL_INSTRUMENTATION_GENAI_UPLOAD_FORMAT`, `OTEL_INSTRUMENTATION_GENAI_COMPLETION_HOOK`, `OTEL_SEMCONV_STABILITY_OPT_IN`, `OTEL_RESOURCE_ATTRIBUTES`, `OTEL_INSTRUMENTATION_GENAI_UPLOAD_BASE_PATH`, and possibly `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT` (normalized). See [`app/app_utils/telemetry.py`](../app/app_utils/telemetry.py).

**Container / deploy**

| Env name | Where set | Purpose |
|----------|-----------|---------|
| `COMMIT_SHA` | [`Dockerfile`](../Dockerfile) build arg | Image metadata / telemetry resource attributes. |
| `AGENT_VERSION` | [`Dockerfile`](../Dockerfile), [`Makefile`](../Makefile) `deploy` | Agent version in container and on Cloud Run. |
| `APP_URL` | [`Makefile`](../Makefile) `deploy` | Production service URL for the agent card. |

**Tests only**

| Env name | Where | Purpose |
|----------|-------|---------|
| `INTEGRATION_TEST` | [`tests/integration/test_server_e2e.py`](../tests/integration/test_server_e2e.py) | Set to `TRUE` by the integration test harness; not read by application code in `app/`. |

### Maintenance rule

Whenever you add or remove an environment variable read in `app/`, update **this section** and the root **`.env.example`** in the same pull request. Optionally run `rg 'getenv|os\.environ' app/` before merging.

Do **not** commit real values; use `.env` locally and plain Cloud Run environment variables (or a secret manager) in production.

## Related code

- [`app/settings.py`](../app/settings.py) — Central settings model
- [`app/auth/clerk_jwt.py`](../app/auth/clerk_jwt.py) — JWKS fetch and JWT validation
- [`app/mcp/mcp_client.py`](../app/mcp/mcp_client.py) — MCP stdio client
