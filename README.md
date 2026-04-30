# multi-agent-system

MVP backend for **JD–resume gap analysis and refinement** as specified in **[docs/prd.md](docs/prd.md)** — Clerk JWT, one CV and one JD per conversation, structured gap output (`gap_analysis_v1`), synchronous refinement with bounded inputs, append-only chat history, ordered section assembly for the final resume, persisted markdown/HTML preview, **idempotent export** of latest output, Redis **per-user LLM budgets** (429) and bounded **timeouts** in the target design.

**Stack:** FastAPI, Postgres (asyncpg), **[Google ADK](https://google.github.io/adk-docs/)**, **[A2A](https://a2a-protocol.org/)** under `/a2a/app/`. What is implemented versus backlog is spelled out in the PRD **As-Is** and **Backlog** sections.

**Docs:** [docs/INDEX.md](docs/INDEX.md) · **Technical gaps:** [docs/tech_debts.md](docs/tech_debts.md)

---

## Starter pack vs. this repo

Bootstrapped from [Google Cloud Agent Starter Pack](https://github.com/GoogleCloudPlatform/agent-starter-pack) (`adk_a2a`, v0.41.0): ADK/A2A app shape, GCP-oriented `Makefile` targets, telemetry hooks, and linked starter-pack guides.

**Added or extended here:**

- **REST** — `/api/v1` (profiles, conversations, chat); schemas under `app/api/v1/`.
- **Auth** — Clerk JWKS JWT verification (`app/auth/`).
- **Data layer** — asyncpg pool, migrations, repositories, services (`app/db/`, `app/repositories/`, `app/services/`).
- **`docs/`** — PRD (`prd.md`), architecture, integrations, testing, tech debt.
- **`app/agent.py`** — still coming from old implementation of multi-stage agent; **To be replace with resume refinement** per PRD P0 backlog (see architecture for current staging patterns).

---

## Project layout

```
multi-agent-system/
├── app/
│   ├── agent.py / agent_runtime.py   # ADK app, runner, pipeline
│   ├── fast_api_app.py               # FastAPI app: lifespan, CORS, A2A mount, REST
│   ├── api/v1/                       # REST routers and schemas
│   ├── auth/                         # Clerk JWT deps
│   ├── db/                           # Pool + migrations
│   ├── repositories/                 # Asyncpg data access
│   ├── services/                     # Conversation / chat orchestration
│   ├── app_utils/                    # Telemetry, helpers
│   └── mcp/                          # MCP client helpers (optional; see docs)
├── docs/                             # Architecture, integrations, PRD, testing
├── tests/                            # Unit + integration
├── GEMINI.md                         # AI-assisted dev notes (Gemini CLI)
├── Makefile                          # install, lint, test, backend, playground, deploy
└── pyproject.toml
```

---

## Requirements

- **[uv](https://docs.astral.sh/uv/getting-started/installation/)** — Python deps and runs (e.g. `uv run`, `uv sync`).
- **[Google Cloud SDK](https://cloud.google.com/sdk/docs/install)** — For default credentials, logging, and deploy targets that use GCP.
- **make** — Preinstalled on most Unix systems.

---

## Configuration

Environment variables are listed in [docs/integrations.md](docs/integrations.md). Copy `.env.example` to `.env` for local development. On Cloud Run, set the same names via `gcloud run services update` or the console (see `make deploy-help`).

---

## Quick start

```bash
make install && make playground
```

`playground` runs the ADK web UI for the agent. For the **HTTP API** (REST + A2A on one process):

```bash
make local-backend
```

---

## Commands

| Command | Description |
| -------- | ----------- |
| `make install` | Install dependencies with uv |
| `make playground` | ADK web playground (agent dev) |
| `make local-backend` | FastAPI + hot reload (default port 8000; `PORT=8001 make local-backend` for parallel runs) |
| `make lint` | codespell + `ruff check`/`format --check` + `ty check` |
| `make test` | Unit and integration tests |
| `make deploy` | Deploy to Cloud Run (requires gcloud project setup) |
| `make deploy-help` | Env var hints for Cloud Run |
| `make inspector` | A2A Protocol Inspector |

Full options: [Makefile](Makefile).

### Optional: starter-pack upgrades

| Command | Purpose |
| -------- | -------- |
| `uvx agent-starter-pack enhance` | Add CI/CD and Terraform |
| `uvx agent-starter-pack setup-cicd` | One-shot CI/CD + infra |
| `uvx agent-starter-pack upgrade` | Upgrade template while preserving customizations |
| `uvx agent-starter-pack extract` | Minimal shareable agent slice |

---

## Development

- Agent behavior: `app/agent.py` — iterate with `make playground` (reload).
- HTTP surface: `app/fast_api_app.py`, `app/api/v1/`.
- Starter-pack workflow: [development guide](https://googlecloudplatform.github.io/agent-starter-pack/guide/development-guide).
- [Gemini CLI](https://github.com/google-gemini/gemini-cli): project notes in [GEMINI.md](GEMINI.md).

---

## Deployment

```bash
gcloud config set project <your-project-id>
make deploy
```

CI/CD and Terraform: `uvx agent-starter-pack enhance` and [deployment guide](https://googlecloudplatform.github.io/agent-starter-pack/guide/deployment).

---

## Observability

Telemetry aligns with starter-pack patterns (Cloud Trace / logging / BigQuery-oriented setup as configured). Details: [observability guide](https://googlecloudplatform.github.io/agent-starter-pack/guide/observability).

---

## A2A

[A2A Protocol](https://a2a-protocol.org/) RPC is mounted at `/a2a/app/`. Product auth policy for A2A is an open PRD backlog item (`make inspector`; [A2A Inspector](https://github.com/a2aproject/a2a-inspector)).
