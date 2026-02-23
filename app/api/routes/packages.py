"""Package-level operations: ZIP upload, status polling, file download.

Upload accepts a .zip file, validates UPG contents, stores files in MinIO,
creates DB records, and enqueues a Celery ingestion task. Status endpoint
lets clients poll for ingestion progress.
"""

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models.post_processor import ErrorResponse, StatusResponse
from app.db.database import get_db
from app.services import post_service
from app.services.storage import storage
from app.workers.tasks import ingest_package

router = APIRouter(prefix="/packages", tags=["packages"])


@router.post("/upload", status_code=202)
async def upload_package(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Upload a ZIP file containing a UPG post processor package.

    Validates file extension (.zip required), validates ZIP contents
    (all files must have known UPG extensions, at least one .SRC required),
    stores files in MinIO, creates DB records, and enqueues async ingestion.

    Returns 202 with package_id, job_id, and initial status.
    """
    # 1. Validate the file is a .zip
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                message="Please upload a .zip file containing your post processor package.",
                detail=f"Received file: '{file.filename or '(no filename)'}'",
                code="INVALID_FILE_TYPE",
            ).model_dump(),
        )

    # 2. Read ZIP bytes
    content = await file.read()

    # 3. Validate ZIP contents
    errors = post_service.validate_zip_contents(content)
    if errors:
        raise HTTPException(
            status_code=422,
            detail=ErrorResponse(
                message="The ZIP file could not be accepted.",
                detail="\n".join(errors),
                code="INVALID_ZIP_CONTENTS",
            ).model_dump(),
        )

    # 4. Extract files from ZIP (flattened)
    extracted_files = post_service.extract_zip_files(content)

    # 5. Generate package ID
    package_id = uuid.uuid4()

    # 6. Derive package name from SRC filename
    src_names = [fn for fn, _ in extracted_files if fn.upper().endswith(".SRC")]
    package_name = src_names[0].rsplit(".", 1)[0] if src_names else file.filename or "unknown"

    # 7. Create package + file records and upload to MinIO
    await post_service.create_package_with_files(
        db=db,
        package_id=package_id,
        name=package_name,
        files=extracted_files,
    )

    # 8. Enqueue Celery ingestion task
    task = ingest_package.delay(str(package_id))

    return {
        "package_id": str(package_id),
        "job_id": task.id,
        "status": "pending",
    }


@router.get("/{package_id}/status", response_model=StatusResponse)
async def get_package_status(
    package_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> StatusResponse:
    """Poll the current status of a package ingestion job.

    Returns the package status along with error details (if any),
    file count, and section count.
    """
    package = await post_service.get_package(db, package_id)
    if not package:
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse(
                message="Package not found.",
                detail=f"No package exists with ID '{package_id}'",
                code="NOT_FOUND",
            ).model_dump(),
        )

    return StatusResponse(
        package_id=str(package.id),
        status=package.status,
        error_message=package.error_message,
        error_detail=package.error_detail,
        file_count=package.file_count,
        section_count=package.section_count,
    )


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
