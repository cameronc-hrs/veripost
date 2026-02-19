# Phase 1: Foundation - Research

**Researched:** 2026-02-19
**Domain:** Dev infrastructure (Docker Compose, PostgreSQL+pgvector, Redis, MinIO, Celery) + UPG corpus archaeology
**Confidence:** HIGH for infrastructure stack (direct codebase + prior research confirmed); MEDIUM for corpus findings (limited to 2 customer packages in C:\CAM CONTENT)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### UPG corpus & catalog
- Large, diverse corpus in C:\CAM CONTENT (thousands of files, many controller types, multiple CAM platforms)
- Select top 3 most common controller types for the initial 20+ file corpus — Claude to scan C:\CAM CONTENT to identify them by file count
- Good coverage across all three controller types, not just one
- Claude to also scan C:\CAM CONTENT for all file extensions present (user unsure if the 7 known types are exhaustive)

#### Dev workflow
- User is not a DevOps person — follows instructions but won't troubleshoot infrastructure issues independently
- Docker Desktop may or may not be installed; verify and install if needed as part of Phase 1
- Setup must be dead simple: single command to start everything
- Small team (1-2 other developers) — setup must be reproducible across machines
- Claude owns all infrastructure decisions (tooling, configuration, containerization approach)

#### Data migration
- All existing SQLite and _store data is disposable — fresh start with PostgreSQL
- MinIO file storage organized by package (each package gets its own prefix/folder)
- Validate file types at upload — only accept known UPG file extensions; reject unrecognized types
- Full list of valid extensions to be determined by scanning C:\CAM CONTENT

#### Ingestion job
- Upload mechanism: ZIP file upload (single .zip containing all package files)
- Error messages: friendly plain-English message with expandable technical details section
- Engineers are technical users but UX should still be approachable

### Claude's Discretion
- Annotation depth for UPG structure catalog (pattern inventory vs deep semantic annotation — pick what downstream phases need)
- Ingestion job status granularity (simple vs detailed per-file progress — pick right level for a skeleton)
- Individual file upload vs packages-only policy
- Docker Compose configuration, service ports, networking
- Progress reporting implementation
- All infrastructure architecture decisions

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

---

## Summary

Phase 1 has two distinct workstreams that must be sequenced carefully: infrastructure standup and corpus archaeology. The infrastructure work (Docker Compose, PostgreSQL migration, MinIO, Redis, Celery skeleton) is well-understood and follows patterns already documented in prior project research. The corpus archaeology is novel — scanning real UPG files to produce the structure catalog that Phase 2 parser development depends on.

**Docker Desktop is not installed** on the user's machine (verified: `C:\Program Files\Docker` does not exist). Installing Docker Desktop is the first task of Phase 1 — nothing else can proceed without it. The install path is well-documented and straightforward on Windows 11.

The UPG corpus scan of `C:\CAM CONTENT` reveals the current available corpus is **2 complete customer packages** (HAAS VF-4 Mill, HAAS ST-15Y MillTurn) plus a partial Mori Seiki Dura Center set (CTL + LNG only, no SRC). This is far fewer than the 20+ files required. The plan must include sourcing additional packages from the broader SharePoint corpus. For controller type coverage, the available evidence points to **HAAS** as the dominant controller in the local sample; Fanuc (used in Doosan machines documented in the folder) and Mori Seiki round out the three recommended controller types to target for corpus collection.

File extensions confirmed in the corpus: `.SRC`, `.LIB`, `.CTL`, `.KIN`, `.PINF`, `.LNG`, `.ATR`. Additional non-UPG extensions found: `.RTF` (report/setup sheet), `.zip` (delivery archives). The 7 documented extensions appear complete — no unknown UPG format extensions were discovered in the scan.

**Primary recommendation:** Install Docker Desktop first, then execute the scaffold-to-PostgreSQL migration in the documented order (Postgres → Alembic → asyncpg → MinIO → Redis → Celery), then run corpus archaeology in parallel with infrastructure validation.

---

## Corpus Scan Results

### C:\CAM CONTENT File Census

**Complete UPG packages found:**

| Package | Machine | Controller | SRC | LIB count | CTL | KIN | ATR | PINF | LNG |
|---------|---------|-----------|-----|-----------|-----|-----|-----|------|-----|
| HAAS_VF-4 | HAAS VF-4 Mill | HAAS | 1 | 5 | 1 | 1 | 1 | 1 | 1 |
| HAAS_ST-15Y | HAAS ST-15Y MillTurn | HAAS | 1 | 4 | 1 | 1 | 1 | 1 | 1 |

**Partial/reference-only material found:**
- Mori Seiki Dura Center: `F6M4A.CTL` + `F6M4A.LNG` only (no SRC — not a usable post package)
- `MoriDuracenter.ctl` + `MoriDuracenter.lng` in MoriDuracenter.zip (same situation)

**Non-UPG files found in corpus folder:**
| Extension | Count | Purpose |
|-----------|-------|---------|
| `.RTF` | 3 | Setup sheets (short-form and long-form documentation included with post delivery) |
| `.zip` | 6 | Package delivery archives (contain the UPG files above) |
| `.NCF` | 1 | Sample NC program (machine output, not post source) |
| `.NC` | 1 | NC code sample |
| `.pdf` | many | Machine documentation (not UPG files) |
| `.docx` | several | HCL intake forms, customer request forms |

**Confirmed UPG file extensions (complete list from corpus scan):**
`.SRC`, `.LIB`, `.CTL`, `.KIN`, `.ATR`, `.PINF`, `.LNG`

No additional unknown UPG extensions found. The 7 documented extensions are confirmed as the complete set for upload validation.

### Controller Type Recommendation

**Available evidence from C:\CAM CONTENT:**
- HAAS: 2 complete packages (Mill + MillTurn) — only controller with complete posts
- Fanuc: Extensive machine documentation (Doosan DNM350, PUMA, LYNX machines all use Fanuc controllers) — no post SRC files locally
- Mori Seiki / Mitsubishi: Machine documentation present — no complete SRC files locally

**Recommended top 3 controller types for corpus collection (20+ files):**
1. **HAAS** — 2 local packages ready; confirmed HRS template; most accessible for initial work
2. **Fanuc** — Doosan machines widely documented; Fanuc G-code is the industry baseline; many HRS posts likely exist on SharePoint
3. **Mori Seiki (Mitsubishi controller)** — documented in machine folder; distinct controller dialect from HAAS/Fanuc; good coverage diversity

**Coverage target:** ~7 packages per controller type (20+ total). Each package = all 7 file types. Balance Mill, MillTurn, and Lathe machine types across the three controllers where available.

---

## UPG Structure Catalog: Observed Patterns

Based on direct inspection of `HAAS_VF-4.SRC` (5,966 lines), `HAAS_ST-15Y.SRC` (745+ sections), and associated library files.

### File-Level Structure

**`.SRC` file anatomy (in order):**
1. **Confidentiality header block** — `*####...` banner + proprietary notice (lines 1-11)
2. **File description block** — `~~ F I L E   D E S C R I P T I O N ~~` ASCII banner with machine type, system, library notes (lines 13-39)
3. **Revision history block** — `~~ R E V I S I O N   H I S T O R Y ~~` — detailed chronological change log, each entry: Date/Revision/Modifications (lines 40-450+)
4. **Machine header summary** — `Controller:`, `Machine:`, `Company:`, `Version:`, `Date:`, `Programmer:`, `Created From:` (lines 456-467)
5. **File management defines** — `:DEFINE` directives for `MILL_SYSTEM_SUB`, `KIN_INCLUDE`, `WARRANTY_EXEMPT`, `_DEBUG_`, `_DEBUGLIB_` (lines 471-513)
6. **Post header settings** — `:SYSTEM=`, `:LEADING=`, `:TRAILING=`, `:DECIMAL=`, `:ARCS=`, `:5AXIS_MILLING=`, `:MAXIMUM_LINE=`, etc. (lines 521-590)
7. **Descriptor block** — `:ATTRNAME=` / `:ATTRTYPE=DESCRIPTOR` definitions for metadata fields (CUSTOMER, MACHINE NAME, CONTROLLER TYPE, POSTCREATOR, NTPN, WARRANTY EXPIRY DATE, etc.) (lines 592-780)
8. **Library declarations** — `:LIBRARY=<path>` (lines 786-790, exactly 4-5 libraries for Mill, similar for MillTurn)
9. **Variable define block** — `:DEFINE` constants for G-codes, M-codes, feed formats, configuration switches (lines 792-1600)
10. **Attachables** — `:ATTRNAME=attachable` with `:ATTRLIST=` (lines 816-826)
11. **Machine posting tab questions** — `:ATTRNAME=setup` with `:ATTRLIST=` entries (lines 832-911)
12. **Operation posting tab questions** — `:OPERID=MILL_OPER_SETUP` through various OPERID types, each with `:OPERLIST=` entries and `:OPEREND` (lines 912-1690)
13. **Template sections** — `:SECTION=<NAME>` blocks, each followed by one or more `:T:` output template lines (lines 1697-4331 in Mill; 744+ sections in MillTurn)
14. **CALC sections** — `:SECTION=CALC_<NAME>` blocks containing computational logic with `IF/THEN/ELSE`, variable assignments, subroutine calls (lines 4332-5966)
15. **Debug area** — `DEBUG_LIB` and debug scaffolding at end of file

### Key Syntax Patterns Observed

**Comments:** Lines beginning with `*` are comments (not `//` or `#`)

**Define directives:**
```
:DEFINE VARIABLE_NAME=value
```

**Attribute (variable metadata) blocks:**
```
:ATTRNAME=variable name
:ATTRTYPE=DESCRIPTOR|LIST|SELECT|VALUE|POST
:ATTRVTYPE=CHARACTER|INTEGER|DECIMAL|SELECT
:ATTRSEL=N
:ATTRINLEN=<integer>
:ATTRSHORT=Short label
:ATTRDEFAULT=default value
:ATTREND
```

**Library includes:**
```
:LIBRARY=C:\path\to\file.LIB
```
Note: Paths are absolute Windows paths from the build machine — these will NOT match paths on other machines. The resolver must locate libraries by filename, not absolute path.

**Section declarations:**
```
:SECTION=SECTION_NAME
:T: template line with <VARIABLE_REFS> and conditionals
:T: IF condition THEN output ENDIF
```

**Operation tab definitions:**
```
:OPERID=OPERATION_TYPE_NAME
:OPERSUB=SUBTYPE
:OPERLIST=variable_name
:OPEREND
```

**Header settings (no colon-colon, just colon):**
```
:SYSTEM=MILL
:LEADING=FALSE
:5AXIS_MILLING=TRUE
:MAXIMUM_LINE=100
```

**Variable references in template lines:**
- `<VARIABLE_NAME>` — output variable value
- `<VARIABLE!>` — forced output
- `<G:GCODE_NAME>` — G-code output
- `<M:MCODE_NAME>` — M-code output
- `<EOL>` — end of line
- `<BLANK>` — blank line
- `<COMMENT_START>` / `<COMMENT_END>` — comment delimiters

**Conditionals in template lines:**
```
:T: IF condition THEN output ENDIF
:T: IF condition THEN output ELSE other_output ENDIF
```

**CALC section logic:**
```
:SECTION=CALC_CNFG_CODES
* comments explaining the switch
:IF SOME_CNFG_VAR = 1 THEN
  VARIABLE = value
  CALL(OTHER_CALC_SECTION)
:ENDIF
```

### Section Category Taxonomy

From the 344 sections in HAAS_VF-4.SRC:

| Category | Example Sections | Count approx | Purpose |
|----------|-----------------|--------------|---------|
| Program lifecycle | `PROGRAM_ID`, `START_OF_TAPE`, `START_OF_TAPE2`, `END_OF_TAPE`, `END_OF_TAPE_NORM`, `END_OF_TAPE_MULTI` | ~12 | Program start/end output |
| Tool change | `INIT_TOOL_CHANGE_MILL`, `SUB_TOOL_CHANGE_MILL`, `INIT_TOOL_CHANGE_MILL_RH`, `SUB_TOOL_CHANGE_MILL_RH` | ~6 | Tool change G-code output |
| Rapid/feed motion | `RAPID_MOVE_MILL`, `FEED_Z_MOVE_DOWN_MILL`, `RAPID_Z_MOVE_UP_MILL`, `FIVE_AXIS_RAPID_MOVE_MILL` | ~30 | Motion output |
| First move | `FIRST_RAPID_Z_MOVE_DOWN_MILL`, `FIRST_Z_MOVE_SAME_TOOL`, `RAPID_FROM_TOOL_CHANGE_MILL` | ~15 | First move after tool change |
| Arc motion | `ARC_MOVE_MILL`, `ARC_MOVE_XZ`, `ARC_MOVE_YZ`, `RADIUS_MOVE_MILL` | ~5 | Arc output |
| Drill cycles | `DRILLING_CYCLE`, `PECKING_CYCLE`, `TAPPING_CYCLE`, `RIGID_TAPPING_CYCLE`, `BORING_CYCLE`, `FINE_BORING_CYCLE`, `REAMING_CYCLE`, `HIGH_SPEED_PECK_CYCLE`, `CANCEL_DRILL_CYCLE`, `END_DRILL_CYCLE` | ~25 | Canned cycle output |
| Subprogram/macro | `BEG_MACRO_MILL`, `END_MACRO_MILL`, `MACRO_CALL_MILL`, `MACRO_RAPID_CALL_MILL`, `MACRO_FIRST_RAPID_CALL_MILL` | ~15 | Subroutine/subprogram handling |
| Rotation/indexing | `ROTATE_X`, `ROTATE_Y`, `ROTATE_Z`, `RESET_X`, `INDEX_POSITION`, `ROTATE_PLANE` | ~12 | 4/5 axis positioning |
| Spindle/coolant | `SPINDLE_ON`, `SPINDLE_OFF`, `COOLANT_CANCEL`, `OUTPUT_COOLANT`, `CHANGE_MILL_SPEED` | ~8 | Spindle and coolant control |
| Probing | `PROBE_SURFACE_X_TOOLPATH`, `PROBE_BORE_TOOLPATH`, `TOUCH_PROBE_ORIENT`, etc. | ~30+ | Renishaw/Haas probe cycles |
| Right angle head | `INIT_TOOL_CHANGE_MILL_RH`, `RAPID_Z_MOVE_DOWN_MILL_RH_Y`, etc. | ~20 | Attachable head support |
| Utility | `BLANK_LINE`, `OUTPUT_DWELL`, `FEED_TYPE`, `PERCENT`, `BEFORE_ATTRIBUTES`, `AFTER_ATTRIBUTES` | ~10 | General output utilities |
| Post operations | `PALLET_CHANGE_POST_OPERATION`, `ROBOT_CALL_POSTOP_OUTPUT`, `P_OUTPUT_TOOL_LIST_*` | ~15 | Post-operation handlers |
| CALC (computed) | `CALC_INITIALIZE`, `CALC_CNFG_CODES`, `CALC_INIT_CODES`, `CALC_INIT_GCODES`, `CALC_INIT_MCODES`, `CALC_DRILL_CNFG`, `CALC_START_OPERATION`, `CALC_END_OPERATION` | ~14 in SRC | Logic/configuration |
| Debug | `WARNING_ERROR`, `SPIN_SPEED_WARNING`, `DEBUG_LIB`, `DUMMY_SECTION` | ~5 | Debug and error output |

### Library File Anatomy

**Named library (`HAAS_VF-4.LIB` — machine-specific):**
- Contains machine-unique variable overrides and format settings
- `:DEFINE REG_SS=38` — register assignments
- `:ATTRNAME=...` blocks for machine-specific post tab variables (feed format, program ID, etc.)
- Takes precedence over shared library files

**Shared library (`MILL_HRS.LIB` — HRS template):**
- `:DEFINE TOOL_CHANGE=-1` through all G-code/M-code numeric constants
- `:DEFINE G_RAPID=0`, `:DEFINE G_LINE=1`, etc.
- Shared section definitions reused across all mill posts

**Probe library (`PROBE_MILL_HRS.LIB`):** Renishaw/Haas probing sections shared across all mill posts

**Headers library (`HEADERS-MILL.LIB`):** Program header comment output, startup comment sections

**Custom set library (`CUSTOM_SET.LIB`):** Set file output for CAMWorks `.set` companion file

### KIN File Anatomy

Plain numeric format with inline comments:
```
0 * 5 Axis Type 0-TABLE_TABLE,1-HEAD_HEAD,2-HEAD_TABLE,...
0 * XYZ Coordinate Type 0-Part, 1-Machine
0.000000 * Spindle Direction X
0.000000 * Spindle Direction Y
1.000000 * Spindle Direction Z
0.000000 * 1st Rotary Axis Direction X
0.000000 * 1st Rotary Axis Direction Y
-1.000000 * 1st Rotary Axis Direction Z
...
-100000.000000 * 1st Rotation Axis Limit Min
100000.000000 * 1st Rotation Axis Limit Max
-35.000000 * 2nd Rotation Axis Limit Min
110.000000 * 2nd Rotation Axis Limit Max
table table * Default Machine Simulation Name
```
Fixed-line format. Each line is: `<value> * <description>`. No section headers.

### PINF File Anatomy

Simple INI-like key=value format:
```
PostName = HAAS_VF-4
PostExtension = NC
ShortInfo = HAAS_VF-4_S.RTF
LongInfo = HAAS_VF-4_L.RTF
```
4 fields. References the RTF files for setup sheet display in UPG-2.

### LNG File Anatomy

Fixed-width table: operation name (left-padded, 70 chars) + `:XXXX:` (4-digit index):
```
program stop                                                          :0001:
optional stop                                                         :0002:
DRILLING                                                              :0005:
MILL_LACE                                                             :0019:
```
Maps operation names to numeric IDs. Used for operation type identification.

### ATR File Anatomy

Master variable registry. Header declares ID range with `:IDHIGH=19000`. Body contains variable definition blocks:
```
:ATTRID=18247
:ATTRNAME=variable name
:ATTRTYPE=SELECT|VALUE|DESCRIPTOR|POST|LIST
:ATTRVTYPE=CHARACTER|INTEGER|DECIMAL|SELECT
[other metadata]
:ATTREND
```
HRS uses ATTRID range 18000-18999. System variables use 1-5000. The VF-4 MASTER.ATR is the canonical variable registry for all HRS posts.

### Annotation Depth Recommendation (Claude's Discretion)

For Phase 2 parser needs, the catalog should document:
- **Pattern inventory** (what constructs exist and their syntax) — required for parser regex/grammar design
- **Section taxonomy** (what categories of sections exist, naming conventions) — required for structured output model
- **Variable reference syntax** (how `<VAR>`, `<G:CODE>`, `<M:CODE>` tokens work) — required for token extraction in Phase 2
- **CALC section logic patterns** (IF/THEN/ELSE, CALL(), variable assignment) — required to understand computational sections

Do NOT attempt deep semantic annotation (what each CALC section "means") in Phase 1. That is Phase 2 work. The catalog is a syntax/structure reference, not a semantic interpreter.

---

## Standard Stack

### Core Infrastructure

| Component | Version | Purpose | Decision Status |
|-----------|---------|---------|----------------|
| Docker Desktop (Windows) | Latest stable | Container runtime | LOCKED — must install first |
| Docker Compose v2 | Plugin (bundled with Desktop) | Multi-service orchestration | LOCKED — single `docker compose up` |
| PostgreSQL + pgvector | `pgvector/pgvector:pg16` image | Primary DB + vector extension | LOCKED — confirmed in prior research |
| Redis | `redis:7-alpine` | Celery broker + task queue | LOCKED |
| MinIO | `minio/minio:latest` | S3-compatible object storage | LOCKED |

### Python Dependencies (additions to scaffold)

| Package | Version | Purpose | Status |
|---------|---------|---------|--------|
| `asyncpg` | `>=0.29` | PostgreSQL async driver (replaces aiosqlite) | NEW |
| `pgvector` | `>=0.3` | SQLAlchemy Vector column type | NEW |
| `redis[asyncio]` | `>=5.0` | Async Redis client | NEW |
| `celery[redis]` | `>=5.0` | Background task queue | NEW |
| `aiobotocore` | `>=2.0` | Async S3/MinIO client | NEW |
| `python-zipfile` | stdlib | ZIP file extraction | STDLIB — no install |
| All existing | — | Keep as-is | KEEP |

**Remove from scaffold:**
- `aiosqlite>=0.20.0` — no longer needed after PostgreSQL migration

### Docker Compose Services

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
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
      minio:
        condition: service_started
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  worker:
    build: .
    env_file: .env
    depends_on:
      - postgres
      - redis
      - minio
    command: celery -A app.workers.tasks worker --loglevel=info

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
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U veripost"]
      interval: 5s
      timeout: 5s
      retries: 5

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

**Port allocation:**
| Service | Port | Notes |
|---------|------|-------|
| FastAPI | 8000 | Main API |
| PostgreSQL | 5432 | Standard port, avoid conflict with local Postgres |
| Redis | 6379 | Standard port |
| MinIO API | 9000 | S3-compatible endpoint |
| MinIO Console | 9001 | Browser UI for verifying uploads |

---

## Architecture Patterns

### Pattern 1: ZIP Upload + Package-Level Storage

**What:** Client uploads a single `.zip` file. API extracts it, validates file extensions, creates package record in PostgreSQL, stores each file in MinIO under `packages/{package_id}/{filename}`, enqueues ingestion job, returns `202 Accepted` with `job_id`.

**Why ZIP:** Decided — matches how engineers already deliver posts (both VF-4 and ST-15Y had `.zip` delivery archives). Eliminates partial-upload ambiguity.

**MinIO key structure:**
```
packages/
  {package_id}/
    HAAS_VF-4.SRC
    HAAS_VF-4.LIB
    HEADERS-MILL.LIB
    MILL_HRS.LIB
    PROBE_MILL_HRS.LIB
    CUSTOM_SET.LIB
    HAAS_VF-4.CTL
    HAAS_VF-4.KIN
    HAAS_VF-4.PINF
    HAAS_VF-4.LNG
    MASTER.ATR
```

**File validation logic:**
```python
VALID_UPG_EXTENSIONS = {".SRC", ".LIB", ".CTL", ".KIN", ".ATR", ".PINF", ".LNG"}

def validate_zip_contents(zip_bytes: bytes) -> list[str]:
    """Return list of error messages. Empty = valid."""
    errors = []
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = [n for n in zf.namelist() if not n.endswith("/")]
        if not names:
            return ["ZIP file is empty — no files found inside."]
        for name in names:
            ext = Path(name).suffix.upper()
            if ext not in VALID_UPG_EXTENSIONS:
                errors.append(
                    f"Unrecognized file type: '{name}' (extension '{ext}' is not a known UPG file type)"
                )
        src_files = [n for n in names if Path(n).suffix.upper() == ".SRC"]
        if not src_files:
            errors.append("No .SRC file found — a post processor package must contain at least one .SRC file.")
    return errors
```

### Pattern 2: Celery Skeleton with Status Tracking

**What:** Ingestion enqueues a Celery task that runs in the `worker` container. The task is a skeleton: it validates the stored files, logs each step, and marks the package status in PostgreSQL. The actual parse step is a stub that logs "parse step not yet implemented."

**Status flow:** `pending` → `validating` → `storing` → `parsing` (stub) → `ready` | `error`

**Status granularity decision (Claude's Discretion):** Use 5 statuses as listed above. Simple enough for a skeleton; detailed enough that the UI can show meaningful progress without polling ambiguity. Do NOT implement per-file progress tracking in Phase 1 — that's Phase 2 work when parsing is real.

```python
# app/workers/tasks.py
from celery import Celery

celery_app = Celery(
    "veripost",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
)

@celery_app.task(bind=True, name="ingest_package")
def ingest_package(self, package_id: str) -> dict:
    """Skeleton ingestion task. Parse step is a stub."""
    try:
        update_package_status(package_id, "validating")
        files = list_package_files_from_minio(package_id)

        update_package_status(package_id, "storing")
        # Files already in MinIO from upload handler — this step confirms integrity

        update_package_status(package_id, "parsing")
        # STUB: Phase 2 will implement real parsing here
        # For now: log file count, set stub section_count
        stub_section_count = 0

        update_package_status(package_id, "ready", section_count=stub_section_count)
        return {"package_id": package_id, "status": "ready"}
    except Exception as exc:
        update_package_status(package_id, "error", error_detail=str(exc))
        raise
```

### Pattern 3: PostgreSQL Schema (Phase 1 baseline)

**Tables needed in Phase 1:**

```sql
-- Required by Phase 1
CREATE TABLE post_packages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,           -- derived from SRC filename
    machine_type TEXT,            -- nullable in Phase 1 (Phase 3 adds machine registry)
    controller_type TEXT,         -- nullable in Phase 1
    platform TEXT NOT NULL DEFAULT 'camworks',
    status TEXT NOT NULL DEFAULT 'pending',  -- pending|validating|storing|parsing|ready|error
    error_message TEXT,           -- friendly message for display
    error_detail TEXT,            -- technical detail for expandable section
    file_count INTEGER,
    section_count INTEGER,        -- stub in Phase 1, real in Phase 2
    minio_prefix TEXT NOT NULL,   -- e.g., "packages/{id}/"
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Required by Phase 1 (files in a package)
CREATE TABLE post_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    package_id UUID NOT NULL REFERENCES post_packages(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    file_extension TEXT NOT NULL,  -- ".SRC", ".LIB", etc.
    minio_key TEXT NOT NULL,       -- full key: "packages/{pkg_id}/{filename}"
    size_bytes INTEGER,
    content_hash TEXT,             -- SHA-256 for deduplication
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- pgvector extension (required even if not used in Phase 1)
CREATE EXTENSION IF NOT EXISTS vector;
```

**Not needed in Phase 1** (add in later phases):
- `parsed_sections` table — Phase 2
- `machine_registry` table — Phase 3
- `embeddings` column — Phase 2/3

### Pattern 4: Error UX Standard

**Decision:** Friendly message + expandable technical details. This is the platform-wide error pattern.

```python
# Error response model — use everywhere
class ErrorResponse(BaseModel):
    message: str           # "Could not process your upload. The ZIP file contained unrecognized file types."
    detail: str | None     # Technical detail for expandable section; None if not applicable
    code: str | None       # Machine-readable error code
```

**Example responses:**

| Scenario | message | detail |
|----------|---------|--------|
| Unknown file extension | "This file type is not supported. VeriPost accepts: .SRC, .LIB, .CTL, .KIN, .ATR, .PINF, .LNG files." | "Rejected file: 'output.NC' (extension '.NC' is not a UPG post processor file)" |
| Empty ZIP | "The uploaded ZIP appears to be empty — no post processor files were found inside." | None |
| No SRC file | "A post processor package must include at least one .SRC source file." | "Files found: HAAS.LIB, MASTER.ATR — missing required .SRC file" |
| Ingestion job failed | "Something went wrong while processing your package. Please try uploading again." | Full stack trace / exception message |
| MinIO unreachable | "File storage is temporarily unavailable. Your upload could not be saved." | Connection error detail |

### Pattern 5: Settings Extension

```python
# app/config.py additions
class Settings(BaseSettings):
    # ... existing ...

    # Database (replace SQLite URL)
    database_url: str = "postgresql+asyncpg://veripost:veripost@postgres:5432/veripost"

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # MinIO
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "veripost"
    minio_secret_key: str = "veripost123"
    minio_bucket: str = "veripost"
    minio_use_ssl: bool = False   # False for dev, True for prod

    # Celery
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/0"
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| ZIP extraction | Custom byte stream parser | `zipfile` (Python stdlib) | Handles all ZIP variants, nested dirs, encoding; stdlib = zero deps |
| File content hashing | Manual read loop | `hashlib.sha256(content).hexdigest()` | One liner; stdlib |
| Async MinIO operations | Direct HTTP to MinIO | `aiobotocore` with S3-compatible endpoint | Handles retry, presigned URLs, multipart; MinIO is S3-compatible, same client |
| Task queue | FastAPI BackgroundTasks or threading | Celery + Redis | BackgroundTasks run in the web server process — large ZIP processing will starve request handlers |
| Database migrations | Manual `CREATE TABLE` scripts | Alembic (already in scaffold) | Version-controlled schema evolution; auto-generate from SQLAlchemy models |
| pgvector extension install | Manual SQL | Docker image `pgvector/pgvector:pg16` (includes extension) + `CREATE EXTENSION vector` in first migration | Extension is already compiled in the image |
| Connection health checks | Polling in app code | Docker Compose `healthcheck` on postgres service | Prevents API startup before DB is ready; `depends_on: condition: service_healthy` |

**Key insight:** The most expensive custom solutions to avoid in Phase 1 are (1) implementing retry/backoff for storage operations manually — `aiobotocore` handles this; and (2) using `FastAPI.BackgroundTasks` for the ingestion job — Celery is essential because ZIP extraction + MinIO upload of 10+ files will take 5-30 seconds.

---

## Common Pitfalls

### Pitfall 1: Docker Desktop Not Installed
**What goes wrong:** Every infrastructure task silently fails. `docker compose up` is not found. User can't run any services.
**Why it happens:** Docker Desktop is a separate download and install on Windows — it's not bundled with anything.
**How to avoid:** Phase 1 starts with verifying Docker Desktop installation. Confirmed: `C:\Program Files\Docker` does not exist on this machine.
**Install path:** https://docs.docker.com/desktop/setup/install/windows-install/ — requires WSL 2 backend (Windows 11 compatible, but must verify WSL 2 is enabled).

### Pitfall 2: API Starts Before PostgreSQL is Ready
**What goes wrong:** API container starts, tries to connect to PostgreSQL, gets `connection refused`, crashes. Docker Compose restarts it. Depending on timing, Alembic migrations may run before the DB accepts connections.
**Why it happens:** Docker Compose `depends_on` without `condition: service_healthy` only waits for the container to start, not for PostgreSQL to be ready to accept connections. PostgreSQL takes 2-5 seconds to initialize.
**How to avoid:** Add `healthcheck` to postgres service and use `condition: service_healthy` in api/worker `depends_on`. Already shown in the Docker Compose config above.

### Pitfall 3: MinIO Endpoint URL Confusion with aiobotocore
**What goes wrong:** MinIO returns SSL errors or connection refused when accessed from the `api` container using `aiobotocore`.
**Why it happens:** `aiobotocore` defaults to HTTPS. MinIO in dev runs HTTP. The endpoint URL must be `http://minio:9000` not `https://minio:9000`. Additionally, boto3/aiobotocore requires `endpoint_url` when not using AWS.
**How to avoid:**
```python
import aiobotocore.session

session = aiobotocore.session.get_session()
async with session.create_client(
    "s3",
    endpoint_url=f"http://{settings.minio_endpoint}",
    aws_access_key_id=settings.minio_access_key,
    aws_secret_access_key=settings.minio_secret_key,
    use_ssl=False,
) as client:
    ...
```

### Pitfall 4: Alembic Migration Runs Against Wrong Database URL
**What goes wrong:** `alembic upgrade head` connects to the SQLite database (the dev default in `config.py`) instead of PostgreSQL, creates SQLite tables, then the app tries to connect to PostgreSQL and finds no tables.
**Why it happens:** `DATABASE_URL` environment variable must be set before running Alembic, and inside Docker it points to the container hostname `postgres`, not `localhost`.
**How to avoid:** Alembic migrations run as part of the API container startup, not manually. Add to the `api` service command or create a separate init script:
```bash
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Or use a separate `migrations` one-shot service in Docker Compose.

### Pitfall 5: ZIP Files with Nested Directories
**What goes wrong:** User zips a folder rather than selecting files. ZIP contains `HAAS_VF-4/HAAS_VF-4.SRC` instead of `HAAS_VF-4.SRC`. File validation sees filenames with directory prefixes and the extension check fails or stores wrong keys in MinIO.
**Why it happens:** Windows zip behavior: "Send to > Compressed folder" on a folder creates a nested structure. Most engineers will zip a folder, not individual files.
**How to avoid:**
```python
def flatten_zip_names(zip_ref: zipfile.ZipFile) -> list[tuple[str, str]]:
    """Return list of (zip_internal_path, filename_only) pairs, skipping directories."""
    result = []
    for name in zip_ref.namelist():
        if name.endswith("/"):
            continue  # skip directories
        filename = Path(name).name  # strips directory prefix
        if filename:  # skip __MACOSX etc.
            result.append((name, filename))
    return result
```

### Pitfall 6: `_store` Dict Removal Breaks Existing Routes
**What goes wrong:** After removing `_store` from `post_service.py`, the existing `/api/v1/posts` routes (list, get, ingest) stop working. The parser route also fails because it calls `post_service.parse_post()` which references `_store`.
**Why it happens:** The scaffold's service layer is entirely `_store`-backed. Removing it without replacing all callers causes `AttributeError` or `KeyError`.
**How to avoid:** Replace `_store` with SQLAlchemy CRUD in the same commit as the PostgreSQL migration. Do not leave any code that references `_store` after the migration task.

### Pitfall 7: Library Path Resolution in ZIP Upload
**What goes wrong:** SRC file contains `:LIBRARY=C:\Posts\Library Files\MILL_HRS.LIB`. The platform tries to resolve this absolute path, which doesn't exist on the server.
**Why it happens:** UPG `:LIBRARY=` directives use absolute Windows paths from the build engineer's machine. These paths are meaningful only on the UPG compilation machine.
**How to avoid:** In Phase 1, store library paths as metadata only — do not try to resolve or validate them. Record `MILL_HRS.LIB` as a dependency name. Phase 2 parser will handle resolution by matching filenames against the package's uploaded files.

---

## Code Examples

### MinIO Bucket Initialization (startup)
```python
# Source: aiobotocore docs pattern + MinIO S3-compatibility
async def init_minio() -> None:
    """Create the veripost bucket if it doesn't exist."""
    session = aiobotocore.session.get_session()
    async with session.create_client(
        "s3",
        endpoint_url=f"http://{settings.minio_endpoint}",
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
        use_ssl=False,
    ) as client:
        try:
            await client.head_bucket(Bucket=settings.minio_bucket)
        except Exception:
            await client.create_bucket(Bucket=settings.minio_bucket)
```

### ZIP Upload Handler (FastAPI route)
```python
# Source: FastAPI UploadFile + zipfile stdlib pattern
@router.post("/packages/upload", status_code=202)
async def upload_package(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(400, detail=ErrorResponse(
            message="Please upload a .zip file containing your post processor package.",
            detail=f"Received file: '{file.filename}'",
        ).model_dump())

    content = await file.read()
    errors = validate_zip_contents(content)
    if errors:
        raise HTTPException(422, detail=ErrorResponse(
            message="The ZIP file could not be accepted.",
            detail="\n".join(errors),
        ).model_dump())

    package_id = str(uuid4())
    await store_zip_to_minio(package_id, content)
    package = await package_service.create_pending(db, package_id, file.filename)

    task = ingest_package.delay(package_id)
    return {"package_id": package_id, "job_id": task.id, "status": "pending"}
```

### Alembic First Migration
```python
# alembic/versions/001_initial_schema.py
def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "post_packages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("machine_type", sa.Text),
        sa.Column("controller_type", sa.Text),
        sa.Column("platform", sa.Text, nullable=False, server_default="camworks"),
        sa.Column("status", sa.Text, nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text),
        sa.Column("error_detail", sa.Text),
        sa.Column("file_count", sa.Integer),
        sa.Column("section_count", sa.Integer),
        sa.Column("minio_prefix", sa.Text, nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "post_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("package_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("post_packages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filename", sa.Text, nullable=False),
        sa.Column("file_extension", sa.Text, nullable=False),
        sa.Column("minio_key", sa.Text, nullable=False),
        sa.Column("size_bytes", sa.Integer),
        sa.Column("content_hash", sa.Text),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
    )
```

---

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|-----------------|--------|
| SQLite in dev | PostgreSQL from day 1 (via Docker) | pgvector works locally; no prod/dev schema divergence |
| In-memory `_store` | PostgreSQL + SQLAlchemy async | Data persists across restarts; multi-worker compatible |
| `FastAPI.BackgroundTasks` for file ops | Celery + Redis | Prevents request handler starvation on large ZIP uploads |
| Filesystem storage | MinIO object storage | S3-compatible; prod swap is env-var only |
| Manual `docker run` per service | `docker compose up` | One command; reproducible across machines |
| Monolithic service container | Separate `api` + `worker` containers | Worker can scale independently; parse jobs don't block HTTP |

**Deprecated in this project:**
- `aiosqlite` — remove from `pyproject.toml` after asyncpg is added
- `_store: dict` in `post_service.py` — replace entirely, no backwards compat needed (data is disposable)
- SQLite `DATABASE_URL` default — replace with PostgreSQL URL pointing to Docker service

---

## Open Questions

1. **WSL 2 on this machine**
   - What we know: Windows 11 Enterprise supports WSL 2. Docker Desktop requires WSL 2 backend.
   - What's unclear: Whether WSL 2 is currently enabled on the user's machine.
   - Recommendation: First task of Phase 1 install plan should verify WSL 2 status (`wsl --status` in PowerShell). If not enabled, enable it before Docker Desktop install. The install plan should include this step.

2. **Corpus sourcing for 20+ file requirement**
   - What we know: Only 2 complete packages exist locally in `C:\CAM CONTENT`. Need 18+ more.
   - What's unclear: How to access the SharePoint corpus to download additional packages. User did not specify.
   - Recommendation: Plan should include a corpus collection task where the user downloads representative packages from SharePoint for Fanuc and Mori Seiki controllers. The plan should specify what to download (target: 7 packages per controller type, all 7 file types, mix of Mill/MillTurn/Lathe).

3. **Celery worker Windows compatibility**
   - What we know: Celery 5.x on Windows has known limitations (prefork pool not supported; use `solo` or `eventlet` pool). Inside Docker containers (Linux), this is not an issue.
   - What's unclear: Whether any development-time Celery usage outside Docker is expected.
   - Recommendation: Run Celery exclusively inside Docker (the `worker` service). Do not document or support running the worker outside Docker on Windows. This is consistent with the single-command philosophy.

4. **MinIO bucket policy**
   - What we know: MinIO defaults to private bucket access.
   - What's unclear: Whether the frontend will fetch files directly from MinIO (presigned URLs) or through the FastAPI proxy.
   - Recommendation (for Phase 1): Route all file access through FastAPI. This is simpler to implement for the skeleton. Phase 3 (Repository) can switch to presigned URLs for large file downloads to avoid proxying bytes through the API.

---

## Sources

### Primary (HIGH confidence)
- Direct file inspection: `c:/CAM CONTENT/Post Processors/Customers - HRS/Ducommun Labarge Technologies/Mill/HAAS_VF-4/HAAS_VF-4.SRC` — 5,966 lines, complete SRC structure observed
- Direct file inspection: `c:/CAM CONTENT/Post Processors/Customers - HRS/Ducommun Labarge Technologies/Mill/HAAS_VF-4/HAAS_VF-4.LIB`, `MILL_HRS.LIB`, `HEADERS-MILL.LIB` — library structure confirmed
- Direct file inspection: `HAAS_VF-4.CTL`, `HAAS_VF-4.KIN`, `HAAS_VF-4.PINF`, `HAAS_VF-4.LNG`, `MASTER.ATR` — all 7 file types observed
- Direct file inspection: `c:/CAM CONTENT/Post Processors/Customers - HRS/Ducommun Labarge Technologies/MillTurn/HAAS_ST-15Y/HAAS_ST-15Y.SRC` — 745 sections in MillTurn variant
- Directory scan: `c:/CAM CONTENT/**/*` — complete file census via Glob; confirmed extensions, package count
- Codebase inspection: `c:/VeriPost/docker-compose.yml`, `c:/VeriPost/pyproject.toml`, `c:/VeriPost/app/config.py`, `c:/VeriPost/app/db/database.py`, `c:/VeriPost/app/services/post_service.py` — confirmed current scaffold state
- Docker Desktop install status: `C:/Program Files/Docker` not found — confirmed not installed
- Prior project research: `.planning/research/STACK.md`, `.planning/research/ARCHITECTURE.md`, `.planning/research/PITFALLS.md` — HIGH confidence foundation

### Secondary (MEDIUM confidence)
- Training knowledge (August 2025): Docker Compose v2 healthcheck syntax, Celery 5 + Redis broker pattern, aiobotocore MinIO endpoint URL behavior, Alembic migration patterns — well-established patterns, verified against scaffold structure

### Tertiary (LOW confidence)
- WSL 2 status on user's machine — not verified; flagged as open question
- SharePoint corpus size and controller type distribution — inferred from folder structure and machine documentation; actual post counts not verified

---

## Metadata

**Confidence breakdown:**
- Infrastructure stack: HIGH — confirmed against scaffold, prior research, and established patterns
- UPG corpus scan: MEDIUM — 2 complete packages observed; patterns are clear but more files would increase confidence
- Corpus extension list: HIGH — all 7 types observed; Glob scan found no unknown UPG extensions
- Controller type recommendation: MEDIUM — HAAS confirmed; Fanuc and Mori Seiki inferred from machine documentation, not post files
- Docker Desktop status: HIGH — confirmed not installed via filesystem check

**Research date:** 2026-02-19
**Valid until:** 2026-03-19 (infrastructure patterns are stable; corpus findings are limited to local files and should be updated when SharePoint packages are downloaded)
