# VeriPost

## What This Is

A web-based post processor automation platform for managing CNC post processors in the CAMWorks/SOLIDWORKS CAM ecosystem. VeriPost turns handcrafted text files (.SRC, .LIB, .CTL) — currently managed through folders, emails, and tribal knowledge — into a centralized, versioned, searchable, AI-augmented system. Built for HawkRidge Systems CAM support engineers, with future expansion to external customers and other CAM platforms (DELMIA, Mastercam).

## Core Value

An AI copilot that can explain post processor logic in plain English — so CAM engineers can understand, modify, and troubleshoot posts without relying on tribal knowledge or expensive machine time.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Centralized repository with Git-based version control for post processor file families (.SRC, .LIB, .CTL, .KIN, .PINF, .LNG, .ATR)
- [ ] Custom parser that converts CAMWorks .SRC/.LIB files into a structured, queryable data model
- [ ] Machine registry linking posts to machine metadata, controller dialects, and known quirks
- [ ] AI-powered "explain this code" — point at a section and get plain English explanation of what it does on the machine
- [ ] AI-powered structural comparison between two post processors
- [ ] AI-powered risky logic detection in post processor code
- [ ] Auto-generated documentation from post processor source
- [ ] Full-text and semantic search across the post corpus
- [ ] Web-based code viewer with syntax awareness for UPG format
- [ ] Upload and ingestion pipeline for post processor file packages

### Out of Scope

- DELMIA NC parser (.pptable + CLDATA) — future platform expansion, not v1
- Mastercam parser (.PST files) — future platform expansion, not v1
- AI writing/modifying post processor code autonomously — AI explains and assists, doesn't author
- Mobile app — web-first, responsive later
- Real-time collaborative editing — single-user authoring is sufficient for validation
- Direct CNC machine integration — platform operates on post source files, not machine connections
- SaaS multi-tenancy — internal tool first, commercialization architecture deferred

## Context

**Domain:** CNC post processors are the critical translators between CAM software (SOLIDWORKS CAM/CAMWorks) and CNC machines. They are authored in HCL's Universal Post Generator (UPG) format — a proprietary language with .SRC (source logic), .LIB (modular libraries), .CTL (control/config), .KIN (machine kinematics), .PINF (metadata), .LNG (language strings), and .ATR (variable definitions) files.

**Corpus:** HawkRidge Systems has thousands of customer-specific post processor packages on SharePoint. Each package follows a consistent structure: machine-specific source files plus shared HRS template libraries (HEADERS, PROBE, MILL/MILLTURN patterns). The `C:\CAM CONTENT` directory contains sample packages (Ducommun Labarge Technologies — HAAS VF-4 Mill, HAAS ST-15Y MillTurn), 40+ usage guides, machine documentation (Doosan, Mori Seiki), and HCL intake forms.

**File characteristics:** .SRC files are large (~294KB for a single machine post) with complex logic including revision history, conditional blocks, subroutine calls, and variable references. .LIB files are modular and reusable. .ATR files define 600+ variables with type information. The HRS template system uses standardized variable naming (ID range 18000-18999) across all posts.

**Existing code:** A scaffolded FastAPI backend exists with parser interfaces and AI copilot stubs, but logic is placeholder — no real parsing or AI integration has been tested against actual post files. This is a fresh start using the scaffold as reference only.

**UPG-2:** The current editor tool (October 2025 release) is a dated GUI with no version control, search, or AI capabilities. VeriPost replaces the workflow around UPG, not UPG itself.

**Validation approach:** 8-week feasibility-first plan. Each phase has a hard success gate. MVP follows only if feasibility is confirmed. A small team of 2-5 CAM engineers at HRS will provide feedback and validation. Deployment infrastructure is flexible — determined by feasibility phase needs.

## Constraints

- **Tech stack**: Next.js/React/TypeScript frontend, Python/FastAPI backend, PostgreSQL + pgvector, S3/MinIO file storage, Redis caching/queues, Anthropic Claude API
- **Timeline**: 8-week feasibility validation before any MVP commitment
- **Parser scope**: CAMWorks UPG format only for v1 — parser depth (section-level vs AST) to be determined by research and experimentation in weeks 2-4
- **AI dependency**: Platform must be useful with AI turned off — repository, parser, versioning, and search stand alone
- **Users**: HRS internal CAM engineers (2-5 testers) for validation phase
- **Philosophy**: AI as enabler, not product. AI compresses time and raises quality but does not replace CAM experts or eliminate validation
- **Corpus access**: Primary corpus on SharePoint, sample files available locally at `C:\CAM CONTENT`

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Fresh start over evolving existing scaffold | Existing code is stubs only; full-stack architecture (Next.js + FastAPI + pgvector) requires clean foundation | — Pending |
| AI usefulness as primary validation target | If AI can't explain post logic usefully, the platform loses its differentiator. Parser and search are table stakes. | — Pending |
| Feasibility-first with hard gates | Post processor domain is specialized; must prove core capabilities before committing to MVP | — Pending |
| CAMWorks UPG format only for v1 | Deepest corpus available, most expertise at HRS, proves the model before expanding | — Pending |

---
*Last updated: 2026-02-18 after initialization*
