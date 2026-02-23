"""Post processor package management endpoints.

All data is persisted in PostgreSQL and MinIO. The in-memory _store
is eliminated. Routes use dependency-injected DB sessions.
"""

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models.post_processor import (
    PackageListResponse,
    PackageResponse,
)
from app.db.database import get_db
from app.services import post_service

router = APIRouter(prefix="/posts", tags=["post-processors"])


@router.get("/", response_model=PackageListResponse)
async def list_packages(db: AsyncSession = Depends(get_db)):
    """List all registered post processor packages."""
    packages = await post_service.list_packages(db)
    return PackageListResponse(
        packages=[PackageResponse.model_validate(p) for p in packages],
        count=len(packages),
    )


@router.get("/{package_id}", response_model=PackageResponse)
async def get_package(package_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get details for a specific post processor package with its files."""
    package = await post_service.get_package(db, package_id)
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    return PackageResponse.model_validate(package)


@router.post("/upload", response_model=PackageResponse, status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    platform: str = "camworks",
    db: AsyncSession = Depends(get_db),
):
    """Upload a single post processor file.

    Creates a package, stores the file in MinIO, and records metadata
    in PostgreSQL. This is a simple single-file placeholder; full ZIP
    upload is implemented in Plan 01-03.
    """
    filename = file.filename or "unknown"
    content = await file.read()

    # Create package record
    name = filename.rsplit(".", 1)[0] if "." in filename else filename
    package = await post_service.create_package(db, name=name, platform=platform)

    # Store file in MinIO and record in DB
    await post_service.add_file_to_package(db, package, filename, content)

    # Update file count
    package.file_count = 1
    package.status = "uploaded"
    await db.commit()
    await db.refresh(package)

    # Re-fetch with files loaded for response
    package = await post_service.get_package(db, package.id)
    return PackageResponse.model_validate(package)
