# Feature Research

**Domain:** CNC Post Processor Management Platform (CAMWorks/SOLIDWORKS CAM ecosystem)
**Researched:** 2026-02-18
**Confidence:** MEDIUM — WebSearch and WebFetch unavailable; analysis drawn from training knowledge of CIMCO Edit, Predator CNC Editor, UPG-2, and general CAM ecosystem tools (knowledge cutoff August 2025), cross-referenced against the detailed domain context in PROJECT.md. Confidence is MEDIUM (not LOW) because the domain is specialized and well-documented in training data, and PROJECT.md provides unusually rich ground truth from the actual users.

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features CAM engineers assume exist in any serious post management tool. Missing these = product feels broken or untrustworthy before they ever try the AI.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **File upload and ingestion** | Every tool accepts files. UPG-2 does it. Anything less is unusable. | LOW | Already scaffolded. Must handle multi-file packages (.SRC + .LIB + .CTL + .KIN + .PINF + .LNG + .ATR as a unit), not just individual files. |
| **File listing / repository browser** | Engineers need to see what posts exist. This is the front door. | LOW | Must show filename, machine name, controller, CAM platform, last modified. Pagination required — thousands of posts on SharePoint today. |
| **File retrieval / download** | You must be able to get the file back out. Non-negotiable. | LOW | Return original bytes, not a processed copy. Integrity matters on machine-critical files. |
| **Version history** | "What changed and when?" — every post has a revision history comment block. Users expect the platform to formalize this. | MEDIUM | UPG-2 has no version control. This is a known pain point. Git-backed or DB-backed versioning with diff view. |
| **Syntax-aware file viewer** | Engineers must be able to read the file. Monospace + line numbers is minimum. UPG syntax highlighting is better. | MEDIUM | No existing editor supports UPG syntax highlighting well. CIMCO Edit has generic CNC NC-code highlighting, not UPG source highlighting. Must at least render large files without truncation (294KB+). |
| **Full-text search** | "Find all posts that reference HAAS_PROBE_CYCLE." Every CAM tool with more than 10 files needs search. | MEDIUM | Must search across file content, not just metadata. UPG variable names and section names are the primary search targets. |
| **Platform/machine metadata** | Posts need tags: machine type, controller dialect, CAM platform version, customer. Without this, the repository is just a file dump. | LOW | Metadata can be partly auto-extracted from file headers. Manual override needed. |
| **File status tracking** | Is this post active, deprecated, draft, needs-review? Engineers manage post lifecycle. | LOW | Simple status enum. Becomes valuable when combined with search filters. |
| **Multi-file package handling** | A "post" is never one file. It's always a family: .SRC + .LIB + .CTL + .KIN + .PINF + .LNG + .ATR. Treating them as individuals loses context. | HIGH | This is the hardest table-stakes item. Must model the package as a unit with a manifest. Orphaned files are a corruption risk. |
| **Basic diff / change comparison** | "What's different between v3 and v4 of this post?" Text diff is the minimum. | MEDIUM | Line-level diff with syntax awareness. UPG variable changes are the meaningful unit of comparison. |
| **Access control / auth** | HRS engineers cannot have customer posts visible to each other's customers. Even internal use needs role-based access. | MEDIUM | For v1 internal tool: authentication only (HRS staff). Customer-scoped ACL is v2. |

### Differentiators (Competitive Advantage)

Features VeriPost can offer that no existing tool does. These are where the AI copilot and structured parsing create real leverage.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **AI plain-English explanation of post sections** | "Explain what this subroutine does" — the core value proposition. No existing tool does this. CIMCO Edit, Predator, UPG-2 are all dumb text editors. | HIGH | Requires parsed section context + AI prompt chain. Quality depends on parser extracting meaningful structure. Must degrade gracefully when AI unavailable. |
| **Structured UPG parser (section/variable model)** | Converts raw text into queryable structure: sections, variables, subroutine calls, conditional blocks. Enables all AI and search features. | HIGH | No public UPG parser exists. This is novel. Parser accuracy is the lynchpin — everything downstream depends on it. Must be validated against real corpus files. |
| **AI structural comparison between two posts** | "What's semantically different between the HAAS VF-4 post and the HAAS VF-6 post?" Beyond text diff — understands what variables changed and what they mean. | HIGH | Requires both posts parsed. AI gets structured diffs, not raw text diffs. High engineering value for post families. |
| **AI risky logic detection** | "Flag sections that could cause machine faults, axis overtravel, or incorrect tool compensation." Safety-critical capability. | HIGH | Must be conservative and explicit about uncertainty. Misses are acceptable; false safety is not. Requires domain-specific prompt engineering with UPG semantics. |
| **Auto-generated post documentation** | Generate a human-readable spec sheet from the post: supported operations, machine limits, controller compatibility, known quirks. | HIGH | Eliminates the manual documentation that doesn't exist for most posts. Massive time saver for HRS support engineers. |
| **Semantic search (pgvector)** | "Find posts similar to this one" or "find posts that handle 5-axis simultaneous the same way." Beyond keyword search. | HIGH | Requires vector embeddings of parsed post sections. pgvector already in stack. Depends on parser quality. |
| **Variable cross-reference** | "Which posts use variable ID 18247? What does it mean across all posts?" The ATR file defines 600+ variables — cross-referencing them is impossible manually. | MEDIUM | High value for HRS template library management. ATR parser required. Shows where HRS standard variables are used vs overridden. |
| **Machine registry with controller dialect tagging** | Structured knowledge of machine families: HAAS, Doosan, Mori Seiki, etc. Links posts to machine quirks and known issues. | MEDIUM | Not AI-dependent. Pure metadata curation. Enables "show me all HAAS mill posts" and contextualizes AI explanations ("this variable controls HAAS-specific spindle behavior"). |
| **Post family grouping** | HRS uses template libraries (HEADERS, PROBE, MILL/MILLTURN patterns) shared across posts. Surfacing which posts share library versions matters for update propagation. | MEDIUM | When a shared .LIB changes, how many posts are affected? This answers the question and enables impact analysis. |
| **HCL intake form integration** | HRS uses standardized intake forms when customers request posts. Linking intake data to post packages closes the loop. | LOW | CSV/JSON import of form data. Metadata enrichment. Not AI. But uniquely valuable for HRS workflow. |
| **Corpus-driven parsing improvement** | As more posts are ingested, parser patterns improve. The corpus becomes a training set for better section detection. | HIGH | Virtuous cycle: more posts → better parser → better AI → more value. Must design for corpus growth from day one. |

### Anti-Features (Commonly Requested, Often Problematic)

Features engineers will ask for that would harm VeriPost's ability to deliver on its core value.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **AI auto-writes / edits post code** | "Just fix it for me" — obvious ask when AI is in the product. | Post processors are machine-safety-critical. An AI-authored change that passes syntax but fails semantically could crash a $500K machine. No amount of disclaimers makes this acceptable for v1. Trust is not yet established. | AI explains what to change and why. Engineer makes the edit. Copilot reviews the change after. "Explain → suggest → human edits → AI validates" is safer and builds trust. |
| **Real-time collaborative editing** | Teams share posts, so "why can't multiple people edit at once?" | Adds enormous complexity (CRDT or OT algorithms, conflict resolution, presence indicators) for a use case that rarely occurs in practice — posts are owned by one engineer at a time. | File locking with clear ownership. Last-writer-wins with version history to recover from conflicts. |
| **Direct CNC machine connection / upload** | "Can it push the post directly to the machine?" | CNC machine network integration is a completely different domain (DNC, MTConnect, proprietary protocols). Scope explodes. Safety liability is severe. | Integration point: export the post file, engineer loads it through their existing DNC workflow. VeriPost manages the source, not the deployment. |
| **Full CAM system integration (plugin)** | "Integrate with SOLIDWORKS CAM so I can pull posts directly." | SOLIDWORKS/CAMWorks plugin development requires separate API access, SDK licensing, testing against multiple versions, and a completely different release cycle. | REST API that CAM tools can call. Design the API correctly and plugins can be built later as a separate project. |
| **Mobile app** | "I want to check posts on my phone." | Mobile use case for post management is near-zero — this is engineering workstation work. Responsive web is sufficient for occasional tablet use. | Responsive web layout. Not a native app. |
| **WYSIWYG post editor** | "I want to edit the post in a GUI form instead of text." | UPG is a domain-specific language. A form-based editor would require implementing the full UPG language model as a UI — years of work. Also removes engineers' ability to use precise UPG syntax. | Excellent syntax-highlighted code editor (Monaco/CodeMirror) with AI copilot assistance alongside. |
| **Automated post testing / simulation** | "Run the post against a test toolpath and check the G-code output." | Requires integrating the actual UPG runtime or a CAMWorks installation — not a web service. Deep dependency on proprietary software. | Document known test cases and expected output in the machine registry. AI can check for common patterns. Full simulation is a separate tool (VERICUT territory). |
| **SaaS multi-tenancy for v1** | "Can we sell this to other CAM resellers?" | Multi-tenant data isolation, billing, customer onboarding, and SLA management multiply complexity by 5x before core features are validated. | Build tenant-aware data model from day one so the option exists. Don't build the tenant management layer until internal validation is complete. |

---

## Feature Dependencies

```
[Multi-File Package Handling]
    └──requires──> [File Upload & Ingestion]
    └──requires──> [File Listing / Repository Browser]

[Structured UPG Parser]
    └──requires──> [File Upload & Ingestion]
    └──requires──> [Multi-File Package Handling]

[Version History + Diff]
    └──requires──> [File Upload & Ingestion]
    └──requires──> [Structured UPG Parser]  (for semantic diff, not just text diff)

[Full-Text Search]
    └──requires──> [File Upload & Ingestion]
    └──enhances──> [Structured UPG Parser]  (structured search > text search)

[Semantic Search (pgvector)]
    └──requires──> [Structured UPG Parser]
    └──requires──> [Full-Text Search]  (builds on search infrastructure)

[AI Plain-English Explanation]
    └──requires──> [Structured UPG Parser]
    └──requires──> [File Upload & Ingestion]

[AI Structural Comparison]
    └──requires──> [AI Plain-English Explanation]  (same parsing + AI infrastructure)
    └──requires──> [Version History + Diff]

[AI Risky Logic Detection]
    └──requires──> [AI Plain-English Explanation]  (same infrastructure)
    └──requires──> [Structured UPG Parser]

[Auto-Generated Documentation]
    └──requires──> [AI Plain-English Explanation]
    └──requires──> [Structured UPG Parser]

[Variable Cross-Reference]
    └──requires──> [Structured UPG Parser]
    └──requires──> [Full-Text Search]

[Post Family Grouping]
    └──requires──> [Multi-File Package Handling]
    └──enhances──> [Variable Cross-Reference]

[Machine Registry]
    └──requires──> [File Listing / Repository Browser]  (metadata enrichment)
    └──enhances──> [AI Plain-English Explanation]  (controller-specific context)

[HCL Intake Form Integration]
    └──requires──> [Machine Registry]

[Corpus-Driven Parsing Improvement]
    └──requires──> [Structured UPG Parser]
    └──requires──> [Multi-File Package Handling]
    └──enhances──> [All AI Features]
```

### Dependency Notes

- **Structured UPG Parser is the lynchpin:** Every AI feature, semantic search, variable cross-reference, and structural comparison depends on it. If the parser fails to extract meaningful structure from real corpus files, the entire AI value proposition collapses. This is the highest-risk dependency in the system.

- **Multi-File Package Handling must precede the parser:** Real UPG posts are families of files. A parser that only sees .SRC files in isolation will miss .LIB includes, .ATR variable definitions, and .KIN kinematics. Package-aware ingestion is prerequisite to accurate parsing.

- **AI features are additive, not independent:** Plain-English explanation, structural comparison, risky logic detection, and auto-documentation all use the same infrastructure (parser output + AI API). Build the pipeline once, add prompts for each use case.

- **Machine Registry enhances AI quality:** Controller-specific context (HAAS vs Fanuc vs Siemens) dramatically improves AI explanation accuracy. Link machine metadata to AI context before shipping AI features to users.

- **Semantic search requires parser quality first:** Vector embeddings of poorly-parsed sections are noise. Full-text search over raw content is a viable fallback and should ship before semantic search.

---

## MVP Definition

### Launch With (v1 — Feasibility Validation, Weeks 1-8)

Minimum viable for the 8-week feasibility validation with 2-5 HRS engineers. Goal: prove the parser works and the AI is useful on real posts. Not a production release.

- [ ] **File upload and ingestion (single file + package)** — Engineers need to get posts in. Without this, nothing else matters.
- [ ] **File listing / repository browser** — See what's in the system.
- [ ] **File retrieval / download** — Get files back out. Trust is built by not corrupting files.
- [ ] **Syntax-aware file viewer** — Read the file without leaving the browser. UPG keyword highlighting preferred, monospace minimum.
- [ ] **Structured UPG parser (.SRC + .LIB, section/variable extraction)** — The foundational capability. Must be validated against real corpus files. Accuracy gate: meaningful sections extracted from 80%+ of test posts.
- [ ] **AI plain-English explanation of sections** — The core value proposition. Must be useful enough that an engineer without UPG expertise can understand what a section does. This is the primary validation gate.
- [ ] **Full-text search** — Find posts and variables by name. Without search, the repository becomes a second SharePoint.
- [ ] **Platform/machine metadata tagging** — Filename + machine + controller + platform. Manual entry acceptable for v1.
- [ ] **Version history (upload-based)** — Track that a new version was uploaded. Full diff is v1.x.

### Add After Validation (v1.x — Post-Feasibility, if gates pass)

Add once core parsing and AI quality are confirmed.

- [ ] **Git-backed version history with diff view** — Trigger: engineers complain about not seeing what changed. Text diff minimum, UPG-semantic diff preferred.
- [ ] **AI structural comparison** — Trigger: post family management becomes the main workflow. Requires parser quality confirmed.
- [ ] **AI risky logic detection** — Trigger: engineers request safety audit use case. High-value but high-risk to ship prematurely.
- [ ] **Variable cross-reference** — Trigger: ATR file parsing validated. Engineers ask "where is variable 18247 used?"
- [ ] **Machine registry** — Trigger: metadata tagging becomes too manual. Structure the controller/machine knowledge.
- [ ] **Multi-file package grouping with manifest** — Trigger: orphaned file complaints. Engineers lose context when .LIB and .SRC are separated.

### Future Consideration (v2+)

Defer until internal product-market fit is established and commercialization is considered.

- [ ] **Auto-generated post documentation** — High value but complex prompt engineering. Needs polished AI output, not just a draft.
- [ ] **Semantic search (pgvector)** — Needs large corpus and validated parser. Premature before 100+ posts are ingested and parsed.
- [ ] **Post family grouping (library version tracking)** — Needs understanding of HRS template library versioning strategy.
- [ ] **HCL intake form integration** — Process automation, not core platform. Defer until workflow is stable.
- [ ] **Corpus-driven parsing improvement** — Systematic improvement loop. Not needed until corpus is large enough to drive meaningful signal.
- [ ] **Customer-facing multi-tenancy** — After internal validation. Architecture must be tenant-aware from day one (data isolation, scoped IDs), but management layer defers.

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| File upload + package ingestion | HIGH | MEDIUM | P1 |
| File listing / repository browser | HIGH | LOW | P1 |
| File retrieval / download | HIGH | LOW | P1 |
| Structured UPG parser | HIGH | HIGH | P1 |
| AI plain-English explanation | HIGH | HIGH | P1 |
| Full-text search | HIGH | MEDIUM | P1 |
| Syntax-aware file viewer | HIGH | MEDIUM | P1 |
| Platform/machine metadata tagging | MEDIUM | LOW | P1 |
| Version history (upload-based) | HIGH | LOW | P1 |
| Git-backed diff view | HIGH | MEDIUM | P2 |
| AI structural comparison | HIGH | MEDIUM | P2 |
| Variable cross-reference | HIGH | MEDIUM | P2 |
| Machine registry | MEDIUM | MEDIUM | P2 |
| Multi-file package manifest | MEDIUM | HIGH | P2 |
| AI risky logic detection | HIGH | HIGH | P2 |
| Auto-generated documentation | MEDIUM | HIGH | P3 |
| Semantic search (pgvector) | MEDIUM | HIGH | P3 |
| Post family grouping | MEDIUM | MEDIUM | P3 |
| HCL intake form integration | LOW | LOW | P3 |
| Corpus-driven parsing improvement | HIGH | HIGH | P3 |

**Priority key:**
- P1: Must have for feasibility validation
- P2: Add after validation gates pass
- P3: v2+ consideration

---

## Competitor Feature Analysis

**Confidence: MEDIUM** — Based on training knowledge of these tools (knowledge cutoff August 2025). WebSearch/WebFetch unavailable for verification. Validate against current product pages before using this for competitive positioning.

| Feature | UPG-2 (HCL) | CIMCO Edit | Predator CNC Editor | VeriPost Approach |
|---------|-------------|------------|---------------------|-------------------|
| File editing | Yes — native UPG editor | Yes — generic NC text editor | Yes — NC text editor | Viewer first, editor deferred |
| Syntax highlighting | Yes — UPG-specific | Yes — NC G-code (not UPG) | Yes — NC G-code (not UPG) | UPG-specific highlighting (differentiator) |
| Version control | None | None | None (DNC version management is separate product) | Git-backed versioning (differentiator) |
| Search | None / basic | File search, NC block search | Find/replace only | Full-text + semantic search (differentiator) |
| File comparison / diff | None | Basic text compare | None | UPG-aware diff (differentiator) |
| Multi-file package handling | Yes — opens all related files | No concept of packages | No concept of packages | Package-first model (differentiator) |
| AI assistance | None | None | None | Core differentiator — entire category advantage |
| Documentation generation | None | None | None | Differentiator |
| Machine registry / metadata | None | None | None | Differentiator |
| Repository / centralized management | None (file system) | None (file system) | None (file system) | Core capability (differentiator) |
| Web-based | No — Windows desktop only | No — Windows desktop only | No — Windows desktop only | Differentiator — accessible from any browser |
| Variable cross-reference | Limited (UPG-2 has variable inspector) | None | None | Differentiator |
| Collaboration / sharing | SharePoint / email | None built-in | None built-in | Centralized repository replaces SharePoint |

**Key observation:** Every existing tool is a Windows desktop application treating post processors as isolated text files. None models posts as versioned, structured, searchable artifacts with machine metadata. VeriPost's entire product concept — repository + parser + AI — has no direct competitor. The risk is not losing to a competitor; it is that the parser fails to extract enough structure to make AI useful, or that engineers prefer their existing text editor workflow.

---

## Sources

- **PROJECT.md** (C:/VeriPost/.planning/PROJECT.md) — Primary ground truth. Rich domain context from actual users. HIGH confidence.
- **Existing codebase** (C:/VeriPost/) — Shows what is scaffolded vs what is real. Parser is placeholder only. AI copilot is stub. HIGH confidence on what exists.
- **Training knowledge of UPG-2** — HCL Universal Post Generator GUI editor. October 2025 release noted in PROJECT.md. No version control, search, or AI. MEDIUM confidence (training knowledge, not verified against current product).
- **Training knowledge of CIMCO Edit** — Professional CNC editor with backplot, file compare, NC assistant. Industry standard for NC code editing. MEDIUM confidence (training knowledge only).
- **Training knowledge of Predator CNC Editor** — DNC and NC editor product line from Predator Software. MEDIUM confidence (training knowledge only).
- **Training knowledge of general CAM ecosystem** — Post processor management patterns from Mastercam, Hypermill, Open Mind, Siemens NX CAM. MEDIUM confidence.

**Unverified claims requiring validation:**
- Current UPG-2 feature set (check HCL documentation at time of competitive analysis)
- Current CIMCO Edit version and features (v8.x at training cutoff)
- Current Predator CNC Editor version and features
- Whether any new AI-native CAM post management tools emerged after August 2025

---
*Feature research for: VeriPost — CNC Post Processor Management Platform*
*Researched: 2026-02-18*
