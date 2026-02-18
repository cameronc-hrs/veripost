"""Post processor management endpoints."""

from fastapi import APIRouter, UploadFile, File, HTTPException
from app.core.models.post_processor import (
    PostProcessorResponse,
    PostProcessorListResponse,
)
from app.services.post_service import PostService

router = APIRouter(prefix="/posts", tags=["post-processors"])

service = PostService()


@router.get("/", response_model=PostProcessorListResponse)
async def list_post_processors():
    """List all registered post processors."""
    posts = await service.list_posts()
    return PostProcessorListResponse(posts=posts, count=len(posts))


@router.get("/{post_id}", response_model=PostProcessorResponse)
async def get_post_processor(post_id: str):
    """Get details for a specific post processor."""
    post = await service.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post processor not found")
    return post


@router.post("/upload", response_model=PostProcessorResponse)
async def upload_post_processor(
    file: UploadFile = File(...),
    platform: str = "camworks",
):
    """Upload a post processor file for analysis."""
    content = await file.read()
    result = await service.ingest_post(
        filename=file.filename or "unknown",
        content=content,
        platform=platform,
    )
    return result
