"""Service layer for post processor operations."""

import uuid
from datetime import datetime, timezone

from app.core.models.post_processor import ParsedPost, PostProcessorResponse
from app.core.parsing import get_parser, detect_parser


# In-memory store for development — replace with DB in production
_store: dict[str, dict] = {}


class PostService:
    """Business logic for post processor management."""

    async def list_posts(self) -> list[PostProcessorResponse]:
        return [PostProcessorResponse(**data) for data in _store.values()]

    async def get_post(self, post_id: str) -> PostProcessorResponse | None:
        data = _store.get(post_id)
        return PostProcessorResponse(**data) if data else None

    async def ingest_post(
        self,
        filename: str,
        content: bytes,
        platform: str,
    ) -> PostProcessorResponse:
        """Ingest and register a new post processor file."""
        post_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        text = content.decode("utf-8", errors="replace")

        # Auto-detect platform if possible
        detected = detect_parser(text)
        if detected:
            platform = detected.platform

        record = {
            "id": post_id,
            "filename": filename,
            "platform": platform,
            "machine_type": None,
            "controller": None,
            "description": None,
            "created_at": now,
            "updated_at": now,
            "section_count": 0,
            "status": "uploaded",
        }

        _store[post_id] = record
        return PostProcessorResponse(**record)

    async def parse_post(self, post_id: str) -> ParsedPost:
        """Parse a previously uploaded post processor."""
        record = _store.get(post_id)
        if not record:
            raise ValueError(f"Post {post_id} not found")

        parser = get_parser(record["platform"])

        # In production, retrieve content from storage/DB
        # For now, return a placeholder
        return ParsedPost(
            post_id=post_id,
            raw_content="[content would be loaded from storage]",
            summary="Parse from stored content not yet implemented",
        )
