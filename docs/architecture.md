# VeriPost Architecture

## Design Principles

1. **AI as Enabler** — The copilot assists engineers; it doesn't make autonomous decisions about machine-critical output.
2. **Platform Extensible** — Parser interface allows adding new CAM platforms without touching core logic.
3. **Corpus-Driven** — Parsing accuracy improves as the post processor corpus grows.
4. **API-First** — All functionality exposed via REST; UI is a separate concern.

## Component Overview

### Parsing Engine
Each CAM platform has a dedicated parser implementing `BaseParser`. The registry auto-detects file format or routes by explicit platform name. Parsers extract sections, variables, and structure into a normalized `ParsedPost` model.

### AI Copilot
The copilot wraps the Anthropic API with domain-specific system prompts. It receives parsed post processor context and answers engineer questions about behavior, modifications, and troubleshooting. Context is truncated to stay within token limits.

### Service Layer
`PostService` orchestrates ingestion, storage, parsing, and retrieval. Currently uses an in-memory store for rapid prototyping — designed for easy swap to SQLAlchemy-backed persistence.

### Database
SQLAlchemy async with aiosqlite (dev) / PostgreSQL (prod). Schema managed via Alembic migrations.

## Validation Roadmap (8-Week Plan)

| Week | Focus                          |
|------|--------------------------------|
| 1-2  | Corpus collection & cataloging |
| 3-4  | Parsing experiments & accuracy |
| 5-6  | AI capability validation       |
| 7-8  | UX prototyping with CAM engineers |
