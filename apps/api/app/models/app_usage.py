from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models._mixins import TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from app.models.user import User


class ProductivityClass(enum.StrEnum):
    """Coarse classification used for productivity scoring."""

    PRODUCTIVE = "productive"     # IDE, docs, terminal
    NEUTRAL = "neutral"           # browsers, file managers
    DISTRACTING = "distracting"   # social, games, video
    UNKNOWN = "unknown"


class AppUsageEvent(Base, UUIDPKMixin, TimestampMixin):
    """A single observed window-focus interval reported by the agent.

    The desktop agent samples the active window every N seconds and emits
    contiguous intervals as events. Events are append-only and the
    analytics engine aggregates them into sessions on demand.
    """

    __tablename__ = "app_usage_events"
    __table_args__ = (
        Index("ix_app_usage_user_started", "user_id", "started_at"),
        Index("ix_app_usage_user_app", "user_id", "app_name"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    device_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("devices.id", ondelete="SET NULL"),
        nullable=True,
    )

    app_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    window_title: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    bundle_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    category: Mapped[ProductivityClass] = mapped_column(
        Enum(ProductivityClass, name="productivity_class"),
        default=ProductivityClass.UNKNOWN,
        nullable=False,
    )

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)

    is_idle: Mapped[bool] = mapped_column(default=False, nullable=False)

    user: Mapped[User] = relationship(back_populates="app_usage_events")
