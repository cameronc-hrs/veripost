"""Pydantic response schemas for post processor API.

Aligned with SQLAlchemy ORM models in app.db.models.
Uses from_attributes for direct ORM-to-response serialization.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class FileResponse(BaseModel):
    """Response schema for a single file within a package."""

    id: UUID
    filename: str
    file_extension: str
    size_bytes: int | None = None

    model_config = {"from_attributes": True}


class PackageResponse(BaseModel):
    """Response schema for a post processor package."""

    id: UUID
    name: str
    machine_type: str | None = None
    controller_type: str | None = None
    platform: str
    status: str
    error_message: str | None = None
    file_count: int | None = None
    section_count: int | None = None
    created_at: datetime
    updated_at: datetime
    files: list[FileResponse] = []

    model_config = {"from_attributes": True}


class PackageListResponse(BaseModel):
    """Response schema for listing packages."""

    packages: list[PackageResponse]
    count: int


class ErrorResponse(BaseModel):
    """Platform-wide error response: friendly message + expandable detail."""

    message: str
    detail: str | None = None
    code: str | None = None


class StatusResponse(BaseModel):
    """Response schema for package ingestion status polling."""

    package_id: str
    status: str
    error_message: str | None = None
    error_detail: str | None = None
    file_count: int | None = None
    section_count: int | None = None
