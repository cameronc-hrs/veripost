"""Package-level operations: file download, etc.

Expanded in Plan 01-03 with ZIP upload endpoint.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.services import post_service
from app.services.storage import storage

router = APIRouter(prefix="/packages", tags=["packages"])


@router.get("/{package_id}/files/{file_id}/download")
async def download_file(
    package_id: uuid.UUID,
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Download a file from a package via MinIO.

    Returns the raw file bytes with the original filename in the
    Content-Disposition header.
    """
    package = await post_service.get_package(db, package_id)
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")

    # Find the requested file in the package
    target_file = None
    for f in package.files:
        if f.id == file_id:
            target_file = f
            break

    if not target_file:
        raise HTTPException(status_code=404, detail="File not found in package")

    # Download from MinIO
    try:
        data = await storage.download_file(target_file.minio_key)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"File storage is temporarily unavailable: {exc}",
        )

    return Response(
        content=data,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{target_file.filename}"'
        },
    )
