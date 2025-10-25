"""Application configuration helpers."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import List

from dotenv import load_dotenv


def _split_origins(raw_origins: str | None) -> List[str]:
    """Split a comma-delimited list of origins into a cleaned list."""
    if not raw_origins:
        return []
    return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]


class Settings:
    """Runtime configuration sourced from environment variables."""

    def __init__(self) -> None:
        load_dotenv()
        self.database_url: str = os.getenv("DATABASE_URL", "")
        self.redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.stack_auth_project_id: str | None = os.getenv("STACK_AUTH_PROJECT_ID")
        self.stack_auth_secret_key: str | None = os.getenv("STACK_AUTH_SECRET_KEY")
        self._cors_origins_raw: str | None = os.getenv("CORS_ORIGINS")

    @property
    def cors_origins(self) -> List[str]:
        return _split_origins(self._cors_origins_raw) or ["http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance so configuration is loaded once."""

    return Settings()
