# Pitfalls Research

**Domain:** CNC Post Processor Management Platform (VeriPost)
**Researched:** 2026-02-18
**Confidence:** MEDIUM — derived from direct codebase inspection + high-confidence domain knowledge across all five technical areas. WebSearch/WebFetch unavailable; flagged claims marked LOW where unverified by secondary source.

---

## Critical Pitfalls

### Pitfall 1: Truncating Large Post Files Before AI Analysis

**What goes wrong:**
The current `copilot.py` hard-truncates context to 8,000 characters (`context[:8000]`) before sending to Claude. UPG `.SRC` files are ~294KB (~300,000 characters). At 8,000 characters you capture roughly 2.7% of a file. A CAM engineer asks "why is this post outputting wrong feed rates on arc moves?" — the relevant subroutine is at character 150,000. The AI confidently answers about the wrong section and gives incorrect guidance. This is a machine-safety issue, not just a UX one.

**Why it happens:**
Developers copying API quickstart examples use 8K context as a safe default. The problem is invisible in testing because test files are small. The placeholder in `post_service.py` (`"[content would be loaded from storage]"`) means this bug hasn't been exercised with real files yet.

**How to avoid:**
- Use Claude's full context window (200K tokens for claude-sonnet-4). A 294KB file is approximately 73,500 tokens — well within limits.
- For multi-file analysis (`.SRC` + `.LIB` includes), implement chunked context with explicit section headers and file boundaries.
- Pass parsed structural summaries alongside full raw content: give the AI the section map first, then the relevant section(s) in full.
- Implement smart context selection: parse to find the section most relevant to the question, send that section in full + surrounding sections + file header.

**Warning signs:**
- AI gives answers that are plausible but don't match what's actually in the file
- Engineers report "it only knows about the top of the file"
- Test queries about variables defined late in the file return "I don't see this defined"

**Phase to address:**
Parser foundation phase (Weeks 1-4). Fix the truncation before any AI validation testing begins. The 8,000-character limit will produce misleading results in all AI capability tests.

---

### Pitfall 2: Building the UPG Parser Without a Ground Truth Corpus First

**What goes wrong:**
The current `camworks.py` uses generic INI-style patterns (`[SECTION]`, `key = value`) as a placeholder. The real UPG format is a proprietary scripting language with conditionals, subroutines, event handlers, variable references, and library includes — not a configuration file. Building the parser before examining real UPG files produces a parser that:
- Misidentifies format constructs as simple key-value pairs
- Strips meaningful syntax (operators, conditionals) as noise
- Requires a full rewrite once real files are analyzed

**Why it happens:**
The temptation is to ship something working quickly. The `SECTION_PATTERN = re.compile(r"^\s*\[(\w+)\]")` and `VARIABLE_PATTERN` in `camworks.py` look reasonable without real files. The real UPG format likely uses event blocks (`BEGIN_OF_PROGRAM`, `END_OF_PROGRAM`), numeric format specifiers, conditional blocks (`IF/THEN/ELSE`), and `#include`-style library directives — none of which are captured by the current patterns.

**How to avoid:**
- **Week 1 gate:** Do not write parser code until you have 20+ real UPG files manually annotated. Build a structure catalog first (what constructs appear, how often, what are the edge cases).
- Build a test fixture library of anonymized real files before writing a single regex.
- Treat the first 2 weeks as pure archaeology — output is a spec document, not code.
- Use property-based testing (Hypothesis) to verify parser invariants against the corpus.

**Warning signs:**
- Parser returns zero sections on real files
- `detect()` method returns False on actual UPG files
- Section count is always 0 or always 1
- Variables dict contains thousands of entries (false positives from non-key-value lines)

**Phase to address:**
Corpus collection phase (Weeks 1-2, before any parser code). Hard gate: no parser development starts until a written UPG structure catalog exists.

---

### Pitfall 3: Assuming UPG Library Includes are Self-Contained

**What goes wrong:**
UPG `.SRC` files include `.LIB` library files for shared subroutines and common definitions. If the parser and AI copilot only analyze the `.SRC` file, they will encounter undefined variable references, calls to subroutines that "don't exist," and produce analyses that are incomplete or wrong. A CAM engineer asks "what does `CALL_LIB ARC_FEED`" do?" — the AI has never seen `ARC_FEED` because it's in the library file. The AI hallucinates a plausible answer.

**Why it happens:**
Single-file upload APIs are the default mental model. The current upload endpoint accepts one `UploadFile`. Library dependency resolution is not a web API primitive. Developers underestimate how common cross-file references are in post processor scripting — in practice, enterprise UPG setups have 10-30 shared library files that are referenced across hundreds of post files.

**How to avoid:**
- Model post processors as **bundles**, not files: a bundle is a `.SRC` + all referenced `.LIB` files.
- The upload flow must either: (a) accept a zip/folder upload containing all files, or (b) resolve library files from a shared library repository after upload.
- The parser's `ParsedPost` model must include a `library_dependencies: list[str]` field and a `resolved: bool` flag.
- AI context must include relevant library sections when answering questions about library-defined constructs.

**Warning signs:**
- Parser returns unresolved reference warnings on real files
- AI analysis frequently says "I don't see a definition for X"
- Engineers mention "the library" when testing the copilot

**Phase to address:**
Parser foundation phase. The data model must represent bundles before the storage layer is built, or storage will need to be redesigned.

---

### Pitfall 4: Semantic Search That Returns Syntactically Similar Posts, Not Behaviorally Similar Ones

**What goes wrong:**
pgvector similarity over raw text embeddings will cluster posts by their textual surface features: same variable names, same boilerplate headers, same machine brand names. A Fanuc-brand milling post and a Fanuc-brand turning post look very similar in embedding space, but are functionally very different. An engineer searching "find me a post that handles 5-axis simultaneous moves like ours" retrieves posts that share the word "simultaneous" in a comment, not posts with equivalent motion control logic.

**Why it happens:**
Embedding raw text is the default pgvector tutorial approach. The domain-specific semantic unit in post processor code is not the word or sentence — it is the **subroutine behavior pattern** (e.g., how arc moves are output, how tool changes are sequenced, how coordinate transformations are applied). Raw text embeddings don't capture this.

**How to avoid:**
- Embed at the structural level, not raw text: generate structured summaries of each section's behavior before embedding.
- Create separate embedding dimensions for: machine type, controller type, motion capabilities, output format patterns.
- Use hybrid search: pgvector similarity + structured filter (machine type, controller brand, axis count). The structured filter should do heavy lifting; semantic search should rank within the filtered set.
- Validate embedding quality in Week 5-6 by asking engineers: "given post A, does the search find posts you'd consider similar?" before shipping search as a feature.

**Warning signs:**
- Search results always include the most verbose/commented posts regardless of query
- Engineers don't use search after initial testing
- "Similar posts" are from the same machine brand but completely different machine types
- Recall tests show relevant posts ranked outside top 10

**Phase to address:**
AI/search validation phase (Weeks 5-6). Do not build search UI before validating embedding approach with at least 50 "ground truth" similarity pairs from engineers.

---

### Pitfall 5: The AI Copilot Confabulates Post-Processor-Specific Behavior

**What goes wrong:**
Post processor scripting languages are extremely niche — CAMWorks UPG, Mastercam PST format, and DELMIA post scripting are not meaningfully represented in Claude's training data. When asked "what does `PMLFCS` mean in this post?", Claude will construct a plausible-sounding explanation based on pattern matching to similar-looking patterns from other domains. The answer will sound authoritative and be wrong. In the CNC context, a wrong answer about a post directive can cause incorrect G-code that damages workpieces or machines.

**Why it happens:**
Claude is exceptionally good at reasoning about code structure. Engineers trust the responses because the style is confident and the surrounding context (where Claude has genuine knowledge) is accurate. The failure mode is invisible without ground-truth validation. The current system prompt says "when unsure, say so" — but Claude doesn't reliably know when it's in unfamiliar territory with proprietary DSLs.

**How to avoid:**
- **Ground the AI in the actual file.** The copilot must cite specific line numbers and exact text from the file when making claims. "Based on line 1847, `PMLFCS` appears to control..." is verifiable; "PMLFCS typically means..." is dangerous.
- Build a validation corpus: for 20 well-understood posts, have subject-matter experts write the "correct" answers to 10 questions each. Score the AI against these before production use.
- Add explicit uncertainty elicitation to the system prompt: "If a variable name, directive, or construct is not clearly explained in the provided file content, state: 'This construct is not defined in the provided file. I cannot confirm its behavior without its source definition.'"
- Do not present AI explanations as authoritative. The UI must label all AI analysis as "AI-generated interpretation — verify with post vendor documentation."

**Warning signs:**
- AI explains acronyms/variable names confidently without finding them in the file text
- SME review of AI responses shows plausible-but-wrong explanations for proprietary constructs
- Engineers start treating AI output as ground truth rather than a starting point

**Phase to address:**
AI validation phase (Weeks 5-6). Hard gate: do not deploy copilot to real users until SME validation benchmarks pass.

---

### Pitfall 6: Versioning Binary-ish Text Files Without Content-Addressable Storage

**What goes wrong:**
Post processor files look like text but have meaningful whitespace, line endings, encoding quirks (BOM, mixed CRLF/LF), and embedded numeric precision that is semantically significant. Storing them as rows in a VARCHAR/TEXT column and diffing them as strings produces diffs that: (a) flag meaningless whitespace changes as version bumps, (b) collapse semantic changes (a numeric format specifier changing from `##.####` to `##.###`) into a single opaque line diff, (c) lose binary fidelity if the database applies encoding normalization.

**Why it happens:**
SQLAlchemy TEXT column is the obvious choice for "text files." Git-style versioning is not part of standard web app development patterns. Engineers think of these files like source code files — but the current architecture stores raw bytes nowhere and only stores metadata in the DB (`_store` in `post_service.py` doesn't persist content at all).

**How to avoid:**
- Store raw file bytes as a content-addressable blob (SHA-256 hash as key) in object storage (S3 or Azure Blob, since the corpus is on SharePoint). Never store raw content in the relational DB — only store the content hash.
- Implement a semantic diff layer on top of raw text diff: diff at the parsed structure level (section-by-section, variable-by-variable) rather than line-by-line.
- Use normalized encoding on ingest (UTF-8, LF line endings) and store the original encoding separately, so diffs don't surface encoding noise.
- Track version lineage as a DAG (parent_hash → child_hash), not just an ordered version list, to support branching post variants.

**Warning signs:**
- "Same" file uploaded twice creates a new version
- Diff view shows hundreds of whitespace changes obscuring one real change
- File download produces different bytes than file upload
- No content is stored when running the current app (the `parse_post` placeholder confirms this)

**Phase to address:**
Storage foundation phase (Weeks 2-4). This must be designed correctly before any versioning features are built. Retrofitting content-addressable storage onto a schema that already has file content in DB TEXT columns is very expensive.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| In-memory `_store` dict for post storage | Zero setup, instant dev iteration | Lost on restart, cannot be shared across workers, no persistence | Week 1-2 skeleton only. Must be replaced before any AI testing |
| Hardcoded `context[:8000]` truncation | Avoids token limit errors | Produces wrong AI answers on large files, safety risk | Never. Remove before AI testing |
| Platform-as-string (not enum) | Flexible, easy to add values | Typos cause silent routing failures, no exhaustiveness checking | MVP only — add Enum by Phase 2 |
| Regex-based UPG "parser" | Gets CI green | Fundamentally wrong model of UPG format, full rewrite required | Acceptable as a skeleton marker. Must be annotated `# PLACEHOLDER` explicitly |
| Single-file upload (no bundle support) | Simpler API surface | Breaks analysis of any file with library includes | Acceptable for Week 1-2 prototype if library resolution is in the roadmap |
| SQLite for development, PostgreSQL for production | Easy local setup | pgvector is not available in SQLite — vector search cannot be tested locally | Acceptable only if pgvector tests run against a dockerized PostgreSQL |
| No file content storage (parse-on-demand only) | Defers storage design | Cannot do batch indexing, version history, or corpus search | Must be resolved before corpus indexing begins |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Claude API (Anthropic) | Setting `max_tokens=2048` as a static cap | Use `max_tokens` appropriate to the task. Explanation of a 300KB file section may need 4K-8K tokens. Cap by task type. |
| Claude API | Sending raw file content as one blob | Send structured context: file header + section map + relevant section(s). Use XML tags to delimit sections for Claude. |
| pgvector (PostgreSQL extension) | Installing pgvector on SQLite dev DB | pgvector requires PostgreSQL. Run PostgreSQL in Docker for local dev. Do not defer to production. |
| pgvector | Using default `vector(1536)` dimension for OpenAI embeddings | If using Claude-based embeddings or a different model, dimension must match. Wrong dimension causes silent wrong results or schema errors. |
| SharePoint (corpus source) | Assuming SharePoint REST API is stable | SharePoint Graph API throttles aggressively. Batch imports of thousands of files will hit rate limits. Implement exponential backoff and a resumable job queue from day one. |
| Monaco Editor | Integrating as an npm package in a plain JS page | Monaco requires a bundler (webpack/vite) with specific worker configuration. Without the worker setup, large files (294KB) cause the UI thread to block and the editor to freeze. |
| Monaco Editor | Expecting TextMate grammar = full language server | TextMate grammars provide syntax coloring only. Semantic features (go-to-definition, hover docs) require a Language Server Protocol implementation, which is a separate multi-week effort. |
| FastAPI + async SQLAlchemy | Using `expire_on_commit=True` (default) | After commit, accessing lazy-loaded attributes raises `MissingGreenlet` in async context. The current `expire_on_commit=False` setting is correct — do not change it. |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Parsing every file on every AI request | Latency spikes, re-parsing identical files repeatedly | Cache parsed structure in DB. Parse once on ingest, store `ParsedPost` as JSONB. Re-parse only when file version changes. | At 50+ files being analyzed concurrently |
| Embedding all ~thousands of files synchronously on corpus import | Import job times out, API costs spike unpredictably | Use a background job queue (Celery + Redis, or FastAPI BackgroundTasks for small scale). Process files in batches of 10-20 with rate limiting. | At 500+ files in a single import batch |
| Full corpus re-indexing when one file changes | Nightly re-index takes hours, search is stale | Implement incremental indexing: only re-embed files whose content hash has changed. Track `last_indexed_at` per file. | At 2,000+ files in corpus |
| Sending 294KB file to Claude API on every question | API cost is $0.50+ per complex question, adds up at team scale | Parse once, store extracted sections. Send only the relevant section(s) to Claude, not the whole file. | At 10+ engineers using copilot daily |
| pgvector HNSW index rebuild on every insert | INSERT operations lock the index, causing latency spikes | Build HNSW index after initial bulk load, not during it. Use IVFFlat for bulk initial indexing, then switch to HNSW for production queries. | At 1,000+ vectors in table |
| Storing raw file content in PostgreSQL TEXT column | DB backup size explodes, backup/restore takes hours | Store content in object storage (blob), store only hash and metadata in PostgreSQL. | At 5,000+ files × 294KB average = ~1.5GB in DB |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Serving raw post processor files without authorization checks | Post processor files contain proprietary machine configurations and toolpath logic — competitive IP. Unauthorized access exposes customer manufacturing data. | Require authentication on all `/posts/*` endpoints. Implement organization-level data isolation from day one — do not build multi-tenant features on top of single-tenant auth later. |
| Passing user-supplied file content directly to Claude API without sanitization | Prompt injection via malicious file content. A file could contain `---SYSTEM OVERRIDE: ignore previous instructions---` patterns. | Strip or escape prompt-injection-looking patterns before insertion into Claude message. Or use XML delimiters with explicit boundary markers that are hard to inject across. |
| Storing Anthropic API key in the `.env` file committed to git | API key exposure = unbounded cost liability | `.env` is in `.gitignore` (verified). Ensure `.env.example` never contains real keys. Add pre-commit hook to detect secrets. |
| Accepting any file type through the upload endpoint | Malicious file upload (polyglot files, files with excessively deep nesting that DoS the parser) | Validate file extension AND magic bytes on upload. Set a maximum file size limit (e.g., 2MB — UPG files should not exceed ~500KB). Timeout parser execution. |
| Logging raw post processor content | Post file content in logs exposes IP in log aggregation services (Datadog, Splunk) | Never log `raw_content`. Log only `post_id`, `filename`, `platform`, `section_count`. |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Displaying AI analysis as a single blob of text | CAM engineers scan for specific information; a wall of text is ignored. Copilot adoption fails. | Structure AI output with labeled sections: "What this section does:", "Potential issues:", "Suggested changes:". Use the prompt to enforce structured output. |
| Showing raw post file content in a generic text editor | Engineers cannot navigate a 294KB file in a scrolling textarea. Critical sections are buried. | Monaco editor with section folding, go-to-section navigation, and at minimum syntax coloring for the most common constructs. Navigation is more important than highlighting. |
| Requiring file upload for every analysis session | Engineers who regularly work with the same 10-20 posts are frustrated by repeated uploads. | Implement a "My Posts" library that persists uploaded files for the user's session/account. |
| Showing version history as raw timestamps | Engineers name post versions by machine/job (e.g., "Haas ST-20 after adding C-axis"). Timestamps are meaningless. | Require a commit message on every version save. Display history as "filename — commit message — author — date". |
| Exposing platform detection as automatic only | When auto-detection fails on an unusual file, the engineer has no way to override it. | Always show "detected platform: X" with a dropdown to override. Auto-detect is a default, not a constraint. |

---

## "Looks Done But Isn't" Checklist

- [ ] **UPG Parser:** Regex returns sections on real 294KB files — verify with actual corpus files, not synthetic test data. The current patterns will fail on real UPG syntax.
- [ ] **AI Copilot:** Answers reference specific line numbers from the file — if the AI cannot cite line numbers, it is not using the file content.
- [ ] **Library Resolution:** When analyzing a `.SRC` file that includes `.LIB` files, verify those library definitions appear in the AI's context. Upload a `.SRC` that calls a library function and ask "what does `CALL_LIB X` do?" — if the AI doesn't know, library resolution is not working.
- [ ] **Versioning:** Upload the same file twice. Verify only one version is created (content-addressable deduplication). Then modify one character and upload again — verify a new version is created.
- [ ] **Semantic Search:** Run the query "arc output format" against the corpus. Manually verify the top 5 results actually contain arc motion handling logic, not just the word "arc" in comments.
- [ ] **File Persistence:** Restart the API server. Verify previously uploaded posts are still retrievable. (Currently they are not — `_store` is in-memory.)
- [ ] **Monaco Editor:** Load a 294KB UPG file into the editor. Verify the browser does not freeze or drop keystrokes. Test on the target hardware (engineering workstations, not developer MacBooks).
- [ ] **Multi-file Bundle:** Upload a `.SRC` + its `.LIB` files as a bundle. Verify the parser correctly resolves cross-file references.

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| AI truncation discovered after engineers tested copilot | MEDIUM | Remove truncation, re-run test sessions, re-collect feedback. Previous test results are invalid. |
| UPG parser built before corpus collected | HIGH | Full parser rewrite. Sunk cost of regex infrastructure. Allow 2 extra weeks. |
| File content stored in DB TEXT column (not blob storage) | HIGH | Data migration: extract content to object storage, replace DB rows with hashes. Risk of data loss during migration. |
| Library dependencies not modeled in data schema | HIGH | Schema migration, rewrite upload flow, re-ingest all corpus files as bundles. Allow 3+ extra weeks. |
| AI confabulation discovered in production with real engineers | CRITICAL | Immediate disclosure to affected engineers. Audit all AI responses that were acted upon. Add SME validation gate before re-enabling copilot. |
| Embedding dimension mismatch discovered after indexing | MEDIUM | Drop and recreate vector index with correct dimensions. Re-embed all documents. Allow 1-2 days per 1,000 documents. |
| SharePoint import rate-limited and data only partially synced | LOW | Add retry queue, re-run import with exponential backoff. No data loss if import is idempotent (content-addressable). |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| AI context truncation (8K chars) | Phase 1: Parser/AI skeleton — fix before Week 3 AI testing | Send 294KB file, ask question about content at position 150,000. Verify AI cites that section. |
| Parser built without corpus | Phase 1: Corpus collection — hard gate before parser code | Written UPG structure catalog must exist and be reviewed before any regex is written |
| Library include dependencies not modeled | Phase 1: Data model design — before storage is built | Upload `.SRC` + `.LIB` bundle, verify `library_dependencies` field is populated |
| Behavioral vs. syntactic similarity in search | Phase 3: Semantic search validation — before search UI is built | 50 ground-truth similarity pairs scored by engineers before feature ships |
| AI confabulation of proprietary constructs | Phase 2: AI validation — hard gate before user-facing deployment | SME scores 200 AI responses against ground truth; accuracy threshold must be defined and met |
| Text column file storage | Phase 1: Storage design — before any ingest code is written | Restart server; all uploaded files still retrievable via hash lookup |
| Monaco freezing on 294KB files | Phase 3: Frontend development — early in UI phase | Load 294KB file on target hardware; measure time-to-interactive |
| No semantic diff for versions | Phase 2: Versioning — when version history UI is built | Modify one numeric format specifier; verify diff highlights exactly that change |
| SharePoint rate limiting on bulk import | Phase 1: Corpus collection — design import job before running it | Run import of 100 files; verify idempotent retry with no duplicates |
| Prompt injection via file content | Phase 1: API hardening — before any external-facing deployment | Upload file containing injection patterns; verify Claude response is not affected |

---

## Sources

- Direct codebase inspection: `C:/VeriPost/app/core/ai/copilot.py` — confirmed 8,000-character truncation (line 50)
- Direct codebase inspection: `C:/VeriPost/app/services/post_service.py` — confirmed in-memory `_store`, no file content persistence, placeholder `parse_post`
- Direct codebase inspection: `C:/VeriPost/app/core/parsing/camworks.py` — confirmed placeholder INI-style regex patterns with `TODO` comment
- Direct codebase inspection: `C:/VeriPost/app/db/database.py` — confirmed SQLite dev / PostgreSQL prod split (pgvector incompatibility)
- Domain knowledge: CAMWorks UPG format characteristics (HIGH confidence — well-documented in CAM engineering literature)
- Domain knowledge: Claude API context window and token behavior (HIGH confidence — Anthropic official docs)
- Domain knowledge: pgvector HNSW vs IVFFlat indexing tradeoffs (MEDIUM confidence — based on pgvector GitHub documentation, unverified against current version)
- Domain knowledge: Monaco Editor worker architecture requirements (HIGH confidence — Monaco official documentation)
- Domain knowledge: CNC post processor file characteristics — library includes, binary-ish text, encoding sensitivity (HIGH confidence — industry standard behavior)
- Domain knowledge: LLM confabulation patterns on proprietary DSLs (HIGH confidence — well-established phenomenon in LLM literature)

---
*Pitfalls research for: VeriPost — CNC Post Processor Management Platform*
*Researched: 2026-02-18*
