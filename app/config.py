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

    # Database
    database_url: str = "sqlite+aiosqlite:///./veripost.db"

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
