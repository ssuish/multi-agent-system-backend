# Documentation index

**Last reviewed:** 2026-04-21

FastAPI service exposing an [A2A](https://a2a-protocol.org/) agent built with [Google ADK](https://google.github.io/adk-docs/), plus authenticated REST APIs backed by Postgres (asyncpg). Generated from the Agent Starter Pack; customized with Clerk JWT auth, Supabase-compatible DB URL, and optional MCP stdio tools.

## Contents

- [architecture.md](architecture.md) — Startup, A2A vs REST, agent runner, data flow
- [modules.md](modules.md) — `app/` package map and notable files
- [integrations.md](integrations.md) — Clerk, Postgres, GCP/Vertex, MCP env surface
- [testing.md](testing.md) — Test layout and Makefile commands

## Related design docs (non-authoritative)

Long-form plans and specs live under [docs/superpowers/](superpowers/). Prefer **this `docs/` reference** for “what the tree does today”; use superpowers docs for historical intent and roadmaps.

## Changelog

- 2026-04-21: Refactored `app/agent.py` pipeline to comply with ADK's "tools XOR output_schema" rule — split research and selection stages into researcher+formatter pairs (`ResearchAgent` → `PlacesFormatter` → `InterestCheckAgent` → `SelectionFormatter` → `CalendarAgent` → `RoutingAgent`); softened `GOOGLE_MAPS_API_KEY` check to a warning; added explicit `GEMINI_MODEL` on every sub-agent.
- 2026-04-20: Reconciled docs with current `app/agent.py` travel-concierge flow; clarified MCP helpers are present but not wired into active agent tools; documented `GOOGLE_MAPS_API_KEY` startup requirement.
- 2026-04-18: Moved reference docs from `docs/memory/` to `docs/` (same filenames).
- 2026-04-18: Refreshed against `app/`: `/api/v1` includes chat (`POST .../conversations/{id}/messages`); testing layout updated.
- 2026-04-18: Initial snapshot (skill-driven).
