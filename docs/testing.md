# Testing

## Commands

From [`Makefile`](../Makefile):

| Command | What it runs |
|---------|----------------|
| `make test` | `uv sync --dev` then `pytest tests/unit` then `pytest tests/integration` |
| `make lint` | `codespell`, `ruff check`, `ruff format --check`, `ty check` |
| `make local-backend` | `uvicorn app.fast_api_app:app` with reload (optional `PORT=`) |
| `make playground` | `adk web .` for local ADK UI |
| `make eval` | ADK eval with optional `EVALSET` / `EVAL_CONFIG` |

## Layout

| Path | Purpose |
|------|---------|
| [`tests/unit/`](../tests/unit/) | Unit tests: Clerk JWT, profiles API, chat service, etc. |
| [`tests/integration/`](../tests/integration/) | A2A HTTP against a running server (`test_server_e2e.py`), ADK `Runner` (`test_agent.py`) |
| [`tests/eval/`](../tests/eval/) | ADK evalset JSON and config for `make eval` |

## Conventions

- Integration tests may spawn the server or assume network; see each file’s docstring and fixtures.
- Optional dependency groups in [`pyproject.toml`](../pyproject.toml): `lint`, `eval`, `agent_eval`, etc., synced via `make` targets as needed.
