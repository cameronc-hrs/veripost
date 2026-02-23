---
phase: 01-foundation
plan: 03
subsystem: infra
tags: [celery, redis, minio, fastapi, zip-upload, async-pipeline, boto3, psycopg2]

# Dependency graph
requires:
  - phase: 01-foundation-01
    provides: "Docker Compose 5-service stack (API, worker, postgres, redis, minio)"
  - phase: 01-foundation-02
    provides: "SQLAlchemy ORM models (PostPackage, PostFile), MinIO storage service, Alembic migrations"
provides:
  - "Celery ingestion task skeleton with status tracking (pending -> validating -> storing -> parsing -> ready)"
  - "ZIP upload endpoint (POST /api/v1/packages/upload) with UPG extension validation"
  - "Status polling endpoint (GET /api/v1/packages/{id}/status)"
  - "UPG file extension constants (7 valid types)"
  - "ErrorResponse model for platform-wide error pattern"
  - "Sync DB/MinIO access pattern for Celery workers (psycopg2 + boto3)"
affects: [02-parser, 03-repository, 04-ai-copilot]

# Tech tracking
tech-stack:
  added: [psycopg2-binary, boto3]
  patterns: [celery-sync-worker, zip-upload-validation, friendly-error-responses, nested-zip-flattening]

key-files:
  created:
    - app/core/constants.py
    - app/workers/tasks.py
  modified:
    - app/workers/celery_app.py
    - app/workers/__init__.py
    - app/api/routes/packages.py
    - app/services/post_service.py
    - app/core/models/post_processor.py
    - pyproject.toml

key-decisions:
  - "Celery tasks use synchronous psycopg2 + boto3 (not async) since Celery workers are synchronous"
  - "Package name derived from first .SRC filename in uploaded ZIP"
  - "Nested ZIP directories flattened to filename-only (handles Windows 'Send to Compressed' behavior)"

patterns-established:
  - "ErrorResponse model: friendly message + expandable detail + machine-readable code for all API errors"
  - "Sync worker pattern: psycopg2 for DB, boto3 for MinIO inside Celery tasks (no async/await)"
  - "ZIP validation: extension whitelist + required .SRC + flatten nested dirs + skip __MACOSX"

requirements-completed: []

# Metrics
duration: 81min
completed: 2026-02-23
---

# Plan 01-03: Async Ingestion Pipeline Summary

**Celery ingestion task with ZIP upload, UPG extension validation, MinIO storage, and status polling endpoint**

## Performance

- **Duration:** 81 min
- **Started:** 2026-02-23T22:10:40Z
- **Completed:** 2026-02-23T23:32:24Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- Celery worker starts in Docker, connects to Redis, registers `ingest_package` task
- ZIP upload endpoint validates UPG extensions (7 types), requires .SRC, flattens nested dirs, returns 202
- Status polling endpoint tracks ingestion from pending through ready (or error)
- Full end-to-end verified: upload ZIP -> 202 -> Celery processes -> status reaches "ready"
- Error responses follow platform-wide "friendly message + expandable detail" pattern

## Task Commits

Each task was committed atomically:

1. **Task 1: Celery app, constants, and ingestion task skeleton** - `763b047` (feat)
2. **Task 2: ZIP upload endpoint with validation and status polling** - `aef0a8d` (feat)

## Files Created/Modified
- `app/core/constants.py` - UPG file extension whitelist (7 valid types: .SRC, .LIB, .CTL, .KIN, .ATR, .PINF, .LNG)
- `app/workers/celery_app.py` - Celery app renamed to `celery_app` for convention match with docker-compose `-A` flag
- `app/workers/tasks.py` - Ingestion task with sync DB/MinIO access, status flow tracking, error handling
- `app/workers/__init__.py` - Worker package init
- `app/api/routes/packages.py` - POST /upload (202) and GET /{id}/status endpoints
- `app/services/post_service.py` - validate_zip_contents(), extract_zip_files(), create_package_with_files()
- `app/core/models/post_processor.py` - ErrorResponse and StatusResponse Pydantic models
- `pyproject.toml` - Added psycopg2-binary and boto3 dependencies

## Decisions Made
- **Sync worker pattern:** Celery tasks use `sqlalchemy.create_engine` (psycopg2) and `boto3` instead of async equivalents. Celery tasks are synchronous -- attempting async/await would require running an event loop inside the task, which is fragile and unnecessary.
- **Package naming:** Package name is derived from the first .SRC filename found in the ZIP (e.g., `HAAS_VF-4.SRC` becomes package name `HAAS_VF-4`). This is the most meaningful identifier for engineers.
- **Directory flattening:** Nested ZIP directories are stripped, keeping only the filename. This handles the common case where engineers "Send to > Compressed folder" on Windows, creating nested structures like `HAAS_VF-4/HAAS_VF-4.SRC`.
- **Celery variable rename:** Renamed Celery instance from `app` to `celery_app` in celery_app.py for clarity and convention. Celery auto-discovers `celery_app` attribute when using `-A app.workers.celery_app`.

## Deviations from Plan

None -- plan executed exactly as written.

## Issues Encountered

None -- all Docker services started cleanly, all verifications passed on first attempt.

## User Setup Required

None -- no external service configuration required.

## Next Phase Readiness
- Async ingestion pipeline is complete and verified end-to-end
- Parse step in Celery task is a documented stub awaiting Phase 2 parser implementation
- Plan 01-04 (UPG Corpus) is still blocked on corpus file download from SharePoint
- Phase 1 success criterion #3 is satisfied: "An async ingestion job skeleton accepts an uploaded file, enqueues it to Celery/Redis, and returns a job ID"

## Self-Check: PASSED

All 9 files verified present. Both task commits (763b047, aef0a8d) confirmed in git log.

---
*Phase: 01-foundation*
*Completed: 2026-02-23*
