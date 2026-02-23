# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-18)

**Core value:** AI copilot that explains CNC post processor logic in plain English -- so CAM engineers can understand, modify, and troubleshoot posts without tribal knowledge or machine time
**Current focus:** Phase 1 -- Foundation

## Current Position

Phase: 1 of 5 (Foundation)
Plan: 3 of 4 in current phase
Status: Executing -- Plans 01-01, 01-02, and 01-03 complete. Plan 01-04 still blocked (corpus download).
Last activity: 2026-02-23 -- Plan 01-03 (async ingestion pipeline) completed

Progress: [████░░░░░░] 15%

## Performance Metrics

**Velocity:**
- Total plans completed: 3
- Average duration: 32 min
- Total execution time: 1.62 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-foundation | 3 | 97 min | 32 min |

**Recent Trend:**
- Last 5 plans: 01-01 (8 min), 01-02 (8 min), 01-03 (81 min)
- Trend: 01-03 longer due to full Docker build/test cycle with Celery + MinIO integration

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Roadmap]: Phase 1 holds no v1 requirements -- it is pure infrastructure prerequisite. All 19 requirements distributed across Phases 2-5.
- [Roadmap]: ACCT-01/ACCT-02 (auth) placed in Phase 3 (Post Repository) -- authentication gates the first user-facing milestone.
- [Roadmap]: AUTH-01..04 + AI-04 form Phase 5 (Authoring Workflow) -- these require AI copilot core (Phase 4) to be validated first.
- [01-01]: Removed alembic from api startup command -- alembic.ini does not exist yet, Plan 01-02 creates it
- [01-01]: Fixed build-backend from broken setuptools.backends._legacy:_Backend to setuptools.build_meta
- [01-01]: Removed aiosqlite, replaced with asyncpg -- PostgreSQL is the only database going forward
- [01-02]: Module-level async functions instead of class-based PostService -- simpler, no state to manage
- [01-02]: Eager-load files relationship on all package queries to avoid async lazy-load issues
- [01-02]: Parsing endpoint returns 501 stub until Phase 2 parser is real
- [01-02]: Single-file upload as placeholder; ZIP upload deferred to Plan 01-03
- [01-03]: Celery tasks use synchronous psycopg2 + boto3 (not async) since Celery workers are synchronous
- [01-03]: Package name derived from first .SRC filename in uploaded ZIP
- [01-03]: Nested ZIP directories flattened to filename-only (handles Windows zip behavior)
- [01-03]: ErrorResponse model established as platform-wide error pattern (friendly message + expandable detail)

### Pending Todos

None yet.

### Blockers/Concerns

- [Phase 2]: Parser is the lynchpin. UPG format is proprietary with sparse public docs. Structure catalog from Phase 1 corpus collection is a hard prerequisite.
- [Phase 4]: AI confabulation risk on proprietary UPG constructs. SME validation gate (50+ scored question/answer pairs) must pass before copilot reaches engineers.
- [Phase 2]: Research flag -- run /gsd:research-phase for UPG language structure before planning Phase 2.
- [Phase 4]: Research flag -- run /gsd:research-phase for ContextBuilder design and AI prompt engineering before planning Phase 4.

## Session Continuity

Last session: 2026-02-23
Stopped at: Completed 01-03-PLAN.md (async ingestion pipeline) -- only Plan 01-04 remains in Phase 1
Resume with: `/gsd:execute-phase 1` -- will attempt Plan 01-04 (UPG corpus, still blocked on SharePoint download)

### Completed Plans
- **01-01 (Docker Compose):** Complete. 5-service stack verified running. Commit `1543708`.
- **01-02 (PostgreSQL + MinIO):** Complete. SQLAlchemy ORM, Alembic migration, MinIO storage, API rewrite. Commits `7cd05f5`, `97b33f2`.
- **01-03 (Async Ingestion):** Complete. Celery task, ZIP upload, status polling, UPG validation. Commits `763b047`, `aef0a8d`.

### Remaining Checkpoints

**Plan 01-04 (UPG Corpus):** Blocked on Task 1 -- Need 18+ more corpus files from SharePoint.
- User action: Download UPG packages from HRS SharePoint into accessible folder
- Target: ~6 HAAS, ~7 Fanuc, ~7 Mori Seiki (20+ total with existing 2 HAAS)
- Resume signal: Provide path + counts per controller type
- After checkpoint: Agent scans corpus and produces UPG-STRUCTURE-CATALOG.md

### Execution Order Remaining
Plan 01-04 (blocked on corpus) --> Phase 1 verification

Note: 3 of 4 plans complete. Phase 1 cannot be fully closed until 01-04 corpus collection is done.
