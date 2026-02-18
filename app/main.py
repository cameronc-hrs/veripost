"""VeriPost — AI Post Processor Copilot."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, posts, parsing
from app.config import get_settings
from app.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup and shutdown lifecycle."""
    settings = get_settings()
    await init_db()
    print(f"VeriPost started in {settings.app_env} mode")
    yield
    print("VeriPost shutting down")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="VeriPost",
        description="AI Post Processor copilot for creating and maintaining custom CNC posts.",
        version="0.1.0",
        debug=settings.is_dev,
        lifespan=lifespan,
    )

    # CORS — loosen in dev, lock down in production
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.is_dev else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register route modules
    app.include_router(health.router)
    app.include_router(posts.router, prefix="/api/v1")
    app.include_router(parsing.router, prefix="/api/v1")

    return app


app = create_app()
