"""Service layer for post processor package operations.

All data flows through PostgreSQL (via SQLAlchemy async) and MinIO
(via StorageService). The in-memory _store is eliminated.
"""

import hashlib
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import PostFile, PostPackage
from app.services.storage import storage


async def list_packages(db: AsyncSession) -> list[PostPackage]:
    """List all packages, newest first, with files eagerly loaded."""
    result = await db.execute(
        select(PostPackage)
        .options(selectinload(PostPackage.files))
        .order_by(PostPackage.created_at.desc())
    )
    return list(result.scalars().all())


async def get_package(db: AsyncSession, package_id: uuid.UUID) -> PostPackage | None:
    """Get a package by ID with its files eagerly loaded."""
    result = await db.execute(
        select(PostPackage)
        .where(PostPackage.id == package_id)
        .options(selectinload(PostPackage.files))
    )
    return result.scalar_one_or_none()


async def create_package(
    db: AsyncSession, name: str, platform: str = "camworks"
) -> PostPackage:
    """Create a new package record in the database."""
    pkg_id = uuid.uuid4()
    package = PostPackage(
        id=pkg_id,
        name=name,
        platform=platform,
        minio_prefix=f"packages/{pkg_id}/",
        status="pending",
    )
    db.add(package)
    await db.commit()
    await db.refresh(package)
    return package


async def add_file_to_package(
    db: AsyncSession, package: PostPackage, filename: str, data: bytes
) -> PostFile:
    """Upload a file to MinIO and record it in the database."""
    ext = "." + filename.rsplit(".", 1)[-1] if "." in filename else ""
    minio_key = f"{package.minio_prefix}{filename}"
    content_hash = hashlib.sha256(data).hexdigest()

    await storage.upload_file(minio_key, data)

    file_record = PostFile(
        package_id=package.id,
        filename=filename,
        file_extension=ext.upper(),
        minio_key=minio_key,
        size_bytes=len(data),
        content_hash=content_hash,
    )
    db.add(file_record)
    await db.commit()
    await db.refresh(file_record)
    return file_record


async def update_package_status(
    db: AsyncSession,
    package_id: uuid.UUID,
    status: str,
    error_message: str | None = None,
    error_detail: str | None = None,
) -> None:
    """Update a package's processing status."""
    package = await get_package(db, package_id)
    if package:
        package.status = status
        if error_message:
            package.error_message = error_message
        if error_detail:
            package.error_detail = error_detail
        await db.commit()
