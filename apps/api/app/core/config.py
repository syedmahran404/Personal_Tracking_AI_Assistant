"""Application configuration loaded from environment variables.

Single source of truth for runtime config. Pydantic-settings validates
types and provides safe defaults. Never hard-code secrets — always use env.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ─── App ───────────────────────────────────────────────
    APP_ENV: Literal["development", "staging", "production", "test"] = "development"
    APP_NAME: str = "Personal Tracking AI Assistant"
    APP_DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # ─── Server ────────────────────────────────────────────
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CORS_ORIGINS: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _parse_cors(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    # ─── Security ──────────────────────────────────────────
    SECRET_KEY: str = "dev-only-please-change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"

    # ─── Database ──────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://ptaa:ptaa_dev_password@localhost:5432/ptaa"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://ptaa:ptaa_dev_password@localhost:5432/ptaa"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # ─── Redis ─────────────────────────────────────────────
    REDIS_URL: RedisDsn = "redis://localhost:6379/0"

    # ─── AI ────────────────────────────────────────────────
    AI_PROVIDER: Literal["openai", "anthropic", "mock"] = "mock"
    AI_MODEL: str = "gpt-4o-mini"
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    # ─── Rate limiting ─────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 120

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
