"""Parsing and AI analysis endpoints.

Stub returning 501 until Phase 2 implements the UPG parser.
"""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/parsing", tags=["parsing"])


@router.post("/analyze")
async def analyze_post():
    """Parse and analyze a post processor — not yet implemented."""
    raise HTTPException(
        status_code=501,
        detail="Parsing not implemented. Available in Phase 2.",
    )
