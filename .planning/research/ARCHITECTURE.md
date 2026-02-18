# Architecture Research

**Domain:** CNC post processor management platform (VeriPost)
**Researched:** 2026-02-18
**Confidence:** HIGH — based on direct codebase inspection plus established patterns for the full target stack

---

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND LAYER                               │
│  Next.js / React / TypeScript                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  Post Browser│  │  Code Viewer │  │  AI Copilot  │              │
│  │  (list/search│  │  (Monaco Ed) │  │  Chat Panel  │              │
│  │   + filters) │  │  read-only   │  │              │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                 │                  │                       │
└─────────┼─────────────────┼──────────────────┼───────────────────────┘
          │     HTTP/REST   │                  │
┌─────────┼─────────────────┼──────────────────┼───────────────────────┐
│         │    API GATEWAY LAYER (FastAPI)      │                       │
│  ┌──────▼───────┐  ┌──────▼───────┐  ┌──────▼───────┐              │
│  │  /posts      │  │  /parsing    │  │  /copilot    │              │
│  │  /packages   │  │  /search     │  │  /diff       │              │
│  │  /machines   │  │  /versions   │  │              │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                 │                  │                       │
├─────────┼─────────────────┼──────────────────┼───────────────────────┤
│                      SERVICE LAYER                                    │
│  ┌──────▼───────┐  ┌──────▼───────┐  ┌──────▼───────┐              │
│  │PostPackage   │  │  Search      │  │  AI Copilot  │              │
│  │  Service     │  │  Service     │  │  Service     │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                 │                  │                       │
├─────────┼─────────────────┼──────────────────┼───────────────────────┤
│                      CORE DOMAIN LAYER                                │
│  ┌──────▼───────┐  ┌──────▼───────┐  ┌──────▼───────┐              │
│  │  UPG Parser  │  │   Machine    │  │ Version      │              │
│  │  (camworks   │  │   Registry   │  │ Manager      │              │
│  │   .SRC/.LIB) │  │              │  │ (git-backed) │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                 │                  │                       │
├─────────┼─────────────────┼──────────────────┼───────────────────────┤
│                   BACKGROUND WORKER LAYER (Redis + RQ/Celery)         │
│  ┌──────▼───────────────────────────────────────────────────┐       │
│  │  Ingestion Pipeline: receive → extract → parse → embed   │       │
│  └──────────────────────────────────────────────────────────┘       │
├──────────────────────────────────────────────────────────────────────┤
│                      PERSISTENCE LAYER                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ PostgreSQL   │  │  S3 / MinIO  │  │    Redis     │              │
│  │ + pgvector   │  │  (raw files) │  │  (cache +    │              │
│  │ (structured) │  │              │  │   queues)    │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└──────────────────────────────────────────────────────────────────────┘
                              │
                   ┌──────────▼──────────┐
                   │  External Services  │
                   │  Anthropic Claude   │
                   │  API               │
                   └─────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Communicates With |
|-----------|----------------|-------------------|
| Next.js UI | Post browser, Monaco code viewer, AI copilot chat, version diff view | FastAPI REST API only |
| FastAPI Routes | Request validation, auth (future), response shaping | Service layer only — no direct DB |
| PostPackage Service | Ingest packages, coordinate storage, trigger parsing jobs | Parser engine, File Store, DB, Redis queue |
| Search Service | Hybrid FTS + semantic search, result ranking | PostgreSQL + pgvector |
| AI Copilot Service | Compose context from parsed data, call Claude API, stream responses | DB (for context), Anthropic API |
| UPG Parser Engine | Parse .SRC/.LIB/.ATR/.KIN files into structured data model, extract sections/variables/subroutines | Called by ingestion worker; writes to DB |
| Machine Registry | Store machine metadata (controller, axes, kinematics), link to post packages | PostgreSQL, queried by UI and copilot |
| Version Manager | Git-backed history of file revisions, diff generation | Git bare repo on filesystem or S3 |
| Ingestion Worker | Async background processing: receive → validate → store raw → parse → embed | Redis (queue), S3 (file storage), PostgreSQL (structured output) |
| PostgreSQL + pgvector | Structured post metadata, parsed sections, embeddings for semantic search | Service layer |
| S3 / MinIO | Raw file storage for post packages (original + all versions) | PostPackage Service, Ingestion Worker |
| Redis | Job queue for ingestion pipeline, response caching | Worker, PostPackage Service |

---

## Recommended Project Structure

This is a full-stack project. Two repos or a monorepo with two top-level roots.

```
veripost/
├── backend/                        # Python / FastAPI service
│   ├── app/
│   │   ├── main.py                 # FastAPI app factory
│   │   ├── config.py               # Pydantic Settings from env
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── packages.py     # Upload, list, get post packages
│   │   │       ├── posts.py        # Individual post file operations
│   │   │       ├── search.py       # FTS + semantic search endpoints
│   │   │       ├── copilot.py      # AI copilot chat endpoint
│   │   │       ├── machines.py     # Machine registry CRUD
│   │   │       ├── versions.py     # Version history + diff
│   │   │       └── health.py       # Health check
│   │   ├── core/
│   │   │   ├── parsing/
│   │   │   │   ├── base.py         # BaseParser ABC
│   │   │   │   ├── registry.py     # Parser detection + dispatch
│   │   │   │   └── camworks/
│   │   │   │       ├── src.py      # .SRC file parser
│   │   │   │       ├── lib.py      # .LIB file parser
│   │   │   │       ├── atr.py      # .ATR variable master parser
│   │   │   │       ├── kin.py      # .KIN kinematics parser
│   │   │   │       └── package.py  # Package-level coordinator
│   │   │   ├── models/
│   │   │   │   ├── package.py      # PostPackage domain model
│   │   │   │   ├── post_file.py    # Individual file model
│   │   │   │   ├── section.py      # Section/block model
│   │   │   │   ├── variable.py     # Variable definition model
│   │   │   │   └── machine.py      # Machine registry model
│   │   │   ├── ai/
│   │   │   │   ├── copilot.py      # Claude API wrapper
│   │   │   │   ├── context.py      # Context builder (selects relevant sections)
│   │   │   │   ├── embedder.py     # Text → embedding via Claude or OpenAI
│   │   │   │   └── prompts.py      # Domain-specific system prompts
│   │   │   └── versioning/
│   │   │       ├── git_store.py    # Git bare repo wrapper (dulwich or subprocess)
│   │   │       └── diff.py         # Structured diff generation
│   │   ├── services/
│   │   │   ├── package_service.py  # Package ingestion orchestration
│   │   │   ├── search_service.py   # Hybrid search coordination
│   │   │   ├── copilot_service.py  # AI session management
│   │   │   └── machine_service.py  # Machine registry operations
│   │   ├── workers/
│   │   │   ├── tasks.py            # RQ task definitions
│   │   │   └── ingestion.py        # Multi-step ingestion pipeline
│   │   └── db/
│   │       ├── database.py         # SQLAlchemy async engine
│   │       ├── models/             # SQLAlchemy ORM models
│   │       └── migrations/         # Alembic migration scripts
│   ├── tests/
│   └── pyproject.toml
│
├── frontend/                       # Next.js / React / TypeScript
│   ├── app/                        # Next.js App Router
│   │   ├── layout.tsx
│   │   ├── page.tsx                # Post browser (list + search)
│   │   ├── packages/
│   │   │   ├── [id]/
│   │   │   │   ├── page.tsx        # Package detail view
│   │   │   │   ├── files/[fileId]/ # Individual file viewer (Monaco)
│   │   │   │   └── versions/       # Version history
│   │   └── machines/               # Machine registry UI
│   ├── components/
│   │   ├── PostBrowser/            # Search + filter + list
│   │   ├── CodeViewer/             # Monaco Editor wrapper (read-only + diff)
│   │   ├── CopilotPanel/           # Chat UI + context selector
│   │   ├── MachineCard/            # Machine metadata display
│   │   └── VersionTimeline/        # Git history visualization
│   ├── lib/
│   │   ├── api.ts                  # API client (fetch wrappers)
│   │   └── types.ts                # Shared TypeScript types
│   └── package.json
│
├── docker-compose.yml              # Full stack: api + worker + postgres + redis + minio
├── .env.example
└── .planning/
```

### Structure Rationale

- **`core/parsing/camworks/`:** Split by file type (.SRC, .LIB, .ATR, .KIN) because each has a distinct grammar. A monolithic UPG parser becomes unmanageable; file-type parsers compose via `package.py`.
- **`core/models/`:** Domain models (Pydantic) are separate from `db/models/` (SQLAlchemy ORM). This is the Clean Architecture boundary — service layer speaks domain models, ORM layer translates to SQL. Never let SQLAlchemy bleed into parsers or copilot.
- **`workers/`:** Isolated from API routes. The API enqueues jobs; workers consume. This prevents HTTP request timeouts on large file parsing (294KB .SRC files take real time to parse and embed).
- **`core/ai/context.py`:** Context building is the hardest part of AI integration. Isolating it allows independent testing and iteration without touching the Claude API wrapper.
- **`services/`:** Services own business logic and cross-cutting concerns. Routes own HTTP translation. Never put business logic in routes.

---

## Architectural Patterns

### Pattern 1: Ingestion Pipeline as Background Job

**What:** File upload returns immediately with a job ID. Actual parse + embed happens asynchronously in a Redis-backed worker. Status is polled or pushed via SSE.

**When to use:** Always — .SRC files are 294KB of complex UPG syntax. Parsing + embedding in a synchronous HTTP handler will timeout and creates poor UX.

**Trade-offs:** Adds Redis dependency; requires job status tracking in DB; upload UX needs a "processing" state in the UI. Worth it — synchronous file processing is the top cause of timeout-related rewrites in document-management platforms.

**Example:**
```python
# Route: returns immediately
@router.post("/packages/upload")
async def upload_package(files: list[UploadFile], ...):
    package_id = await package_service.create_pending(files)
    job = queue.enqueue(tasks.ingest_package, package_id)
    return {"package_id": package_id, "job_id": job.id, "status": "processing"}

# Worker: runs async in background
def ingest_package(package_id: str):
    files = storage.get_raw_files(package_id)
    for f in files:
        parsed = parser_registry.parse(f)
        db.save_parsed(parsed)
        embeddings = embedder.embed_sections(parsed.sections)
        db.save_embeddings(package_id, embeddings)
    db.mark_complete(package_id)
```

### Pattern 2: Package-Level Data Model (not file-level)

**What:** The top-level entity is a `PostPackage` (7-12 files for one machine), not individual files. Files are children of a package. UI, search, and versioning all operate at the package level.

**When to use:** Always — this matches how CAM engineers think. They care about "the Haas VF-4 mill post" (the package), not "file HRS_HAAS_VF4.SRC" in isolation.

**Trade-offs:** Slightly more complex data model upfront, but prevents a painful refactor later when the UI needs to show "which machine does this file belong to?"

**Example:**
```python
class PostPackage(BaseModel):
    id: str
    machine_id: str              # FK → MachineRegistry
    name: str                    # "Ducommun HAAS VF-4 Mill"
    platform: str                # "camworks"
    files: list[PostFile]        # .SRC, .LIB, .ATR, .KIN, .PINF, .LNG
    version: str                 # semver or git SHA
    status: PackageStatus        # pending | parsing | ready | error
    tags: list[str]
    created_at: datetime
    updated_at: datetime
```

### Pattern 3: Hybrid Search (FTS + Semantic, Not Either/Or)

**What:** Run both PostgreSQL full-text search (tsvector on variable names, section names, raw content) and pgvector semantic search (cosine similarity on section embeddings) in parallel, then merge-rank results with a weighted score.

**When to use:** Always for the main search bar — FTS catches exact variable names like `COOLANT_ON`; semantic search catches intent like "how do I output M8 for coolant." Both are needed.

**Trade-offs:** Two query paths to maintain; embedding generation adds ingestion latency; pgvector index needs tuning. The alternative (FTS only) fails for AI-assisted search; semantic only fails for variable lookup.

**Example:**
```python
async def hybrid_search(query: str, limit: int = 20) -> list[SearchResult]:
    embedding = await embedder.embed(query)

    fts_results = await db.execute(
        "SELECT id, ts_rank(...) AS score FROM sections WHERE to_tsvector(...) @@ plainto_tsquery(:q)",
        {"q": query}
    )
    semantic_results = await db.execute(
        "SELECT id, 1 - (embedding <=> :emb) AS score FROM sections ORDER BY embedding <=> :emb LIMIT 50",
        {"emb": embedding}
    )

    return merge_rank(fts_results, semantic_results, fts_weight=0.4, semantic_weight=0.6)
```

### Pattern 4: AI Context Assembly (Not Raw File Injection)

**What:** Never send raw .SRC file content directly to Claude. Instead, assemble a structured context: relevant sections (selected by the user's question or clicked code), variable definitions from .ATR, machine metadata from the registry. Token budget enforced explicitly.

**When to use:** All copilot calls. The existing `copilot.py` does `context[:8000]` — this is wrong for production. Smart context selection is what makes the AI useful.

**Trade-offs:** Requires understanding of what context matters (domain knowledge needed up front); slower than naively truncating. But a copilot that answers "what does COOLANT_ON do?" with the wrong section in context will give wrong answers, destroying user trust.

**Example:**
```python
class ContextBuilder:
    def build(self, question: str, package: PostPackage, selected_section: str | None) -> str:
        context_parts = []

        # Always include machine header
        context_parts.append(f"Machine: {package.machine.name}, Controller: {package.machine.controller}")

        # Include selected section if user clicked a block
        if selected_section:
            context_parts.append(f"Selected section:\n{selected_section}")

        # Include semantically relevant sections (top-3 by embedding similarity)
        relevant = self.search_sections(question, package, limit=3)
        for section in relevant:
            context_parts.append(f"[{section.name}]\n{section.content}")

        # Append relevant ATR variable definitions
        mentioned_vars = extract_variable_references(selected_section or question)
        defs = package.get_variable_definitions(mentioned_vars)
        if defs:
            context_parts.append(f"Variable definitions:\n{defs}")

        return "\n\n---\n\n".join(context_parts)[:12000]  # explicit token budget
```

### Pattern 5: Git-Backed Versioning via Bare Repository

**What:** Each post package gets a dedicated Git bare repository stored on the filesystem (or in S3 via git-remote-s3). Version history, diffs, and rollback use standard Git operations via Python's `dulwich` or subprocess. The `versions` table in PostgreSQL indexes commits but the truth is in Git.

**When to use:** For all version-tracked packages. Do not implement a custom "versions" table with full content snapshots — Git already does this correctly and tools (diff, blame, log) come free.

**Trade-offs:** Requires understanding of Git plumbing vs porcelain APIs; `dulwich` (pure Python Git) is less battle-tested than subprocess + system Git. Use system Git via subprocess, not dulwich, to avoid edge cases.

**Example:**
```python
class GitVersionStore:
    def commit_package_version(self, package_id: str, files: dict[str, bytes], message: str) -> str:
        repo_path = self.get_repo_path(package_id)
        with git_worktree(repo_path) as worktree:
            for filename, content in files.items():
                (worktree / filename).write_bytes(content)
            subprocess.run(["git", "add", "-A"], cwd=worktree, check=True)
            result = subprocess.run(["git", "commit", "-m", message], cwd=worktree, capture_output=True)
        return result.stdout.decode().split()[1]  # SHA

    def get_diff(self, package_id: str, sha_a: str, sha_b: str) -> str:
        repo_path = self.get_repo_path(package_id)
        result = subprocess.run(
            ["git", "diff", sha_a, sha_b],
            cwd=repo_path, capture_output=True
        )
        return result.stdout.decode()
```

---

## Data Flow

### File Ingestion Flow

```
CAM Engineer uploads ZIP / folder of post files
    ↓
POST /api/v1/packages/upload (FastAPI)
    ↓
PackageService.create_pending()
    → Saves raw files to S3/MinIO (one bucket path per package)
    → Creates PostPackage DB record with status=pending
    → Enqueues ingestion job via Redis
    ↓ (returns immediately with package_id + job_id)

[Background Worker picks up job]
    ↓
ingestion.ingest_package(package_id)
    → Loads raw files from S3
    → Detects file types (.SRC, .LIB, .ATR, .KIN, etc.)
    → Dispatches to file-type-specific parsers
    → Saves ParsedPost records to PostgreSQL
    → Generates section embeddings via Claude/embeddings API
    → Saves embeddings to pgvector columns
    → Creates initial Git commit in package's bare repo
    → Updates PostPackage.status = ready
    ↓
UI polls /api/v1/packages/{id}/status
    → Receives status=ready
    → Loads package detail view
```

### AI Copilot Flow

```
Engineer selects a section in Monaco code viewer
    ↓ (section ID sent with question)
POST /api/v1/copilot/ask
    { package_id, question, selected_section_id }
    ↓
CopilotService.ask()
    → Loads package metadata from DB
    → Loads selected section content from DB
    → Calls ContextBuilder.build(question, package, selected_section)
        → FTS + semantic search for relevant sections
        → Fetches ATR variable definitions for referenced vars
        → Assembles context string within token budget
    → Calls Anthropic Claude API (streaming)
    ↓
Server-Sent Events stream to frontend
    ↓
CopilotPanel renders response with section references
```

### Search Flow

```
Engineer types query in search bar
    ↓
GET /api/v1/search?q=coolant+M8&type=section
    ↓
SearchService.search(query)
    → Parallel:
        → PostgreSQL FTS: tsvector search on content + variable names
        → pgvector: cosine similarity on query embedding
    → Merge-rank results (weighted score)
    → Return top 20 ranked SearchResult objects
        { package_id, file_id, section_name, snippet, score, match_type }
    ↓
UI renders results grouped by package
    → Click result → opens Monaco viewer scrolled to section
```

### Version History Flow

```
Engineer requests diff between two versions
    ↓
GET /api/v1/packages/{id}/versions/{sha_a}/diff/{sha_b}
    ↓
VersionManager.get_diff(package_id, sha_a, sha_b)
    → Runs git diff sha_a sha_b in package's bare repo
    → Parses unified diff into structured DiffResult
        { file_path, hunks: [{ old_line, new_line, content }] }
    ↓
Monaco Editor diff view renders side-by-side comparison
```

---

## Build Order

The components have hard dependencies that dictate build sequence. Build in this order:

```
Phase 1: Core Infrastructure
    PostgreSQL schema + Alembic migrations
    S3/MinIO integration + file storage
    Redis + worker process setup (RQ or Celery)
    → All later phases depend on these

Phase 2: UPG Parser Engine
    .SRC section/block parser (structure first, deep semantics later)
    .LIB modular library parser
    .ATR variable definition parser (600+ vars with types)
    .KIN kinematics parser
    Package coordinator
    → Required by: ingestion pipeline, AI context builder, search

Phase 3: Ingestion Pipeline
    File upload → S3 storage
    Background job dispatch (Redis queue)
    Parser dispatch + PostgreSQL write
    Package status tracking
    → Required by: UI, search, AI copilot

Phase 4: Machine Registry
    Machine DB schema + CRUD API
    Machine ↔ Package linking
    → Required by: AI context (provides machine metadata)

Phase 5: Search
    PostgreSQL FTS (tsvector on sections + variable names)
    pgvector setup + section embedding generation
    Hybrid search endpoint + ranking
    → Required by: AI context builder (relevant section lookup)

Phase 6: AI Copilot
    Context builder (uses parser output + machine registry + search)
    Claude API integration (streaming)
    Prompt tuning for UPG domain
    → Depends on: phases 2-5 being functional

Phase 7: Version Management
    Git bare repo per package
    Commit on ingest + on explicit save
    Diff API endpoint
    → Can be built in parallel with Phase 6

Phase 8: Frontend UI
    Next.js app with API client
    Post browser (list + FTS search)
    Monaco code viewer (read-only, UPG syntax)
    Copilot chat panel
    Version diff view (Monaco diff)
    → Depends on: API endpoints from phases 3-7
```

**Critical path:** Parser (Phase 2) → Ingestion (Phase 3) → Search (Phase 5) → Copilot (Phase 6). Everything else (machine registry, versioning, UI) can be sequenced around this path.

---

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Anthropic Claude API | HTTP client (async, streaming) | Use `anthropic` Python SDK, not raw HTTP. SSE streaming to frontend via FastAPI StreamingResponse. Model: `claude-sonnet-4-20250514` already configured. |
| S3 / MinIO | `boto3` / `aiobotocore` | Use presigned URLs for large file downloads to UI. Never proxy raw file bytes through FastAPI — let S3 serve them directly. |
| Redis | `rq` (Redis Queue) or `celery[redis]` — prefer RQ for simplicity at this scale | Worker process runs separately from API (`rq worker`). |
| PostgreSQL + pgvector | SQLAlchemy async + `pgvector` Python extension | Use `asyncpg` driver. pgvector requires `CREATE EXTENSION vector` in migration. |

### Internal Component Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| API routes ↔ Services | Direct Python function calls (same process) | Services return domain models, not ORM objects |
| Services ↔ Database | SQLAlchemy async ORM | ORM models live in `db/models/`, domain models in `core/models/`. Map at service boundary. |
| API ↔ Worker | Redis job queue | API enqueues, worker dequeues. Job ID returned to client for polling. |
| Parser ↔ Service | Domain model return (`ParsedPost`, `ParsedPackage`) | Parsers are pure functions — no DB access. Services save results. |
| Copilot ↔ Search | Direct Python function call (same process) | Context builder calls SearchService to find relevant sections. |
| Frontend ↔ Backend | HTTP REST + SSE (for copilot streaming) | No WebSockets needed — SSE is sufficient for streaming copilot responses. |
| Version Manager ↔ Git | subprocess + system Git | Do not use `dulwich` — system Git is more reliable for complex operations. Store bare repos in a predictable path: `{GIT_STORE_ROOT}/{package_id}.git` |

---

## Anti-Patterns

### Anti-Pattern 1: Storing Raw File Bytes in PostgreSQL

**What people do:** Save .SRC file content as a `TEXT` column in the posts table.

**Why it's wrong:** 294KB per file × thousands of packages fills PostgreSQL quickly, makes backups slow, and bypasses streaming. PostgreSQL is not a file store.

**Do this instead:** Store raw bytes in S3/MinIO. PostgreSQL holds metadata, parsed structure, and embeddings only. S3 path is a column (`s3_key TEXT NOT NULL`).

### Anti-Pattern 2: Parsing in the HTTP Request Handler

**What people do:** Upload endpoint calls the parser synchronously and returns parsed results in the HTTP response.

**Why it's wrong:** Parsing a 294KB .SRC file + generating embeddings takes 5-30 seconds. HTTP timeouts at 30s by default. Adding 7-12 files per package makes this worse. Users experience failures and retry, causing duplicate processing.

**Do this instead:** Upload stores to S3, enqueues job, returns `202 Accepted` with job ID. Worker parses. UI polls status.

### Anti-Pattern 3: Sending Entire .SRC File Content to Claude

**What people do:** `context = file_content[:8000]` — truncate the file and send as AI context. (The existing `copilot.py` does this.)

**Why it's wrong:** A .SRC file has hundreds of sections. The first 8000 characters are almost never the section the engineer is asking about. Wrong context → wrong answers → engineer stops trusting the copilot.

**Do this instead:** Use `ContextBuilder` with semantic search to select the 3-5 sections most relevant to the question, plus the clicked section if any. Aim for precision, not volume.

### Anti-Pattern 4: One Repository for All Post Files

**What people do:** Put all post packages in a single Git repository for "centralized versioning."

**Why it's wrong:** A monorepo of thousands of post packages creates massive Git history, slow clones, and makes per-package rollback painful. Each package has independent change cadence.

**Do this instead:** One bare Git repository per post package (stored at `{GIT_STORE_ROOT}/{package_id}.git`). PostgreSQL stores the index of packages and their current Git SHA. This is how tools like Gitea and Forgejo manage multi-repo storage.

### Anti-Pattern 5: Implementing Full AST for UPG Before Validating Value

**What people do:** Build a complete grammar/AST parser for UPG before proving the platform is useful.

**Why it's wrong:** UPG is a proprietary format with undocumented edge cases. A full AST takes months and will have regressions on corpus files. Section-level extraction (regex/line-based) is sufficient for AI context and search.

**Do this instead:** Start with section-level structural parsing (detect `[SECTION]` headers and their contents). Move to deeper semantic parsing only after AI copilot usefulness is validated. Invest in AST when specific features demand it (e.g., "find all subroutine calls" or "detect variable cross-references").

---

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0-100 packages | Single Docker Compose stack. SQLite for dev, PostgreSQL for production. One RQ worker process. S3 or MinIO local — either works. |
| 100-10K packages | Add pgvector HNSW index for approximate nearest-neighbor search (exact cosine becomes slow above ~50K vectors). Add Redis caching for frequently accessed package metadata. Consider read replica for PostgreSQL if search queries compete with writes. |
| 10K+ packages | Separate worker fleet from API. Partition pgvector by platform. Consider dedicated embedding service (batch embed on ingest). Git bare repos may need migration to an object-store-backed Git service if filesystem fills. |

### Scaling Priorities

1. **First bottleneck:** pgvector scan performance. Fix with HNSW index (`CREATE INDEX ON sections USING hnsw (embedding vector_cosine_ops)`). This is a one-line migration.
2. **Second bottleneck:** Ingestion queue depth if batch-importing SharePoint corpus. Fix with multiple RQ workers (horizontal scale via Docker replica count).
3. **Third bottleneck:** Claude API rate limits during AI-heavy workflows. Fix with request queuing in CopilotService and exponential backoff.

---

## Sources

- Codebase inspection: `C:/VeriPost/app/**` — existing scaffold, parser structure, AI copilot stub, service layer (HIGH confidence — direct source)
- Project definition: `C:/VeriPost/.planning/PROJECT.md` — requirements, constraints, file format descriptions (HIGH confidence — direct source)
- Architecture note: `C:/VeriPost/docs/architecture.md` — existing design principles (HIGH confidence — direct source)
- FastAPI background tasks and async patterns — training data (MEDIUM confidence, well-established pattern)
- pgvector hybrid search architecture — training data (MEDIUM confidence, well-documented pattern in pgvector docs as of 2025)
- Git bare repository per-project pattern — training data, consistent with Gitea/Forgejo implementation approach (MEDIUM confidence)
- Redis Queue (RQ) vs Celery tradeoff for single-service background jobs — training data (MEDIUM confidence)

---

*Architecture research for: VeriPost — CNC post processor management platform*
*Researched: 2026-02-18*
