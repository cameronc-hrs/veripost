# Phase 1: Foundation - Context

**Gathered:** 2026-02-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Dev environment with real persistence (PostgreSQL + pgvector, Redis, MinIO), async ingestion infrastructure (Celery), and a documented UPG corpus catalog from 20+ real files. This phase delivers zero v1 requirements — it is pure infrastructure that unblocks Phases 2-5. Discussion clarifies implementation within this boundary.

</domain>

<decisions>
## Implementation Decisions

### UPG corpus & catalog
- Large, diverse corpus in C:\CAM CONTENT (thousands of files, many controller types, multiple CAM platforms)
- Select top 3 most common controller types for the initial 20+ file corpus — Claude to scan C:\CAM CONTENT to identify them by file count
- Good coverage across all three controller types, not just one
- Claude to also scan C:\CAM CONTENT for all file extensions present (user unsure if the 7 known types are exhaustive)

### Dev workflow
- User is not a DevOps person — follows instructions but won't troubleshoot infrastructure issues independently
- Docker Desktop may or may not be installed; verify and install if needed as part of Phase 1
- Setup must be dead simple: single command to start everything
- Small team (1-2 other developers) — setup must be reproducible across machines
- Claude owns all infrastructure decisions (tooling, configuration, containerization approach)

### Data migration
- All existing SQLite and _store data is disposable — fresh start with PostgreSQL
- MinIO file storage organized by package (each package gets its own prefix/folder)
- Validate file types at upload — only accept known UPG file extensions; reject unrecognized types
- Full list of valid extensions to be determined by scanning C:\CAM CONTENT

### Ingestion job
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

</decisions>

<specifics>
## Specific Ideas

- C:\CAM CONTENT is the source of truth for real UPG files — scan it to identify top 3 controller types and all file extensions
- User explicitly wants package-level organization in storage, not flat
- Error UX pattern: "friendly message + expandable details" should be the standard across the platform, not just ingestion

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-foundation*
*Context gathered: 2026-02-19*
