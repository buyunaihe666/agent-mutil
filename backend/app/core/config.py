"""Application configuration using pydantic-settings."""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _find_project_root() -> Path:
    """Find project root directory."""
    current = Path(__file__).resolve().parent.parent.parent
    for parent in [current, current.parent]:
        if (parent / ".env").exists():
            return parent
    return current.parent


def _load_yaml_config() -> dict:
    yaml_path = _find_project_root() / "config.yaml"
    if yaml_path.exists():
        with open(yaml_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_find_project_root() / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    APP_ENV: str = Field(default="development")
    LOG_LEVEL: str = Field(default="DEBUG")
    DATABASE_URL: str = Field(default="postgresql+asyncpg://nexus:nexus_dev@localhost:5432/nexus")
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    LLM_API_KEYS: Union[str, dict] = Field(default="{}")

    @field_validator("LLM_API_KEYS", mode="before")
    @classmethod
    def parse_api_keys(cls, v: Any) -> dict:
        if isinstance(v, dict):
            return v
        try:
            return json.loads(str(v))
        except (json.JSONDecodeError, TypeError):
            return {}

    def get_api_key(self, provider: str) -> Optional[str]:
        keys = self.LLM_API_KEYS
        if isinstance(keys, str):
            try:
                keys = json.loads(keys)
            except (json.JSONDecodeError, TypeError):
                return None
        return keys.get(provider)

    DEFAULT_LLM_MODEL: str = Field(default="deepseek-chat")
    ENCRYPTION_KEY: str = Field(default="change-me-to-a-random-64-char-hex-string")
    CORS_ORIGINS: Union[str, list] = Field(default="http://localhost:5173,http://localhost:3000")

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, list):
            return v
        return [o.strip() for o in str(v).split(",") if o.strip()]

    WS_HEARTBEAT_INTERVAL: int = Field(default=30)
    WS_MAX_RECONNECT_DELAY: int = Field(default=30)
    SANDBOX_MEMORY_LIMIT: str = Field(default="512m")
    SANDBOX_CPU_LIMIT: float = Field(default=1.0)
    SANDBOX_TIMEOUT: int = Field(default=60)
    AUDIT_LOG_RETENTION_DAYS: int = Field(default=90)
    RATE_LIMIT_PER_MINUTE: int = Field(default=60)
    RATE_LIMIT_PER_MINUTE_LLM: int = Field(default=10)


@lru_cache()
def get_settings() -> Settings:
    return Settings()
