"""Post processor domain models."""

from datetime import datetime
from pydantic import BaseModel, Field


class PostProcessorBase(BaseModel):
    filename: str
    platform: str  # camworks | delmia | mastercam
    machine_type: str | None = None
    controller: str | None = None
    description: str | None = None


class PostProcessorResponse(PostProcessorBase):
    id: str
    created_at: datetime
    updated_at: datetime
    section_count: int = 0
    status: str = "uploaded"  # uploaded | parsed | validated | error


class PostProcessorListResponse(BaseModel):
    posts: list[PostProcessorResponse]
    count: int


class ParsedPost(BaseModel):
    """Result of parsing a post processor file."""

    post_id: str
    raw_content: str
    summary: str = ""
    section_names: list[str] = Field(default_factory=list)
    variables: dict[str, str] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
