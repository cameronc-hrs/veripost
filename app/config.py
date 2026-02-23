"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Application
    app_env: str = "development"
    app_debug: bool = False
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # AI
    anthropic_api_key: str = ""
    ai_model: str = "claude-sonnet-4-20250514"

    # Database (PostgreSQL + asyncpg)
    database_url: str = "postgresql+asyncpg://veripost:veripost@postgres:5432/veripost"

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # MinIO (S3-compatible object storage)
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "veripost"
    minio_secret_key: str = "veripost123"
    minio_bucket: str = "veripost"
    minio_use_ssl: bool = False

    # Celery (async task queue)
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/0"

    # Corpus
    corpus_dir: Path = Path("./corpus")

    # Logging
    log_level: str = "INFO"

    @property
    def is_dev(self) -> bool:
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
