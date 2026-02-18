# Stack Research

**Domain:** CNC Post Processor Management Platform (VeriPost)
**Researched:** 2026-02-18
**Confidence:** MEDIUM (stack is explicitly specified in PROJECT.md; versions verified via training data to August 2025, flagged where currency is uncertain)

---

## Executive Context

The stack is **pre-decided** in the project constraints. This document's job is to:
1. Confirm versions are current and compatible
2. Identify the right supporting libraries within each technology
3. Call out integration gotchas specific to this domain
4. Flag what the scaffold got wrong and needs to change

The existing FastAPI scaffold uses SQLite + in-memory store. The target stack adds PostgreSQL+pgvector, Redis, and MinIO — each requiring non-trivial migration steps. The frontend does not exist yet.

---

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Next.js | 15.x (App Router) | Frontend framework | App Router with React Server Components enables streaming AI responses naturally; built-in API routes reduce ops complexity for thin BFF layer; Vercel ecosystem for easy deploy |
| React | 19.x | UI library | Bundled with Next.js 15; concurrent features handle Monaco Editor's heavy rendering without blocking UI |
| TypeScript | 5.x | Type safety | Non-negotiable for a domain with complex nested data models (ParsedPost, UPG AST, machine registry); catches interface drift between frontend and backend |
| Python | 3.11+ | Backend runtime | Already pinned in pyproject.toml; 3.11 brings significant performance improvements for I/O-bound async workloads; 3.12+ viable but 3.11 is the safest LTS target |
| FastAPI | 0.115+ | Backend framework | Already in scaffold; best-in-class async Python web framework; Pydantic v2 integration for free validation; automatic OpenAPI generation eliminates hand-maintaining API contracts with frontend |
| PostgreSQL | 16.x | Primary database | pgvector extension requires pg14+; pg16 is current stable with best pgvector performance; replaces SQLite from scaffold |
| pgvector | 0.7+ | Vector similarity search | Enables semantic search across post processor corpus; stored as embedding columns on existing Postgres tables; no separate vector DB needed for this scale |
| Redis | 7.x | Cache + task queue | Used for: (1) caching expensive AI responses per post+question hash, (2) background job queue for parsing large .SRC files, (3) rate-limit counters for Claude API calls |
| MinIO | latest (RELEASE.2024+) | S3-compatible file storage | Stores raw post processor file packages (.SRC, .LIB, .CTL, etc.); local dev replacement for AWS S3; same boto3/S3 API so production swap is env-var only |
| Anthropic Claude API | claude-sonnet-4-5 or claude-opus-4 | AI copilot backbone | Already integrated in scaffold; claude-sonnet-4-5 is the right model for this use case — longer context window handles large .SRC files, strong code comprehension for UPG format |

**Note on AI model version:** The scaffold pins `claude-sonnet-4-20250514`. As of August 2025 training cutoff, this is current. Verify against https://docs.anthropic.com/en/docs/about-claude/models at project start — model IDs change frequently. Always use the latest Sonnet or Opus model in the `claude-sonnet-4-*` family for this workload.

---

### Supporting Libraries — Frontend (Next.js)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Monaco Editor (`@monaco-editor/react`) | 4.x | Code editor for viewing/editing UPG post processor files | All post processor viewing screens; provides syntax highlighting, line numbers, diff view — the core UI component for this product |
| TanStack Query (`@tanstack/react-query`) | 5.x | Server state management | All API data fetching; handles caching, background refetch, optimistic updates; eliminates manual loading/error state boilerplate |
| Zustand | 4.x | Client state management | UI state only (selected post, panel open/closed, diff comparison targets); intentionally lightweight — server state lives in TanStack Query |
| Tailwind CSS | 4.x | Styling | Rapid UI iteration during feasibility phase; avoids CSS maintenance overhead; dark mode critical for code editor feel |
| shadcn/ui | latest | UI component library | Built on Radix UI primitives + Tailwind; provides accessible dialogs, dropdowns, tabs without fighting with Monaco's z-index; install components individually, not as package |
| Zod | 3.x | Runtime schema validation | Validate API responses on the frontend; share schema definitions between frontend validation and backend Pydantic models (manual sync, not auto-gen) |
| `@anthropic-ai/sdk` | 0.30+ | Streaming AI responses | If streaming Claude responses directly to browser via Next.js API route; uses `ReadableStream` for token-by-token display in the copilot chat UI |

---

### Supporting Libraries — Backend (FastAPI/Python)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| SQLAlchemy | 2.x async | ORM + query builder | Already in scaffold; use async session pattern throughout; do NOT use sync SQLAlchemy anywhere |
| Alembic | 1.13+ | Database migrations | Already in scaffold; manages schema evolution as parsing models mature; critical for pgvector column additions |
| asyncpg | 0.29+ | PostgreSQL async driver | Required for SQLAlchemy async with PostgreSQL (replaces aiosqlite); fastest Python PostgreSQL driver; needed once SQLite is replaced |
| pgvector Python | 0.3+ | pgvector ORM integration | Exposes `Vector` column type for SQLAlchemy; enables storing and querying embeddings in Postgres |
| redis-py (async) | 5.x | Redis client | Use `redis.asyncio` interface; caching parsed post results, rate limiting Claude API calls, Celery broker |
| Celery | 5.x | Background task queue | Long-running parse jobs (large .SRC files can be 300KB+); embedding generation after upload; do NOT block FastAPI request handlers with these |
| boto3 / aiobotocore | 1.35+ / 2.x | S3/MinIO file storage | Store raw post processor file packages; use aiobotocore for async; boto3 for sync admin scripts |
| python-multipart | 0.0.9+ | File upload handling | Already in scaffold; required for FastAPI UploadFile; keep as-is |
| anthropic | 0.40+ | Claude API client | Already in scaffold; use `AsyncAnthropic` throughout; streaming responses available via `client.messages.stream()` |
| pydantic-settings | 2.x | Environment config | Already in scaffold; manages all config from `.env`; add pgvector URL, Redis URL, MinIO credentials here |
| Ruff | 0.6+ | Linting + formatting | Already in pyproject.toml; replaces black + isort + flake8; keep as-is |
| mypy | 1.11+ | Type checking | Already in pyproject.toml with `strict = true`; enforce this — the domain has complex nested types |
| pytest-asyncio | 0.24+ | Async test runner | Already in scaffold; all service and parsing tests are async |

---

### Supporting Libraries — Infrastructure / DevOps

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Docker Compose | v2 (plugin) | Local multi-service orchestration | Running postgres, redis, minio alongside the API in dev; the existing `docker-compose.yml` only has the API — expand it |
| pgAdmin or TablePlus | latest | Database inspection | Dev-time only; inspect pgvector embeddings, verify schema migrations |
| MinIO Console | bundled | Object storage browser | Dev-time only; verify file uploads, inspect stored post packages |

---

## Installation

### Frontend (Next.js App)

```bash
# Bootstrap Next.js 15 with TypeScript and Tailwind (from project root)
npx create-next-app@latest frontend --typescript --tailwind --app --src-dir --import-alias "@/*"

# Monaco Editor
npm install @monaco-editor/react

# Data fetching + state
npm install @tanstack/react-query zustand

# Validation
npm install zod

# shadcn/ui (CLI-based, install components individually)
npx shadcn@latest init
npx shadcn@latest add button dialog tabs card badge

# Anthropic streaming (if streaming copilot via BFF route)
npm install @anthropic-ai/sdk

# Dev
npm install -D @types/node
```

### Backend (Python — additions to existing scaffold)

```bash
# Replace aiosqlite with asyncpg for PostgreSQL
pip install asyncpg

# pgvector integration
pip install pgvector

# Redis async
pip install "redis[asyncio]>=5.0"

# Background tasks
pip install "celery[redis]>=5.0"

# S3/MinIO async
pip install aiobotocore

# Update pyproject.toml dependencies list with above
```

### Expanded `docker-compose.yml` for dev

```yaml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file: .env
    volumes:
      - ./app:/app/app
    depends_on:
      - postgres
      - redis
      - minio
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: veripost
      POSTGRES_PASSWORD: veripost
      POSTGRES_DB: veripost
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: veripost
      MINIO_ROOT_PASSWORD: veripost123
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data

volumes:
  postgres_data:
  minio_data:
```

---

## Alternatives Considered

| Category | Recommended | Alternative | When Alternative Is Better |
|----------|-------------|-------------|---------------------------|
| Frontend framework | Next.js 15 App Router | Vite + React SPA | If you need zero server-side rendering; SPA is simpler but loses streaming RSC for AI responses |
| Code editor | Monaco Editor | CodeMirror 6 | CodeMirror is lighter and more extensible; Monaco is the right choice here because it has built-in diff viewer needed for post comparison feature |
| Vector database | pgvector (in Postgres) | Qdrant, Weaviate, Pinecone | Separate vector DBs make sense at 10M+ vectors; for a corpus of hundreds to low thousands of posts, pgvector eliminates an entire infrastructure dependency |
| Background jobs | Celery | ARQ (asyncio native) | ARQ is architecturally cleaner for async Python; Celery has vastly more production documentation and operational tooling — safer choice for a team not running Python background jobs day-to-day |
| File storage | MinIO (dev) / S3 (prod) | Filesystem on disk | Filesystem works for solo dev but breaks in containerized/multi-instance deployments; S3 API from day one avoids a painful migration later |
| CSS framework | Tailwind CSS 4 | CSS Modules | CSS Modules give more control; Tailwind 4 is appropriate for rapid iteration during feasibility phase where UI is exploratory |
| ORM | SQLAlchemy 2 async | Tortoise ORM, SQLModel | SQLModel (FastAPI author's project) is tempting but thinner community and less battle-tested for complex queries; SQLAlchemy 2 async is industry standard |
| AI streaming | `@anthropic-ai/sdk` (streaming) | Poll for completion | Streaming is strictly better UX for the copilot — explaining 300KB post processors takes time; polling causes long perceived wait |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| SQLite in production | Cannot support pgvector; no concurrent writes; the scaffold uses it for dev only — acceptable — but never for production or even integration testing | PostgreSQL 16 + pgvector |
| Synchronous SQLAlchemy | Blocks FastAPI's event loop; undermines the entire async architecture | SQLAlchemy 2 async with `AsyncSession` throughout |
| LangChain / LlamaIndex | Heavyweight abstraction over Anthropic SDK; adds dependency complexity without value for a focused use case (explain code, compare posts); the copilot calls are simple enough to own directly | `anthropic` Python SDK with hand-written prompts |
| Prisma (for Python) | Not production-ready for Python; the JavaScript Prisma is unrelated | SQLAlchemy 2 + Alembic |
| FastAPI `BackgroundTasks` for heavy parsing | FastAPI BackgroundTasks run in the same process as the web server — blocking during large .SRC parsing will starve request handlers | Celery with Redis broker for any job over 1-2 seconds |
| `npm run dev` with `python` in the same terminal | Running both servers manually for every session is friction that kills iteration speed | Docker Compose for all backend services; `npm run dev` for frontend only |
| Custom vector storage in application code | Rolling your own vector similarity in Python is slow and won't scale | pgvector with `<->` distance operator |
| Direct Claude API calls from the browser | Exposes API key in client code; enables unlimited usage | Route all Claude calls through the FastAPI backend |
| Monaco Editor without Web Workers | Monaco is CPU-heavy on large files; without worker configuration it freezes the UI on .SRC files (300KB+) | Configure `@monaco-editor/react` with `MonacoEnvironment.getWorkerUrl` |

---

## Stack Patterns by Variant

**If deploying to production AWS:**
- Replace MinIO with AWS S3 (zero code change — same boto3 API, only env vars differ)
- Replace local PostgreSQL with RDS PostgreSQL 16 with pgvector extension enabled
- Replace local Redis with ElastiCache Redis 7
- Keep FastAPI on ECS Fargate or a single EC2 instance for this scale

**If staying fully on-prem / self-hosted:**
- Keep MinIO — it's production-grade for this file volume
- Consider managed Postgres (e.g., Supabase self-hosted) for pgvector extension management

**If Next.js feels like overkill during feasibility phase:**
- Use Next.js App Router with zero server components initially — just use it as a React SPA wrapper with `use client` everywhere
- Add RSC/streaming incrementally as the copilot UI matures
- This avoids the "hybrid app" mental model during early iteration while keeping the option open

**If the parser produces AST-level data (not just section/variable extraction):**
- Add a `parsed_ast: JSONB` column to the post_processors table in Postgres
- Store the full parsed tree for re-querying without re-parsing
- pgvector embeddings live alongside the JSONB column in the same row

---

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| `pgvector/pgvector:pg16` Docker image | pgvector Python 0.3+ | Use the official pgvector Docker image — it bundles the extension; `CREATE EXTENSION vector;` still required in first migration |
| FastAPI 0.115+ | Pydantic v2 only | Pydantic v1 compatibility shim removed in FastAPI 0.100+; scaffold already uses Pydantic v2 — do not downgrade |
| SQLAlchemy 2.x async | asyncpg 0.29+ | asyncpg is the required driver for async Postgres; aiosqlite only works with SQLite |
| Next.js 15 | React 19 | Next.js 15 requires React 19; do not mix React 18 with Next.js 15 — peer dependency conflicts |
| `@monaco-editor/react` 4.x | React 18 and 19 | Verify React 19 compatibility at install time; Monaco's react wrapper lags behind Monaco core releases |
| Tailwind CSS 4.x | PostCSS 8.x | Tailwind 4 changes the config format significantly from v3; do not follow v3 tutorials |
| Celery 5.x | Redis 7.x | Celery 5 supports Redis 7 broker; use `celery[redis]` extra |
| anthropic Python 0.40+ | asyncio | Async client is `AsyncAnthropic`; always instantiate inside an async context, not at module level |

---

## Critical Migration: Scaffold → Target Stack

The existing scaffold uses:
- SQLite (`sqlite+aiosqlite://`) → must become `postgresql+asyncpg://`
- In-memory dict store (`_store: dict`) → must become SQLAlchemy ORM models with Postgres tables
- No file storage → add MinIO for raw post file packages
- No Redis → add Redis for caching and background jobs
- No pgvector → add as Alembic migration after Postgres is running

Migration order matters:
1. Stand up Postgres + pgvector in Docker Compose first
2. Create first Alembic migration with `post_processors` table and `CREATE EXTENSION vector`
3. Remove `aiosqlite` from dependencies, add `asyncpg`
4. Replace `_store` dict in `post_service.py` with SQLAlchemy async CRUD
5. Add MinIO storage for file upload in `posts.py` route
6. Add Redis after storage is working (caching is an optimization, not a prerequisite)
7. Add Celery after Redis (for large file parse jobs in background)

---

## Confidence Assessment by Component

| Component | Confidence | Basis | Validation Needed |
|-----------|------------|-------|-------------------|
| FastAPI 0.115+ | HIGH | Pinned in scaffold pyproject.toml; FastAPI is stable | None |
| Pydantic v2 | HIGH | Pinned in scaffold; currently the standard | None |
| PostgreSQL 16 + pgvector | HIGH | pgvector is the standard embedded vector solution for Postgres-based stacks | Verify `pgvector/pgvector:pg16` Docker image tag is current |
| Next.js 15 / React 19 | MEDIUM | Training cutoff August 2025; Next.js 15 was released late 2024 and stable | Verify latest patch version at `npm view next version` |
| `@monaco-editor/react` 4.x | MEDIUM | Stable package; version 4.x current as of training | Verify React 19 peer dependency compatibility |
| Tailwind CSS 4.x | MEDIUM | v4 released early 2025; is current stable | Check if shadcn/ui has updated for Tailwind v4 — this integration is known to lag |
| shadcn/ui | MEDIUM | CLI-based install is stable pattern; component versions vary | Run `npx shadcn@latest` to get current components; do not pin shadcn as a package |
| Anthropic Python SDK 0.40+ | MEDIUM | Training cutoff; `claude-sonnet-4-20250514` is the model in scaffold | Verify latest model ID at https://docs.anthropic.com/en/docs/about-claude/models before first AI integration |
| Claude model ID | LOW | Model IDs change; `claude-sonnet-4-20250514` will be outdated | MUST verify at project start — wrong model ID causes silent 404 from API |
| Celery 5.x + Redis broker | MEDIUM | Standard pattern, well-documented | Verify Celery 5.x supports Python 3.12 if upgrading Python later |
| aiobotocore for MinIO | MEDIUM | Standard S3-compat pattern | Test MinIO endpoint config with aiobotocore early — endpoint URL handling has quirks |

---

## Sources

- Existing scaffold: `c:/VeriPost/pyproject.toml` — confirms FastAPI 0.115+, Pydantic v2, Python 3.11, anthropic 0.40+, SQLAlchemy 2.x, Alembic 1.13+ (HIGH confidence — ground truth)
- Existing scaffold: `c:/VeriPost/app/config.py` — confirms `claude-sonnet-4-20250514` model target (HIGH confidence for scaffold intent; LOW confidence the model ID remains valid)
- Project constraints: `c:/VeriPost/.planning/PROJECT.md` — confirms full target stack: Next.js/React/TS, FastAPI, PostgreSQL+pgvector, S3/MinIO, Redis, Claude API (project authority)
- Architecture doc: `c:/VeriPost/docs/architecture.md` — confirms async-first design, Alembic migrations, SQLite→Postgres swap pattern
- Training data (August 2025): Next.js 15, React 19, Tailwind 4, pgvector 0.7, redis-py 5, Celery 5 (MEDIUM confidence — verify versions at project start)

---

## Open Questions (Verify at Project Start)

1. **Claude model ID**: What is the current `claude-sonnet-4-*` model identifier? Check https://docs.anthropic.com/en/docs/about-claude/models. The scaffold hardcodes `claude-sonnet-4-20250514` which is likely stale.

2. **Monaco + React 19**: Does `@monaco-editor/react@4.x` declare React 19 as a peer dependency? Test with `npm install --legacy-peer-deps` if not — Monaco's react wrapper historically lags React releases.

3. **shadcn/ui + Tailwind 4**: shadcn/ui v0 was built for Tailwind v3. Confirm the current shadcn/ui supports Tailwind v4 config format before scaffolding the frontend.

4. **pgvector embedding dimensions**: What embedding model will generate the vectors? OpenAI ada-002 is 1536d; Claude does not expose embeddings directly. Consider `text-embedding-3-small` (OpenAI, 1536d) or `voyage-3` (Anthropic partner, various dimensions). This choice must be made before the first Alembic migration that adds the `embedding vector(N)` column.

5. **MinIO TLS in dev**: MinIO default dev config uses HTTP. If the FastAPI backend runs in Docker and accesses MinIO via service name, confirm no TLS negotiation issues with aiobotocore's default HTTPS behavior.

---

*Stack research for: VeriPost — CNC Post Processor Management Platform*
*Researched: 2026-02-18*
