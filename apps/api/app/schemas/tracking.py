from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.app_usage import ProductivityClass


class DeviceRegister(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    platform: str = Field(min_length=1, max_length=32)
    hostname: str | None = Field(default=None, max_length=255)
    agent_version: str | None = Field(default=None, max_length=32)


class DevicePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    platform: str
    hostname: str | None
    agent_version: str | None
    last_seen_at: datetime | None
    created_at: datetime


class AppUsageEventIn(BaseModel):
    """Single app focus interval pushed by the agent."""

    app_name: str = Field(min_length=1, max_length=255)
    window_title: str | None = Field(default=None, max_length=1024)
    bundle_id: str | None = Field(default=None, max_length=255)
    started_at: datetime
    ended_at: datetime
    is_idle: bool = False

    @field_validator("ended_at")
    @classmethod
    def _ends_after_starts(cls, v: datetime, info):
        started = info.data.get("started_at")
        if started and v < started:
            raise ValueError("ended_at must be >= started_at")
        return v


class AppUsageEventBatch(BaseModel):
    """Batch ingestion endpoint payload."""

    device_id: uuid.UUID | None = None
    events: list[AppUsageEventIn] = Field(min_length=1, max_length=2000)


class AppUsageEventPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    app_name: str
    window_title: str | None
    category: ProductivityClass
    started_at: datetime
    ended_at: datetime
    duration_seconds: int
    is_idle: bool


class CodingSessionIn(BaseModel):
    project: str | None = Field(default=None, max_length=255)
    language: str | None = Field(default=None, max_length=64)
    editor: str | None = Field(default=None, max_length=64)
    branch: str | None = Field(default=None, max_length=255)
    started_at: datetime
    ended_at: datetime
    active_seconds: int = Field(ge=0)
    keystrokes: int = Field(default=0, ge=0)
    files_touched: list[str] = Field(default_factory=list)


class CodingSessionPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project: str | None
    language: str | None
    editor: str | None
    branch: str | None
    started_at: datetime
    ended_at: datetime
    duration_seconds: int
    active_seconds: int
    keystrokes: int
    files_touched: list[str]


class GitCommitIn(BaseModel):
    repo: str = Field(min_length=1, max_length=255)
    branch: str | None = Field(default=None, max_length=255)
    sha: str = Field(min_length=4, max_length=64)
    message: str = Field(min_length=1)
    additions: int = 0
    deletions: int = 0
    files_changed: int = 0
    committed_at: datetime
