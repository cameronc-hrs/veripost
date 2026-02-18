# Project Research Summary

**Project:** VeriPost — CNC Post Processor Management Platform
**Domain:** Specialized engineering document management with AI-assisted code analysis
**Researched:** 2026-02-18
**Confidence:** MEDIUM

## Executive Summary

VeriPost is a web-based repository and AI analysis platform for CAMWorks/SOLIDWORKS CAM post processors — domain-specific programs written in HCL's Universal Post Generator (UPG) scripting language that translate CAM toolpaths into machine-specific G-code. No commercial competitor offers centralized management, version control, or AI analysis for these files; all existing tools (UPG-2, CIMCO Edit, Predator CNC Editor) are Windows desktop applications that treat posts as isolated text files on a file system. The product concept is sound and uncontested, but its entire value proposition rests on a single high-risk dependency: a UPG parser capable of extracting meaningful structure from proprietary, undocumented scripting files. If the parser fails to extract structure from real corpus files, every AI feature collapses with it.

The recommended build approach is a FastAPI (Python) backend with PostgreSQL + pgvector, Redis + Celery for background processing, MinIO for object storage, and a Next.js/React/TypeScript frontend with Monaco Editor. The stack is largely pre-decided in the project constraints and is well-suited to the domain — pgvector enables semantic search over parsed content without a separate vector database, and Monaco provides built-in diff viewing needed for post comparison. The critical architectural insight is that file ingestion must be asynchronous: real UPG post packages (7-12 files, up to 294KB for a single .SRC file) must be parsed and embedded in background workers, not synchronous HTTP handlers. The existing scaffold correctly uses FastAPI but has three known-broken placeholders that must be replaced before any meaningful testing: the in-memory `_store` (no persistence), the 8,000-character AI context truncation (covers only 2.7% of a real file), and the placeholder INI-style UPG parser (fundamentally wrong grammar model).

The top risk is AI confabulation on proprietary UPG constructs — Claude has minimal training data on CAMWorks UPG, so grounding every AI response in specific file text with line citations is mandatory before user-facing deployment. The second risk is building the parser without first collecting and manually annotating a real corpus of 20+ UPG files. Building against a synthetic grammar produces a parser that requires full rewrite when it encounters real files. Both risks have clear mitigations: corpus-first parser development, and a mandatory SME validation gate before the AI copilot reaches engineers.

---

## Key Findings

### Recommended Stack

The stack is pre-decided in PROJECT.md and validated by the research. The backend (FastAPI 0.115+, Python 3.11+, PostgreSQL 16 + pgvector, Redis 7, MinIO, Anthropic Claude API) is the right choice for this workload. The frontend (Next.js 15/React 19/TypeScript 5, Monaco Editor, TanStack Query, Tailwind CSS 4, shadcn/ui) is appropriate for a code-editor-centric UI. The most significant migration required is moving the existing scaffold from SQLite + in-memory dict storage to PostgreSQL + object storage — this must happen in a specific sequence to avoid data model lock-in.

**Core technologies:**
- **FastAPI 0.115+ / Python 3.11+**: Already scaffolded; async-first; Pydantic v2 validation and OpenAPI generation are essential for this domain's complex nested data models.
- **PostgreSQL 16 + pgvector 0.7+**: Replaces SQLite from scaffold; pgvector eliminates a separate vector database; single storage layer for structured metadata, parsed sections, and semantic embeddings.
- **Redis 7 + Celery 5**: Background ingestion pipeline for large file parsing; response caching for Claude API calls; rate-limit counters. Use Celery over FastAPI BackgroundTasks — heavy parsing blocks the event loop.
- **MinIO (dev) / S3 (prod)**: Content-addressable raw file storage; same boto3 API eliminates production migration; never store raw file bytes in PostgreSQL.
- **Next.js 15 / React 19 / TypeScript 5**: App Router with streaming support for AI responses; TypeScript mandatory given complex nested domain models (PostPackage, ParsedPost, UPG AST).
- **Monaco Editor (`@monaco-editor/react` 4.x)**: The UI centerpiece; built-in diff viewer is required for the post comparison feature; must be configured with Web Workers or it freezes on 294KB files.
- **Anthropic Claude API (claude-sonnet-4-* family)**: Already in scaffold; verify current model ID at project start — scaffold pins `claude-sonnet-4-20250514` which may be stale.

**Critical version/compatibility notes:**
- Next.js 15 requires React 19 — do not mix React 18.
- Tailwind CSS 4 has a completely different config format from v3 — verify shadcn/ui compatibility before scaffolding frontend.
- `AsyncAnthropic` must be used throughout — never sync Anthropic client.
- pgvector embedding dimension must be chosen before the first Alembic migration — changing it later requires dropping and recreating the entire vector index.

**Scaffold migration order:** Postgres + pgvector in Docker Compose → first Alembic migration → replace `_store` dict with SQLAlchemy async CRUD → add MinIO for file upload → add Redis → add Celery for background parse jobs.

### Expected Features

The feature landscape has a clear dependency structure: multi-file package handling and the UPG parser are prerequisites for every AI and semantic search feature. The AI copilot infrastructure (parser output + Claude API) is built once and extended to cover explanation, structural comparison, risky logic detection, and documentation generation.

**Must have (table stakes — v1 feasibility validation, 8 weeks):**
- File upload and ingestion (multi-file package as a unit: .SRC + .LIB + .CTL + .KIN + .PINF + .LNG + .ATR)
- File listing / repository browser with metadata (machine, controller, CAM platform, status)
- File retrieval / download (original bytes, not processed copy)
- Syntax-aware file viewer (Monaco Editor, UPG keyword highlighting)
- Structured UPG parser (.SRC + .LIB, section/variable extraction) — the lynchpin feature
- AI plain-English explanation of post sections — the primary validation gate
- Full-text search (across content and variable names)
- Platform/machine metadata tagging
- Version history (upload-based, upload count is sufficient for v1)

**Should have (competitive advantage — v1.x, post-feasibility):**
- Git-backed version history with diff view (Monaco diff)
- AI structural comparison between two posts
- AI risky logic detection (conservative; requires SME validation gate)
- Variable cross-reference across corpus
- Machine registry with controller dialect tagging
- Multi-file package manifest with orphan detection

**Defer (v2+):**
- Auto-generated post documentation (requires polished AI output)
- Semantic search via pgvector (requires large corpus + validated parser)
- Post family grouping and library version tracking
- HCL intake form integration
- Corpus-driven parsing improvement loop
- Customer-facing multi-tenancy (design for it from day one, build management layer later)

**Anti-features to explicitly reject:**
- AI auto-writes/edits post code (machine-safety risk; trust not yet established)
- Real-time collaborative editing (CRDT complexity; use file locking instead)
- Direct CNC machine connection/upload (scope explosion; safety liability)
- SOLIDWORKS CAM plugin (separate SDK, release cycle, licensing)
- Automated post testing/simulation (requires UPG runtime integration)

### Architecture Approach

The architecture is a layered monolith with async boundaries: Next.js frontend calls a FastAPI REST API, which delegates to service classes that call domain-layer components (parser engine, machine registry, version manager), which write to PostgreSQL/S3/Redis. The critical async boundary is between the API (synchronous from the request's perspective: returns a job ID) and the Celery worker (which does the actual parse + embed pipeline). Domain models (Pydantic) are strictly separated from ORM models (SQLAlchemy) — parsers never touch the database; services translate between domain and ORM.

**Major components:**
1. **UPG Parser Engine** (`core/parsing/camworks/`) — Split by file type (src.py, lib.py, atr.py, kin.py); composed by package.py coordinator; returns pure domain models with no DB access. The hardest component to build correctly.
2. **Ingestion Pipeline** (Celery worker) — Background job: receive → validate → store raw to S3 → dispatch to parser → save parsed structure to PostgreSQL → generate embeddings → commit Git version → mark package ready.
3. **PostPackage Service** — Top-level entity is a PostPackage (7-12 files for one machine), not individual files. This matches how CAM engineers think.
4. **AI Copilot Service + ContextBuilder** — Never sends raw file content; uses semantic search to select 3-5 relevant sections + ATR variable definitions + machine metadata within an explicit token budget.
5. **Search Service** — Hybrid FTS (PostgreSQL tsvector) + semantic (pgvector cosine) running in parallel, merge-ranked with weighted score.
6. **Version Manager** — Per-package Git bare repositories via subprocess + system Git (not dulwich); PostgreSQL indexes commits; truth lives in Git.
7. **Next.js Frontend** — Post browser, Monaco code viewer (read-only), copilot chat panel with streaming SSE, version diff view.

**Key architectural decisions:**
- Package-level data model: `PostPackage` is the top-level entity with child `PostFile` records.
- Ingestion always asynchronous: upload returns 202 + job ID; UI polls status.
- AI context is assembled, not truncated: ContextBuilder selects relevant sections rather than naive truncation.
- One Git bare repo per post package (not a monorepo of all posts).
- Raw file bytes live in S3/MinIO only — PostgreSQL never stores file content.
- SSE (not WebSockets) for streaming copilot responses — simpler, sufficient.

### Critical Pitfalls

1. **AI context truncation (8K characters)** — The existing `copilot.py` truncates at 8,000 characters. A 294KB UPG file is ~300K characters; 8K covers 2.7% of it. Questions about content at character 150,000 receive wrong answers from wrong context. Fix this before any AI testing begins — it will invalidate all test results. Claude's context window (200K tokens) can hold an entire .SRC file; use smart section selection, not truncation.

2. **Parser built before corpus collection** — The existing parser uses INI-style regex patterns (`[SECTION]`, `key = value`) that are fundamentally wrong for UPG's scripting language (event handlers, conditionals, library includes, numeric format specifiers). Hard gate: collect and manually annotate 20+ real UPG files and write a structure catalog document before writing a single line of parser code.

3. **Library includes not modeled in data schema** — UPG .SRC files include .LIB files for shared subroutines. A parser that only sees .SRC files will produce incomplete analysis and AI hallucinations about library-defined constructs. The `PostPackage` data model must include `library_dependencies` and `resolved` fields before the storage layer is built — retrofitting this later requires re-ingesting the entire corpus.

4. **AI confabulation on proprietary UPG constructs** — Claude has minimal training data on CAMWorks UPG. It will produce confident, plausible, wrong explanations for proprietary directives. Mitigations: (a) AI must cite specific line numbers; (b) SME validation corpus of 200 question/answer pairs must be scored before user-facing deployment; (c) UI must label all AI output as "AI-generated interpretation — verify with vendor documentation."

5. **Semantic search returning syntactically similar posts, not behaviorally similar ones** — Raw text embeddings cluster by surface features (same variable names, same machine brand) not behavioral patterns (how arc moves are output, how tool changes are sequenced). Mitigate by embedding structured behavioral summaries of sections, not raw text. Validate with 50 engineer-labeled ground-truth similarity pairs before shipping semantic search.

6. **File content stored in PostgreSQL TEXT columns** — Storing 294KB files as TEXT in PostgreSQL fills the DB rapidly (~1.5GB at 5,000 files), makes backups slow, and loses binary fidelity. All raw file bytes must live in S3/MinIO from the first line of storage code — this is impossible to migrate cheaply after data is in the DB.

---

## Implications for Roadmap

Research across all four files converges on the same phase structure. The dependency graph is unambiguous: parser before ingestion pipeline before AI copilot before search. The main decision is whether to build the frontend iteratively alongside backend phases or as a dedicated final phase. Given the 8-week feasibility window, a minimal UI should be available by Week 5-6 for AI validation testing — engineers cannot validate AI quality through curl commands.

### Phase 1: Foundation and Corpus Collection

**Rationale:** The two biggest pitfalls (parser without corpus, wrong storage design) must be prevented before any code is written. This phase produces no user-facing features but prevents multi-week rewrites. The scaffold's three broken placeholders are fixed here.
**Delivers:** Docker Compose dev environment (Postgres + pgvector + Redis + MinIO), SQLite → PostgreSQL migration, content-addressable raw file storage in MinIO, asynchronous ingestion job skeleton, and — critically — a written UPG structure catalog from manual annotation of 20+ real files. The in-memory `_store` is eliminated; files persist across restarts.
**Addresses (from FEATURES.md):** File upload and ingestion, file retrieval / download (now persistent).
**Avoids (from PITFALLS.md):** File content in DB TEXT columns (Pitfall 6), parser built before corpus (Pitfall 2), library includes not modeled (Pitfall 3).
**Research flag:** Standard infrastructure patterns — does not need `/gsd:research-phase`. The UPG corpus annotation is domain work, not a research question for an AI agent.

### Phase 2: UPG Parser Engine

**Rationale:** The parser is the lynchpin. Every AI feature, semantic search, variable cross-reference, and structural comparison depends on it. Building it second (after corpus collection) with real files as test fixtures is the only viable sequence. Parser quality is the primary risk gate for the entire project.
**Delivers:** File-type parsers for .SRC (section/block extraction), .LIB (subroutine library), .ATR (600+ variable definitions), .KIN (kinematics); package coordinator that resolves cross-file references; `ParsedPost` and `PostPackage` domain models; property-based test suite against real corpus files. Success gate: meaningful sections extracted from 80%+ of corpus files.
**Addresses (from FEATURES.md):** Structured UPG parser (the P1 differentiator), multi-file package handling, platform/machine metadata tagging (auto-extracted from file headers).
**Avoids (from PITFALLS.md):** Parser built before corpus (Pitfall 2), library includes not modeled (Pitfall 3).
**Research flag:** Needs research during planning — UPG format specifics, section boundary detection heuristics. Run `/gsd:research-phase` focused on UPG language structure and real file examples.

### Phase 3: Post Repository (Ingestion + Browser)

**Rationale:** Once the parser exists, wire it into the background ingestion pipeline and build the minimal UI engineers need to interact with the repository. This phase is the first user-facing milestone.
**Delivers:** Celery + Redis ingestion pipeline (upload → S3 → parse → PostgreSQL); post package listing with metadata filters; full-text search (PostgreSQL tsvector); syntax-aware file viewer (Monaco Editor with UPG highlighting or at minimum monospace); basic version history (upload count); file download. The first version HRS engineers can actually use.
**Addresses (from FEATURES.md):** File listing/repository browser, full-text search, syntax-aware file viewer, version history (upload-based). All P1 table-stakes features except AI.
**Avoids (from PITFALLS.md):** Parsing in the HTTP request handler (Pitfall: use Celery), Monaco freezing on 294KB files (configure Web Workers early).
**Research flag:** Standard patterns — does not need `/gsd:research-phase`. Celery + Redis ingestion and PostgreSQL FTS are well-documented.

### Phase 4: AI Copilot (Explanation + Validation Gate)

**Rationale:** AI copilot is the primary validation gate for the feasibility phase. It must be built and validated with real engineers against real posts before any further AI features are added. The ContextBuilder (not file truncation) must be functional here. A mandatory SME validation step is a hard gate before deployment.
**Delivers:** ContextBuilder (section-relevance search + ATR variable lookup + machine metadata + token budget enforcement); Claude API integration with streaming (SSE to frontend); AI plain-English explanation of selected post sections; copilot chat panel in the UI; SME validation corpus and scoring. AI explanations cite specific line numbers. UI labels all AI output as interpretation.
**Addresses (from FEATURES.md):** AI plain-English explanation (P1 differentiator and primary validation gate).
**Avoids (from PITFALLS.md):** AI context truncation (Pitfall 1 — replace 8K truncation with ContextBuilder), AI confabulation (Pitfall 5 — SME validation gate before user deployment), prompt injection via file content (security: XML delimiters).
**Research flag:** Needs research during planning — ContextBuilder section-selection strategy, system prompt engineering for UPG domain, SME validation methodology. Run `/gsd:research-phase` focused on AI context assembly patterns for code analysis.

### Phase 5: Semantic Search and Machine Registry

**Rationale:** Once the parser quality is validated via the copilot, the semantic search layer can be built on top of it. Embedding quality must be validated with engineer-labeled ground-truth pairs before the search UI ships. Machine registry provides controller-specific context that improves AI quality.
**Delivers:** Section-level embeddings generated during ingestion; pgvector HNSW index; hybrid search endpoint (FTS + semantic, merge-ranked); machine registry CRUD API and UI; machine ↔ package linking. Embedding validation: 50 ground-truth similarity pairs scored by engineers.
**Addresses (from FEATURES.md):** Machine registry (P2), semantic search foundation (groundwork for P3 pgvector feature).
**Avoids (from PITFALLS.md):** Behavioral vs. syntactic similarity (Pitfall 4 — embed structured summaries, validate before shipping), embedding dimension mismatch (choose embedding model and dimension before first migration).
**Research flag:** Needs research during planning — embedding model selection (OpenAI text-embedding-3-small vs. Voyage vs. other), behavioral summarization strategy for UPG sections, hybrid search ranking weights.

### Phase 6: Version Control and Advanced AI Features

**Rationale:** With the core platform validated, add the features that require the full infrastructure (parser + AI + search) to work well. Git-backed versioning, structural comparison, and risky logic detection are all in this phase.
**Delivers:** Per-package Git bare repositories (subprocess + system Git); diff API endpoint; Monaco diff view; AI structural comparison between two posts; AI risky logic detection (conservative, with explicit uncertainty); variable cross-reference across corpus.
**Addresses (from FEATURES.md):** Git-backed version history with diff view (P2), AI structural comparison (P2), AI risky logic detection (P2), variable cross-reference (P2).
**Avoids (from PITFALLS.md):** One repository for all posts (Pitfall: one bare repo per package), semantic diff over whitespace noise (semantic diff layer), raw git diff exposing meaningless encoding changes.
**Research flag:** Standard patterns for Git bare repo management — does not need `/gsd:research-phase`. AI risky logic detection prompt engineering may benefit from research.

### Phase Ordering Rationale

- **Corpus before parser:** Pitfalls research is unambiguous — building the parser without real files produces a guaranteed rewrite. This is the most expensive mistake available and costs weeks.
- **Parser before ingestion:** The ingestion pipeline has nothing to do without a parser. The background job worker exists from Phase 1 skeleton but only does store-and-queue until the parser is ready.
- **Ingestion before AI:** The ContextBuilder requires parsed section data in PostgreSQL. The copilot cannot function without ingested and parsed posts.
- **AI validation before semantic search:** Parser quality must be confirmed via AI copilot testing before investing in embedding infrastructure. If the parser produces poor structure, embeddings are noise.
- **Frontend iterative, not last:** A minimal UI ships in Phase 3 so AI validation in Phase 4 can be done by engineers (not via curl). The UI grows with each phase rather than being built all at once.

### Research Flags

**Phases needing deeper research during planning (`/gsd:research-phase`):**
- **Phase 2 (UPG Parser):** UPG language structure is proprietary with sparse public documentation. Research should focus on UPG file format specifications, real example file structures, section boundary patterns, and whether any open-source UPG tools expose grammar details.
- **Phase 4 (AI Copilot):** ContextBuilder design for large code files is non-trivial. Research should focus on code analysis context assembly patterns, token budget strategies, system prompt engineering for proprietary DSL explanation, and validation methodology.
- **Phase 5 (Semantic Search):** Embedding model selection is a permanent schema decision (vector dimension is fixed in first migration). Research should compare text-embedding-3-small vs. Voyage-3 vs. other models for code/DSL content, and examine behavioral summarization strategies.

**Phases with standard patterns (skip `/gsd:research-phase`):**
- **Phase 1 (Foundation):** Docker Compose, PostgreSQL setup, Alembic migrations, MinIO S3 integration — all well-documented patterns.
- **Phase 3 (Repository):** Celery + Redis ingestion pipeline, PostgreSQL FTS tsvector, Monaco Editor setup — all standard patterns with rich documentation.
- **Phase 6 (Version Control):** Git bare repository management via subprocess is a well-documented pattern (consistent with Gitea/Forgejo implementations).

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM | Core stack is project-specified and well-validated (HIGH). Version-specific risks: Claude model ID (LOW — verify at project start), Monaco + React 19 peer deps (MEDIUM), shadcn/ui + Tailwind 4 compatibility (MEDIUM — known to lag). |
| Features | MEDIUM | Domain requirements derived from PROJECT.md ground truth (HIGH) and training knowledge of competitor tools (MEDIUM). No live competitor verification possible. Competitor feature set should be validated at project start. |
| Architecture | HIGH | Based on direct codebase inspection plus established patterns (async ingestion, pgvector hybrid search, Git bare repos per project). Architectural decisions have clear rationale and are consistent across research files. |
| Pitfalls | HIGH | Six of eight critical pitfalls confirmed by direct codebase inspection (not inference). The 8K truncation, in-memory `_store`, and placeholder parser are verified facts in the existing code, not theoretical risks. |

**Overall confidence:** MEDIUM-HIGH

### Gaps to Address

- **Claude model ID**: Verify `claude-sonnet-4-*` current model identifier before first AI integration. The scaffold's `claude-sonnet-4-20250514` is likely stale. Check https://docs.anthropic.com/en/docs/about-claude/models at project start.

- **Embedding model selection**: The vector dimension in the first Alembic migration is permanent without a full re-index. The embedding model (OpenAI text-embedding-3-small at 1536d, Voyage-3, or another) must be chosen before Phase 5 planning. Claude does not expose embeddings directly — a third-party embedding model is required.

- **UPG format specification**: Public documentation for HCL's UPG scripting language is sparse. The structure catalog (Phase 1 corpus collection) will be the primary source of truth. If HRS has access to any HCL documentation or specification documents, these should be collected before development begins.

- **shadcn/ui + Tailwind 4 compatibility**: shadcn/ui was built for Tailwind v3. Verify current shadcn/ui supports Tailwind v4 config format before scaffolding the frontend. If not compatible, evaluate whether to use Tailwind v3 or a different component library.

- **Monaco + React 19 peer dependencies**: Verify `@monaco-editor/react@4.x` declares React 19 as a supported peer dependency. This is a known risk — Monaco's React wrapper historically lags React releases. Test with `npm install` before committing to the stack.

- **SME validation methodology**: The AI copilot validation gate requires a structured approach (200 question/answer pairs, scoring rubric, pass/fail threshold). This methodology should be defined during Phase 4 planning, not improvised during validation.

---

## Sources

### Primary (HIGH confidence)
- `c:/VeriPost/.planning/PROJECT.md` — Project requirements, constraints, domain context, stack specification
- `c:/VeriPost/pyproject.toml` — Confirmed FastAPI 0.115+, Pydantic v2, Python 3.11, anthropic 0.40+, SQLAlchemy 2.x, Alembic 1.13+
- `c:/VeriPost/app/core/ai/copilot.py` — Confirmed 8,000-character truncation bug (line 50)
- `c:/VeriPost/app/services/post_service.py` — Confirmed in-memory `_store`, no file persistence, placeholder `parse_post`
- `c:/VeriPost/app/core/parsing/camworks.py` — Confirmed placeholder INI-style regex patterns with TODO comment
- `c:/VeriPost/app/db/database.py` — Confirmed SQLite dev / PostgreSQL production split (pgvector incompatible with SQLite)
- `c:/VeriPost/docs/architecture.md` — Existing design principles, async-first intent

### Secondary (MEDIUM confidence)
- Training knowledge (cutoff August 2025): Next.js 15, React 19, Tailwind 4, pgvector 0.7, Redis 7, Celery 5 — version currency may have shifted; verify at project start
- Training knowledge: UPG-2 (HCL), CIMCO Edit, Predator CNC Editor competitor feature sets — validate against current product pages before competitive positioning
- Training knowledge: pgvector hybrid search patterns, Celery + Redis ingestion architecture, Git bare repo per-project pattern — well-established but unverified against current documentation

### Tertiary (LOW confidence)
- Claude model ID `claude-sonnet-4-20250514` — scaffold intent confirmed; current validity unknown; MUST verify before use
- pgvector HNSW vs IVFFlat indexing tradeoffs — based on pgvector GitHub documentation; verify against current pgvector version
- Competitor AI-native CAM tools — no verification possible for tools that may have emerged after August 2025 training cutoff

---

*Research completed: 2026-02-18*
*Ready for roadmap: yes*
