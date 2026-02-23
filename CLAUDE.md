# VeriPost — Claude Code Context

## What This Project Is

AI copilot platform for CNC post processor engineers. Explains UPG post processor logic in plain English so CAM engineers can understand, modify, and troubleshoot posts without tribal knowledge or machine time.

## Tech Stack

- **Backend:** Python 3.11, FastAPI, SQLAlchemy (async), Celery
- **Database:** PostgreSQL + pgvector
- **Cache/Broker:** Redis
- **Object Storage:** MinIO (S3-compatible)
- **Frontend:** Next.js (Phase 3+)
- **AI:** Claude API (Phase 4+)
- **Infra:** Docker Compose (all services containerized)

## Project Structure

```
app/               # FastAPI application (existing scaffold)
  api/routes/      # API endpoints
  core/            # Domain models, AI, parsing
  db/              # Database layer
  services/        # Business logic
.planning/         # GSD planning files
  ROADMAP.md       # 5-phase roadmap
  STATE.md         # Current execution state (READ THIS FIRST)
  PROJECT.md       # Project definition and decisions
  REQUIREMENTS.md  # All 19 v1 requirements
  phases/01-foundation/  # Phase 1 plans and artifacts
```

## Current State (2026-02-23)

**Phase 1: Foundation** — executing. Plan 01-01 (Docker Compose) complete. Plan 01-02 (PostgreSQL + MinIO persistence) is next.

**Completed:**
- Plan 01-01: Docker Compose 5-service stack (api, worker, postgres, redis, minio) verified running

**Next up:** Plan 01-02 — Replace SQLite + in-memory `_store` with PostgreSQL (Alembic migrations) and MinIO object storage. This plan has 2 tasks:
1. Settings cleanup, SQLAlchemy ORM models, Alembic migration setup
2. MinIO storage service, rewrite API routes against PostgreSQL/MinIO

**Still blocked:** Plan 01-04 (UPG Corpus) — needs 18+ more corpus files from HRS SharePoint

**Resume:** `/gsd:execute-phase 1` — will pick up at Plan 01-02

## Key Decisions

- Phase 1 is pure infrastructure — no v1 requirements, all 19 distributed across Phases 2-5
- SQLite + in-memory `_store` are disposable (being replaced by PostgreSQL + MinIO in Plan 01-02)
- UPG format is proprietary — structure catalog from real corpus files is mandatory before Phase 2 parser work
- Phase 4 (AI Copilot) is the feasibility gate — 8-week window

## Commands

- `/gsd:progress` — check status and next action
- `/gsd:execute-phase 1` — resume phase 1 execution
- `/gsd:plan-phase N` — plan a phase before execution
