# VeriPost

An AI Post Processor copilot for creating and maintaining custom CNC posts.

> **Philosophy:** AI as enabler, not product. VeriPost augments CAM engineers' expertise — it doesn't replace it.

## Architecture

```
app/
├── main.py                  # FastAPI entry point
├── config.py                # Environment-based settings
├── api/routes/              # REST endpoints
│   ├── health.py            # Health check
│   ├── posts.py             # Post processor CRUD
│   └── parsing.py           # Parse & AI analysis
├── core/
│   ├── parsing/             # Platform-specific parsers
│   │   ├── base.py          # Abstract parser interface
│   │   ├── camworks.py      # CAMWorks UPG format
│   │   ├── delmia.py        # DELMIA (placeholder)
│   │   └── mastercam.py     # Mastercam (placeholder)
│   ├── ai/
│   │   ├── copilot.py       # Claude-powered assistant
│   │   └── prompts.py       # System prompts
│   └── models/
│       └── post_processor.py  # Domain models
├── services/
│   └── post_service.py      # Business logic
└── db/
    └── database.py          # SQLAlchemy async setup

corpus/                      # Post processor file corpus (by platform)
tests/                       # pytest suite
docs/                        # Architecture & design docs
```

## Supported Platforms

| Platform   | Status       | Format        |
|------------|-------------|---------------|
| CAMWorks   | In Progress | UPG (.ctl)    |
| DELMIA     | Planned     | TBD           |
| Mastercam  | Planned     | .mcpost/.pst  |

## Quick Start

```bash
# Clone
git clone https://github.com/cameronc-hrs/veripost.git
cd veripost

# Setup
cp .env.example .env          # Configure your API key
pip install -e ".[dev]"        # Install with dev dependencies

# Run
uvicorn app.main:app --reload

# Test
pytest
```

## Docker

```bash
docker compose up
```

API available at `http://localhost:8000`. Docs at `http://localhost:8000/docs`.

## API Endpoints

| Method | Path                    | Description                      |
|--------|------------------------|----------------------------------|
| GET    | `/health`              | Health check                     |
| GET    | `/api/v1/posts/`       | List all post processors         |
| GET    | `/api/v1/posts/{id}`   | Get post processor details       |
| POST   | `/api/v1/posts/upload` | Upload a post processor file     |
| POST   | `/api/v1/parsing/analyze` | Parse & analyze with AI copilot |
