"""Celery worker tasks for async processing.

IMPORTANT: Celery tasks are SYNCHRONOUS. This module uses:
- ``sqlalchemy.create_engine`` (sync) with psycopg2 for DB access
- ``boto3`` for synchronous MinIO/S3 access

Do NOT use async/await in this module.
"""

import logging
import os

import boto3
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def get_sync_db_url() -> str:
    """Convert the async DATABASE_URL to a synchronous one for psycopg2."""
    async_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://veripost:veripost@postgres:5432/veripost",
    )
    return async_url.replace("+asyncpg", "")


def get_sync_engine():
    """Create a synchronous SQLAlchemy engine for the Celery worker."""
    return create_engine(get_sync_db_url())


def get_minio_client():
    """Create a synchronous boto3 S3 client for MinIO access."""
    return boto3.client(
        "s3",
        endpoint_url=f"http://{os.environ.get('MINIO_ENDPOINT', 'minio:9000')}",
        aws_access_key_id=os.environ.get("MINIO_ACCESS_KEY", "veripost"),
        aws_secret_access_key=os.environ.get("MINIO_SECRET_KEY", "veripost123"),
    )


@celery_app.task(bind=True, name="ingest_package")
def ingest_package(self, package_id: str) -> dict:
    """Skeleton ingestion task. Processes a ZIP package that was already
    uploaded to MinIO by the API route.

    Status flow: pending -> validating -> storing -> parsing (stub) -> ready | error

    The parse step is a stub -- Phase 2 will implement real UPG parsing.
    """
    engine = get_sync_engine()
    try:
        with Session(engine) as db:
            # -- validating: verify files exist in MinIO --
            db.execute(
                text("UPDATE post_packages SET status = 'validating' WHERE id = :id"),
                {"id": package_id},
            )
            db.commit()
            logger.info("Package %s: validating", package_id)

            s3 = get_minio_client()
            prefix = f"packages/{package_id}/"
            bucket = os.environ.get("MINIO_BUCKET", "veripost")
            resp = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
            files = resp.get("Contents", [])
            logger.info("Package %s: found %d files in MinIO", package_id, len(files))

            # -- storing: confirm file integrity (already in MinIO from upload) --
            db.execute(
                text("UPDATE post_packages SET status = 'storing' WHERE id = :id"),
                {"id": package_id},
            )
            db.commit()
            logger.info("Package %s: storing (files verified in MinIO)", package_id)

            # -- parsing: STUB -- Phase 2 will implement real parsing --
            db.execute(
                text("UPDATE post_packages SET status = 'parsing' WHERE id = :id"),
                {"id": package_id},
            )
            db.commit()
            logger.info(
                "Package %s: parsing (stub - Phase 2 will implement real parsing)",
                package_id,
            )

            # -- ready: mark package as successfully ingested --
            db.execute(
                text(
                    "UPDATE post_packages SET status = 'ready', "
                    "file_count = :fc, section_count = 0 "
                    "WHERE id = :id"
                ),
                {"id": package_id, "fc": len(files)},
            )
            db.commit()
            logger.info("Package %s: ready", package_id)

        return {"package_id": package_id, "status": "ready", "file_count": len(files)}

    except Exception as exc:
        logger.error("Package %s: error - %s", package_id, exc)
        with Session(engine) as db:
            db.execute(
                text(
                    "UPDATE post_packages SET status = 'error', "
                    "error_message = :msg, error_detail = :detail "
                    "WHERE id = :id"
                ),
                {
                    "id": package_id,
                    "msg": "Something went wrong while processing your package.",
                    "detail": str(exc),
                },
            )
            db.commit()
        raise
    finally:
        engine.dispose()
