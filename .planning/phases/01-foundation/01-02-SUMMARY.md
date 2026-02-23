---
phase: 01-foundation
plan: 02
subsystem: database, infra
tags: [postgresql, asyncpg, sqlalchemy, alembic, minio, aiobotocore, pgvector, s3]

# Dependency graph
requires:
  - phase: 01-foundation-01
    provides: "Docker Compose 5-service stack (postgres, redis, minio, api, worker)"
provides:
  - "SQLAlchemy ORM models (PostPackage, PostFile) for post processor data"
  - "Alembic async migration infrastructure with initial schema"
  - "MinIO StorageService for async file upload/download/list/delete"
  - "Rewritten API routes backed by PostgreSQL and MinIO"
  - "pgvector extension enabled for future embedding storage"
affects: [01-foundation-03, 02-parser, 03-repository]

# Tech tracking
tech-stack:
  added: [sqlalchemy-orm, alembic-async, aiobotocore, pgvector-extension]
  patterns: [async-sqlalchemy-crud, selectinload-eager-loading, module-level-service-functions, minio-prefix-per-package]

key-files:
  created:
    - app/db/models.py
    - app/services/storage.py
    - app/api/routes/packages.py
    - alembic.ini
    - alembic/env.py
    - alembic/script.mako
    - alembic/versions/001_initial_schema.py
  modified:
    - app/config.py
    - app/db/database.py
    - app/core/models/post_processor.py
    - app/services/post_service.py
    - app/api/routes/posts.py
    - app/api/routes/parsing.py
    - app/main.py
    - Dockerfile
    - docker-compose.yml

key-decisions:
  - "Module-level async functions instead of class-based PostService -- simpler, no state to manage"
  - "Eager-load files relationship on all package queries to avoid async lazy-load issues"
  - "Parsing endpoint returns 501 stub until Phase 2 parser is real"
  - "Single-file upload as placeholder; ZIP upload deferred to Plan 01-03"

patterns-established:
  - "Async CRUD: module-level async functions accepting AsyncSession as first param"
  - "Storage keys: packages/{uuid}/ prefix per package in MinIO"
  - "Pydantic from_attributes: ORM models serialize directly to response schemas"
  - "Alembic at startup: sh -c alembic upgrade head && uvicorn in docker-compose command"

requirements-completed: []

# Metrics
duration: 8min
completed: 2026-02-23
---

# Phase 1 Plan 02: PostgreSQL + MinIO Persistence Summary

**SQLAlchemy async ORM with Alembic migrations replacing in-memory _store, MinIO storage service for file upload/download, all API routes rewritten against PostgreSQL**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-23T21:53:15Z
- **Completed:** 2026-02-23T22:01:24Z
- **Tasks:** 2
- **Files modified:** 16 (7 created, 9 modified)

## Accomplishments
- PostPackage and PostFile ORM models with Alembic async migration creating tables and pgvector extension
- MinIO StorageService with async upload/download/list/delete operations using aiobotocore
- All API routes rewritten: list/get/upload packages from PostgreSQL, file download from MinIO
- Complete elimination of in-memory _store dict and SQLite references from codebase
- File round-trip verified: upload through API, stored in MinIO, download returns identical bytes

## Task Commits

Each task was committed atomically:

1. **Task 1: Settings, SQLAlchemy models, and Alembic migration** - `7cd05f5` (feat)
2. **Task 2: MinIO storage service and API route rewrite** - `97b33f2` (feat)

**Plan metadata:** (pending -- docs commit)

## Files Created/Modified
- `app/db/models.py` - SQLAlchemy ORM models for PostPackage and PostFile
- `app/services/storage.py` - Async MinIO client (StorageService) with module-level singleton
- `app/api/routes/packages.py` - Package file download endpoint
- `alembic.ini` - Alembic configuration with async PostgreSQL
- `alembic/env.py` - Async migration runner importing Base metadata
- `alembic/script.mako` - Migration template
- `alembic/versions/001_initial_schema.py` - Initial schema: post_packages, post_files, pgvector
- `app/config.py` - Removed corpus_dir field (corpus lives in MinIO)
- `app/db/database.py` - Added pool_size=5, max_overflow=10 for connection pooling
- `app/core/models/post_processor.py` - Rewritten Pydantic schemas (PackageResponse, FileResponse, PackageListResponse)
- `app/services/post_service.py` - Complete rewrite: async functions replacing PostService class and _store
- `app/api/routes/posts.py` - Rewritten to use DB sessions and new service layer
- `app/api/routes/parsing.py` - Simplified to 501 stub
- `app/main.py` - Added storage init, packages router, removed init_db
- `Dockerfile` - Added COPY for alembic.ini and alembic/
- `docker-compose.yml` - Added alembic upgrade head to api command, mounted alembic volume

## Decisions Made
- Used module-level async functions instead of PostService class (simpler, no instance state needed)
- Added selectinload on all package queries to prevent async lazy-loading errors with Pydantic serialization
- Kept init_db() in database.py for testing use but removed from app startup (Alembic handles production migrations)
- Single-file upload endpoint preserved as placeholder; full ZIP upload is Plan 01-03 scope
- Parsing route returns 501 Not Implemented until Phase 2 builds the UPG parser

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed lazy-loading error on list_packages endpoint**
- **Found during:** Task 2 (API route rewrite)
- **Issue:** list_packages query did not eagerly load the files relationship. When Pydantic tried to serialize PackageResponse.files, SQLAlchemy raised MissingGreenlet because lazy loading requires an async context that Pydantic does not provide.
- **Fix:** Added `.options(selectinload(PostPackage.files))` to the list_packages query
- **Files modified:** app/services/post_service.py
- **Verification:** GET /api/v1/posts/ returns packages with files array populated
- **Committed in:** 97b33f2 (amended into Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Essential fix for correctness. No scope creep.

## Issues Encountered
None beyond the lazy-loading bug documented above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- PostgreSQL schema ready for Plan 01-03 (async ingestion pipeline with Celery)
- MinIO storage service ready for ZIP upload endpoint (Plan 01-03)
- API contract established: packages with files, file download from MinIO
- pgvector extension installed and ready for Phase 2 embedding storage

## Self-Check: PASSED

- All 7 created files verified on disk
- Both task commits verified in git log (7cd05f5, 97b33f2)
- Docker verification completed: migration ran, tables created, pgvector installed, API endpoints functional, file round-trip confirmed

---
*Phase: 01-foundation*
*Completed: 2026-02-23*
