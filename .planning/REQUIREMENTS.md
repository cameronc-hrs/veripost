# Requirements: VeriPost

**Defined:** 2026-02-18
**Core Value:** AI copilot that helps CAM engineers understand, author, and manage CNC post processor source code — turning customer requests into compiled posts and managing them through their lifecycle.

## v1 Requirements

Requirements for 8-week feasibility validation. Each maps to roadmap phases.

### Repository

- [ ] **REPO-01**: Engineer can upload a post processor file package (.SRC, .LIB, .CTL, .KIN, .PINF, .LNG, .ATR) as a grouped unit
- [ ] **REPO-02**: Engineer can browse all uploaded post processor packages with name, machine, and status visible
- [ ] **REPO-03**: Engineer can download any file or complete package with original bytes intact
- [ ] **REPO-04**: Engineer can tag a post package with machine name, controller type, and CAM platform
- [ ] **REPO-05**: Engineer can track upload-based version history (who uploaded what, when)

### Parsing

- [ ] **PARS-01**: System can parse CAMWorks .SRC files into structured sections (subroutines, conditional blocks, operation handlers)
- [ ] **PARS-02**: System can parse .LIB files into structured variable definitions and library includes
- [ ] **PARS-03**: Parser extracts meaningful structure from 80%+ of real corpus files (accuracy gate)
- [ ] **PARS-04**: Engineer can view parsed structure alongside raw source in a syntax-aware code viewer

### AI Copilot

- [ ] **AI-01**: Engineer can select a section of post processor code and receive a plain-English explanation of what it does on the machine
- [ ] **AI-02**: AI explanation references machine-specific context (controller dialect, known quirks) when available
- [ ] **AI-03**: AI explanations are accurate enough that engineers without UPG expertise can understand post logic (validated by 2-5 HRS engineers)
- [ ] **AI-04**: AI copilot can summarize customer-specific customizations in a post relative to the base HRS template

### Authoring & Management

- [ ] **AUTH-01**: Engineer can take a customer's custom requirements and identify which sections of existing source need modification
- [ ] **AUTH-02**: AI copilot can suggest specific code changes to apply customer requirements to a base post template
- [ ] **AUTH-03**: Engineer can review, edit, and apply AI-suggested changes through the code viewer
- [ ] **AUTH-04**: System tracks the relationship between customer requirements and the source changes that fulfilled them

### Authentication

- [ ] **ACCT-01**: Engineer can log in via SSO/OAuth (Azure AD or equivalent HRS identity provider)
- [ ] **ACCT-02**: Only authenticated HRS staff can access the platform

## v2 Requirements

Deferred to post-feasibility. Tracked but not in current roadmap.

### Search

- **SRCH-01**: Engineer can search across all post content by keyword, variable name, or section name (full-text)
- **SRCH-02**: Engineer can find posts semantically similar to a given post or section (pgvector)

### Advanced AI

- **AI-05**: AI can structurally compare two post processors and explain meaningful differences
- **AI-06**: AI can detect risky or non-standard logic patterns in post code
- **AI-07**: AI can auto-generate documentation from post source (supported operations, limits, quirks)
- **AI-08**: AI can suggest fixes based on patterns from past issue resolutions

### Version Control

- **VER-01**: Git-backed version control per post package with full diff view
- **VER-02**: UPG-semantic diff showing variable and section changes, not just text diffs

### Machine Intelligence

- **MACH-01**: Machine registry with controller dialects, known quirks, and recommended patterns
- **MACH-02**: Variable cross-reference showing where ATR variables are used across all posts
- **MACH-03**: Post family grouping showing shared library dependencies and impact analysis

### Analytics

- **ANLY-01**: Dashboard showing post processor corpus trends (uploads, modifications, issues by machine type)
- **ANLY-02**: Ingest HRS post processor support data for analytics on common requests and issues

## Out of Scope

| Feature | Reason |
|---------|--------|
| AI autonomously writing complete post processors | Safety-critical output requires human authorship and validation. AI suggests, engineer decides. |
| DELMIA NC parser (.pptable + CLDATA) | Future platform expansion. CAMWorks UPG only for v1. |
| Mastercam parser (.PST files) | Future platform expansion. CAMWorks UPG only for v1. |
| Direct CNC machine connection | VeriPost manages source, not machine deployment. Engineers use existing DNC workflows. |
| SOLIDWORKS CAM plugin | Separate SDK/licensing/release cycle. REST API enables future plugin development. |
| Real-time collaborative editing | Posts are owned by one engineer at a time. File locking sufficient. |
| SaaS multi-tenancy | Internal tool first. Tenant-aware data model, but no tenant management layer until validated. |
| Automated post testing/simulation | Requires UPG runtime or CAMWorks installation. Separate tool (VERICUT territory). |
| Mobile app | Web-first. Responsive layout sufficient for occasional non-desktop use. |
| WYSIWYG post editor | UPG is a domain language — form-based editing would require implementing full UPG language model. Monaco + AI copilot is the approach. |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| REPO-01 | — | Pending |
| REPO-02 | — | Pending |
| REPO-03 | — | Pending |
| REPO-04 | — | Pending |
| REPO-05 | — | Pending |
| PARS-01 | — | Pending |
| PARS-02 | — | Pending |
| PARS-03 | — | Pending |
| PARS-04 | — | Pending |
| AI-01 | — | Pending |
| AI-02 | — | Pending |
| AI-03 | — | Pending |
| AI-04 | — | Pending |
| AUTH-01 | — | Pending |
| AUTH-02 | — | Pending |
| AUTH-03 | — | Pending |
| AUTH-04 | — | Pending |
| ACCT-01 | — | Pending |
| ACCT-02 | — | Pending |

**Coverage:**
- v1 requirements: 19 total
- Mapped to phases: 0
- Unmapped: 19

---
*Requirements defined: 2026-02-18*
*Last updated: 2026-02-18 after initial definition*
