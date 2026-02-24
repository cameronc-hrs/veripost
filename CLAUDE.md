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
app/               # FastAPI application
  api/routes/      # API endpoints (health, posts, packages, parsing)
  core/            # Domain models, constants, AI, parsing
  db/              # Database layer (models.py, database.py)
  services/        # Business logic (post_service.py, storage.py)
  workers/         # Celery tasks (celery_app.py, tasks.py)
alembic/           # Database migrations
.planning/         # GSD planning files
  ROADMAP.md       # 5-phase roadmap
  STATE.md         # Current execution state (READ THIS FIRST)
  PROJECT.md       # Project definition and decisions
  REQUIREMENTS.md  # All 19 v1 requirements
  phases/01-foundation/  # Phase 1 plans and artifacts
```

## Current State (2026-02-23)

**Phase 1: Foundation** — 3 of 4 plans complete. Only Plan 01-04 (UPG Corpus) remains.

**Completed:**
- Plan 01-01: Docker Compose 5-service stack (api, worker, postgres, redis, minio)
- Plan 01-02: PostgreSQL + MinIO persistence (Alembic, ORM models, storage service, API rewrite)
- Plan 01-03: Async ZIP ingestion pipeline (Celery task, upload endpoint, validation, status polling)

**Still blocked:** Plan 01-04 (UPG Corpus) — needs 18+ more corpus files from HRS SharePoint
- Target: ~6 HAAS, ~7 Fanuc, ~7 Mori Seiki (20+ total)
- Resume signal: Provide file path + counts per controller type
- After checkpoint: Agent scans corpus and produces UPG-STRUCTURE-CATALOG.md

**Resume:** `/gsd:execute-phase 1` — will attempt Plan 01-04, then verify phase

## What's Working

- `docker compose up` starts all 5 services
- `POST /api/v1/packages/upload` accepts ZIP, validates UPG extensions, stores in MinIO, enqueues Celery task
- `GET /api/v1/packages/{id}/status` shows ingestion progress (pending→validating→storing→parsing→ready)
- `GET /api/v1/packages/{id}/files/{file_id}/download` returns file bytes from MinIO
- Alembic migration runs automatically on container startup
- PostgreSQL has post_packages + post_files tables with pgvector extension

## Key Decisions

- Phase 1 is pure infrastructure — no v1 requirements, all 19 distributed across Phases 2-5
- Celery tasks use synchronous psycopg2 + boto3 (Celery workers can't use async)
- ErrorResponse model = friendly message + expandable detail (platform-wide pattern)
- Package name derived from first .SRC filename in uploaded ZIP
- Nested ZIP directories flattened to filename-only
- Parsing endpoint returns 501 stub until Phase 2

## Commands

- `/gsd:progress` — check status and next action
- `/gsd:execute-phase 1` — resume phase 1 (will run Plan 01-04 when corpus files provided)
- `/gsd:plan-phase N` — plan a phase before execution
