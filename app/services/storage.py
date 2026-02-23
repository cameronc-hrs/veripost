"""MinIO S3-compatible object storage service.

Provides async file upload, download, listing, and deletion
using aiobotocore. All files are stored in the configured bucket
under package-specific prefixes (packages/{id}/).
"""

import aiobotocore.session

from app.config import get_settings


class StorageService:
    """Async MinIO client for file operations."""

    def __init__(self) -> None:
        self._session = aiobotocore.session.get_session()
        self._settings = get_settings()

    def _get_client_kwargs(self) -> dict:
        return {
            "service_name": "s3",
            "endpoint_url": f"http://{self._settings.minio_endpoint}",
            "aws_access_key_id": self._settings.minio_access_key,
            "aws_secret_access_key": self._settings.minio_secret_key,
        }

    async def init_bucket(self) -> None:
        """Create the veripost bucket if it does not exist. Called at app startup."""
        async with self._session.create_client(**self._get_client_kwargs()) as client:
            try:
                await client.head_bucket(Bucket=self._settings.minio_bucket)
            except Exception:
                await client.create_bucket(Bucket=self._settings.minio_bucket)

    async def upload_file(
        self, key: str, data: bytes, content_type: str = "application/octet-stream"
    ) -> None:
        """Upload bytes to MinIO under the given key."""
        async with self._session.create_client(**self._get_client_kwargs()) as client:
            await client.put_object(
                Bucket=self._settings.minio_bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
            )

    async def download_file(self, key: str) -> bytes:
        """Download file bytes from MinIO by key."""
        async with self._session.create_client(**self._get_client_kwargs()) as client:
            resp = await client.get_object(
                Bucket=self._settings.minio_bucket, Key=key
            )
            async with resp["Body"] as stream:
                return await stream.read()

    async def list_files(self, prefix: str) -> list[str]:
        """List all keys under a prefix (e.g., packages/{id}/)."""
        async with self._session.create_client(**self._get_client_kwargs()) as client:
            resp = await client.list_objects_v2(
                Bucket=self._settings.minio_bucket, Prefix=prefix
            )
            return [obj["Key"] for obj in resp.get("Contents", [])]

    async def delete_prefix(self, prefix: str) -> None:
        """Delete all objects under a prefix."""
        keys = await self.list_files(prefix)
        if keys:
            async with self._session.create_client(**self._get_client_kwargs()) as client:
                for key in keys:
                    await client.delete_object(
                        Bucket=self._settings.minio_bucket, Key=key
                    )


# Module-level singleton — imported by routes and services
storage = StorageService()
