from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models._mixins import TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from app.models.user import User


class CodingSession(Base, UUIDPKMixin, TimestampMixin):
    """A contiguous coding session derived from IDE focus events."""

    __tablename__ = "coding_sessions"
    __table_args__ = (
        Index("ix_coding_user_started", "user_id", "started_at"),
        Index("ix_coding_user_lang", "user_id", "language"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    project: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    language: Mapped[str | None] = mapped_column(String(64), nullable=True)
    editor: Mapped[str | None] = mapped_column(String(64), nullable=True)  # vscode, jetbrains
    branch: Mapped[str | None] = mapped_column(String(255), nullable=True)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    active_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    keystrokes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    files_touched: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)

    user: Mapped[User] = relationship(back_populates="coding_sessions")


class GitCommit(Base, UUIDPKMixin, TimestampMixin):
    """Git commits attributed to the user, scraped by the agent or pushed via API."""

    __tablename__ = "git_commits"
    __table_args__ = (
        Index("ix_git_user_committed", "user_id", "committed_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    repo: Mapped[str] = mapped_column(String(255), nullable=False)
    branch: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sha: Mapped[str] = mapped_column(String(64), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    additions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    deletions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    files_changed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    committed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
