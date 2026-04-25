# Documentation index

**Last reviewed:** 2026-04-25

FastAPI service exposing an [A2A](https://a2a-protocol.org/) agent built with [Google ADK](https://google.github.io/adk-docs/), plus authenticated REST APIs backed by Postgres (asyncpg). Generated from the Agent Starter Pack; customized with Clerk JWT auth, Supabase-compatible DB URL, and optional MCP stdio tools.

## Contents

- [architecture.md](architecture.md) — Startup, A2A vs REST, agent runner, data flow
- [modules.md](modules.md) — `app/` package map and notable files
- [integrations.md](integrations.md) — Clerk, Postgres, GCP/Vertex, MCP env surface
- [testing.md](testing.md) — Test layout and Makefile commands

## Changelog

- 2026-04-25: Refreshed docs against current `/api/v1` routes; added `conversations` router and `ConversationService` coverage to `modules.md` and `architecture.md`.
- 2026-04-25: Rewrote [prd.md](prd.md) to a trimmed MVP scope; refreshed To-Be constraints, As-Is analysis, and P0/P1 backlog with auth/limits/timeout guardrails.
- 2026-04-22: Added [prd.md](prd.md) to the documentation index; formatted MVP PRD (To-Be / As-Is / backlog).
- 2026-04-21: Refactored `app/agent.py` pipeline to comply with ADK's "tools XOR output_schema" rule — split research and selection stages into researcher+formatter pairs (`ResearchAgent` → `PlacesFormatter` → `InterestCheckAgent` → `SelectionFormatter` → `CalendarAgent` → `RoutingAgent`); softened `GOOGLE_MAPS_API_KEY` check to a warning; added explicit `GEMINI_MODEL` on every sub-agent.
- 2026-04-20: Reconciled docs with current `app/agent.py` travel-concierge flow; clarified MCP helpers are present but not wired into active agent tools; documented `GOOGLE_MAPS_API_KEY` startup requirement.
- 2026-04-18: Moved reference docs from `docs/memory/` to `docs/` (same filenames).
- 2026-04-18: Refreshed against `app/`: `/api/v1` includes chat (`POST .../conversations/{id}/messages`); testing layout updated.
- 2026-04-18: Initial snapshot (skill-driven).
