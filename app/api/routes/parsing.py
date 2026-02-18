"""Parsing and AI analysis endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.ai.copilot import Copilot
from app.services.post_service import PostService

router = APIRouter(prefix="/parsing", tags=["parsing"])

service = PostService()
copilot = Copilot()


class AnalyzeRequest(BaseModel):
    post_id: str
    question: str | None = None


class AnalyzeResponse(BaseModel):
    post_id: str
    platform: str
    summary: str
    sections: list[str]
    ai_analysis: str | None = None


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_post(request: AnalyzeRequest):
    """Parse and analyze a post processor with optional AI copilot question."""
    post = await service.get_post(request.post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post processor not found")

    parsed = await service.parse_post(request.post_id)

    ai_analysis = None
    if request.question:
        ai_analysis = await copilot.ask(
            context=parsed.raw_content,
            question=request.question,
            platform=post.platform,
        )

    return AnalyzeResponse(
        post_id=request.post_id,
        platform=post.platform,
        summary=parsed.summary,
        sections=parsed.section_names,
        ai_analysis=ai_analysis,
    )
