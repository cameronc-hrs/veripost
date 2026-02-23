"""Service layer for post processor package operations.

All data flows through PostgreSQL (via SQLAlchemy async) and MinIO
(via StorageService). The in-memory _store is eliminated.
"""

import hashlib
import io
import uuid
import zipfile
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import VALID_UPG_EXTENSIONS
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


def validate_zip_contents(content: bytes) -> list[str]:
    """Validate that a ZIP archive contains valid UPG post processor files.

    Returns a list of error strings. Empty list means the ZIP is valid.

    Handles:
    - Bad ZIP files
    - Empty ZIPs
    - Unrecognized file extensions (checked case-insensitively)
    - Missing .SRC file requirement
    - Nested directories (flattened -- only filename matters)
    - __MACOSX entries (skipped)
    """
    errors: list[str] = []
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            names: list[tuple[str, str]] = []
            for name in zf.namelist():
                # Skip directory entries and macOS resource forks
                if name.endswith("/") or "__MACOSX" in name:
                    continue
                filename = Path(name).name
                if filename:
                    names.append((name, filename))

            if not names:
                return ["ZIP file is empty -- no files found inside."]

            for zip_path, filename in names:
                ext = Path(filename).suffix.upper()
                if ext not in VALID_UPG_EXTENSIONS:
                    errors.append(
                        f"Unrecognized file type: '{filename}' "
                        f"(extension '{ext}' is not a known UPG file type)"
                    )

            src_files = [fn for _, fn in names if Path(fn).suffix.upper() == ".SRC"]
            if not src_files:
                errors.append(
                    "No .SRC file found -- a post processor package must "
                    "contain at least one .SRC file."
                )
    except zipfile.BadZipFile:
        return ["The uploaded file is not a valid ZIP archive."]

    return errors


def extract_zip_files(content: bytes) -> list[tuple[str, bytes]]:
    """Extract files from a ZIP archive, flattening nested directories.

    Returns list of (filename, file_bytes) tuples.
    Skips directory entries and __MACOSX resource forks.
    """
    result: list[tuple[str, bytes]] = []
    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        for name in zf.namelist():
            if name.endswith("/") or "__MACOSX" in name:
                continue
            filename = Path(name).name
            if filename:
                result.append((filename, zf.read(name)))
    return result


async def create_package_with_files(
    db: AsyncSession,
    package_id: uuid.UUID,
    name: str,
    files: list[tuple[str, bytes]],
) -> PostPackage:
    """Create a PostPackage and its PostFile records, upload files to MinIO.

    All operations happen in a single transaction. Files are uploaded to
    MinIO under packages/{package_id}/{filename} (flattened, no dirs).
    """
    minio_prefix = f"packages/{package_id}/"

    package = PostPackage(
        id=package_id,
        name=name,
        platform="camworks",
        minio_prefix=minio_prefix,
        status="pending",
        file_count=len(files),
    )
    db.add(package)

    for filename, data in files:
        ext = "." + filename.rsplit(".", 1)[-1] if "." in filename else ""
        minio_key = f"{minio_prefix}{filename}"
        content_hash = hashlib.sha256(data).hexdigest()

        # Upload to MinIO
        await storage.upload_file(minio_key, data)

        file_record = PostFile(
            package_id=package_id,
            filename=filename,
            file_extension=ext.upper(),
            minio_key=minio_key,
            size_bytes=len(data),
            content_hash=content_hash,
        )
        db.add(file_record)

    await db.commit()
    await db.refresh(package)
    return package
