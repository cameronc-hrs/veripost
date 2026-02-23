# Roadmap: VeriPost

## Overview

VeriPost is built in five phases that follow an unambiguous dependency chain: foundation infrastructure before parser, parser before repository, repository before AI copilot, and AI copilot before authoring workflow. Each phase delivers a verifiable capability, with Phase 4 (AI Copilot Core) serving as the hard feasibility gate — if engineers cannot use the AI to understand real post processor code, the platform's primary differentiator is unproven and no further investment is warranted. The 8-week feasibility window is the lens through which every phase is scoped.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Foundation** - Dev environment, persistence layer, and UPG corpus collection that unblocks everything downstream
- [ ] **Phase 2: Parser Engine** - UPG parser that extracts meaningful structure from real corpus files — the lynchpin of the platform
- [ ] **Phase 3: Post Repository** - Ingestion pipeline, authenticated repository browser, file viewer, and version history — first user-facing milestone
- [ ] **Phase 4: AI Copilot Core** - Plain-English explanation of post code with validated accuracy — the primary feasibility gate
- [ ] **Phase 5: Authoring Workflow** - AI-assisted identification and application of customer requirements to post source

## Phase Details

### Phase 1: Foundation
**Goal**: A working dev environment with real persistence, async infrastructure, and a documented UPG corpus — so that every phase that follows builds on solid ground rather than placeholder stubs
**Depends on**: Nothing (first phase)
**Requirements**: None (infrastructure prerequisite — all 19 v1 requirements depend on this phase but are delivered in subsequent phases)
**Success Criteria** (what must be TRUE):
  1. The dev stack (PostgreSQL + pgvector, Redis, MinIO) runs from a single `docker compose up` command and survives a restart with data intact
  2. A file uploaded via the API is stored in MinIO (not in a database column), retrievable with original bytes, and the in-memory `_store` is gone
  3. An async ingestion job skeleton accepts an uploaded file, enqueues it to Celery/Redis, and returns a job ID — even if the parse step is a stub
  4. A UPG structure catalog document exists, derived from manual annotation of 20+ real corpus files, describing section patterns, block delimiters, variable references, and library include syntax
**Plans**: 4 plans in 3 waves

Plans:
- [x] 01-01-PLAN.md — Docker Compose dev environment (PostgreSQL+pgvector, Redis, MinIO, Celery worker) [Wave 1]
- [x] 01-02-PLAN.md — PostgreSQL migration, eliminate _store, wire MinIO for file storage [Wave 2]
- [x] 01-03-PLAN.md — Async ingestion skeleton (ZIP upload, Celery task, status polling) [Wave 3]
- [ ] 01-04-PLAN.md — UPG corpus collection and structure catalog (20+ files, 3 controller types) [Wave 1]

### Phase 2: Parser Engine
**Goal**: Engineers can upload real post processor packages and the system reliably extracts structured sections, variables, and cross-file references — making the corpus queryable and AI-ready
**Depends on**: Phase 1
**Requirements**: PARS-01, PARS-02, PARS-03, PARS-04
**Success Criteria** (what must be TRUE):
  1. A .SRC file from the real corpus produces a parsed result with named subroutines, conditional blocks, and operation handlers — not an empty or error response
  2. A .LIB file from the real corpus produces a parsed result with variable definitions and library includes resolved
  3. Parser successfully extracts meaningful structure from 80%+ of the real corpus files (PARS-03 accuracy gate), verified by a test suite run against real files
  4. Engineer can view the parsed section tree alongside raw source in the code viewer — both panels populated from real corpus data
**Plans**: TBD

Plans:
- [ ] 02-01: UPG .SRC parser (section/subroutine/block extraction) built against real corpus files
- [ ] 02-02: .LIB, .ATR, and .KIN file parsers with cross-file reference resolution
- [ ] 02-03: Package coordinator, PostPackage/ParsedPost domain models, property-based test suite
- [ ] 02-04: Wire parser into Celery ingestion job, save structured output to PostgreSQL

### Phase 3: Post Repository
**Goal**: Authenticated HRS engineers can upload, browse, tag, download, and track versions of post processor packages through a working web UI
**Depends on**: Phase 2
**Requirements**: REPO-01, REPO-02, REPO-03, REPO-04, REPO-05, ACCT-01, ACCT-02
**Success Criteria** (what must be TRUE):
  1. Engineer can log in via SSO/OAuth (Azure AD) and is blocked from accessing any page without authentication
  2. Engineer can upload a multi-file post processor package (.SRC, .LIB, .CTL, .KIN, .PINF, .LNG, .ATR) as a single grouped unit and see it appear in the repository browser
  3. Engineer can browse the repository and see each package's machine name, controller type, CAM platform, and upload status
  4. Engineer can download any individual file or the complete package and receive original bytes intact
  5. Engineer can view upload-based version history for any package, showing who uploaded each version and when
**Plans**: TBD

Plans:
- [ ] 03-01: OAuth/SSO authentication (Azure AD), session management, access guard middleware
- [ ] 03-02: Post package upload API with multi-file grouping, ingestion job dispatch, status polling
- [ ] 03-03: Repository browser UI (Next.js) with metadata filters, package listing, tagging (machine, controller, CAM platform)
- [ ] 03-04: File download endpoint and version history UI

### Phase 4: AI Copilot Core
**Goal**: Engineers can select a section of real post processor code and receive a plain-English explanation accurate enough to understand machine behavior — validated by 2-5 HRS engineers against real corpus files
**Depends on**: Phase 3
**Requirements**: AI-01, AI-02, AI-03
**Success Criteria** (what must be TRUE):
  1. Engineer can select a section of post code in the viewer and receive a plain-English explanation of what that section does on the machine
  2. AI explanation references controller dialect or known quirks when machine metadata is available for that package
  3. AI explanations pass SME validation: 2-5 HRS engineers score explanation quality against a corpus of 50+ real questions, and the majority rate explanations as accurate enough to act on
  4. Every AI response cites specific line numbers from the source, and the UI labels all output as AI-generated interpretation requiring verification
**Plans**: TBD

Plans:
- [ ] 04-01: ContextBuilder — section-relevance selection, ATR variable lookup, machine metadata injection, token budget enforcement (replaces 8K truncation)
- [ ] 04-02: Claude API integration with streaming SSE, copilot chat panel in the UI, line-number citation requirement
- [ ] 04-03: SME validation corpus (50+ question/answer pairs from real files, scoring rubric, pass/fail threshold)

### Phase 5: Authoring Workflow
**Goal**: Engineers can bring a customer's custom requirements into the platform, get AI-guided identification of which post sections need modification, review AI-suggested changes in the code viewer, and track which requirements drove which source changes
**Depends on**: Phase 4
**Requirements**: AUTH-01, AUTH-02, AUTH-03, AUTH-04, AI-04
**Success Criteria** (what must be TRUE):
  1. Engineer can enter a customer's custom requirements and the AI identifies which specific sections of the existing post source are relevant to those requirements
  2. AI can suggest specific code changes to apply a customer requirement to a base post template, with the suggestion presented as a diff in the code viewer
  3. Engineer can review, edit, and apply AI-suggested changes through the Monaco code viewer
  4. System tracks which customer requirements correspond to which source changes so engineers can trace decisions back to their origin
  5. AI can summarize the customer-specific customizations in a post relative to the base HRS template
**Plans**: TBD

Plans:
- [ ] 05-01: Customer requirements intake and AI-guided section identification (AUTH-01, AI-04)
- [ ] 05-02: AI change suggestion engine with diff output and Monaco diff view integration (AUTH-02, AUTH-03)
- [ ] 05-03: Requirements-to-changes traceability model and UI (AUTH-04)

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 3/4 | In progress | - |
| 2. Parser Engine | 0/4 | Not started | - |
| 3. Post Repository | 0/4 | Not started | - |
| 4. AI Copilot Core | 0/3 | Not started | - |
| 5. Authoring Workflow | 0/3 | Not started | - |
