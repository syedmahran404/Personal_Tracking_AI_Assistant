"""initial schema

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-01-01 00:00:00.000000

Captures the entire schema as defined in app.models. After this baseline,
generate further migrations with:
    alembic revision --autogenerate -m "describe change"
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# ─── ENUMs ──────────────────────────────────────────────────────────────
PRODUCTIVITY_CLASS = sa.Enum(
    "productive", "neutral", "distracting", "unknown",
    name="productivity_class",
)
INSIGHT_KIND = sa.Enum(
    "daily_summary",
    "weekly_summary",
    "distraction_alert",
    "burnout_warning",
    "focus_tip",
    "streak",
    "recommendation",
    name="insight_kind",
)
CHAT_ROLE = sa.Enum("user", "assistant", "system", "tool", name="chat_role")


def upgrade() -> None:
    bind = op.get_bind()
    PRODUCTIVITY_CLASS.create(bind, checkfirst=True)
    INSIGHT_KIND.create(bind, checkfirst=True)
    CHAT_ROLE.create(bind, checkfirst=True)

    # ─── users ──────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("full_name", sa.String(120), nullable=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("timezone", sa.String(64), nullable=False, server_default="UTC"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("is_verified", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("is_admin", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ─── devices ────────────────────────────────────────────────────────
    op.create_table(
        "devices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("platform", sa.String(32), nullable=False),
        sa.Column("hostname", sa.String(255), nullable=True),
        sa.Column("agent_version", sa.String(32), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_devices_user_id", "devices", ["user_id"])

    # ─── refresh_tokens ─────────────────────────────────────────────────
    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("jti", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_refresh_tokens_jti", "refresh_tokens", ["jti"], unique=True)
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])

    # ─── app_usage_events ───────────────────────────────────────────────
    op.create_table(
        "app_usage_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("device_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("devices.id", ondelete="SET NULL"), nullable=True),
        sa.Column("app_name", sa.String(255), nullable=False),
        sa.Column("window_title", sa.String(1024), nullable=True),
        sa.Column("bundle_id", sa.String(255), nullable=True),
        sa.Column("category", PRODUCTIVITY_CLASS, nullable=False, server_default="unknown"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_seconds", sa.Integer, nullable=False),
        sa.Column("is_idle", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_app_usage_events_app_name", "app_usage_events", ["app_name"])
    op.create_index("ix_app_usage_user_started", "app_usage_events", ["user_id", "started_at"])
    op.create_index("ix_app_usage_user_app", "app_usage_events", ["user_id", "app_name"])

    # ─── coding_sessions ────────────────────────────────────────────────
    op.create_table(
        "coding_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project", sa.String(255), nullable=True),
        sa.Column("language", sa.String(64), nullable=True),
        sa.Column("editor", sa.String(64), nullable=True),
        sa.Column("branch", sa.String(255), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_seconds", sa.Integer, nullable=False),
        sa.Column("active_seconds", sa.Integer, nullable=False, server_default="0"),
        sa.Column("keystrokes", sa.Integer, nullable=False, server_default="0"),
        sa.Column("files_touched", postgresql.JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_coding_sessions_project", "coding_sessions", ["project"])
    op.create_index("ix_coding_user_started", "coding_sessions", ["user_id", "started_at"])
    op.create_index("ix_coding_user_lang", "coding_sessions", ["user_id", "language"])

    # ─── git_commits ────────────────────────────────────────────────────
    op.create_table(
        "git_commits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("repo", sa.String(255), nullable=False),
        sa.Column("branch", sa.String(255), nullable=True),
        sa.Column("sha", sa.String(64), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("additions", sa.Integer, nullable=False, server_default="0"),
        sa.Column("deletions", sa.Integer, nullable=False, server_default="0"),
        sa.Column("files_changed", sa.Integer, nullable=False, server_default="0"),
        sa.Column("committed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_git_user_committed", "git_commits", ["user_id", "committed_at"])

    # ─── insights ───────────────────────────────────────────────────────
    op.create_table(
        "insights",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", INSIGHT_KIND, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("severity", sa.String(16), nullable=False, server_default="info"),
        sa.Column("score", sa.Float, nullable=True),
        sa.Column("metrics", postgresql.JSONB, nullable=True),
        sa.Column("period_start", sa.Date, nullable=True),
        sa.Column("period_end", sa.Date, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_insights_user_id", "insights", ["user_id"])
    op.create_index("ix_insights_kind", "insights", ["kind"])

    # ─── chat_sessions ──────────────────────────────────────────────────
    op.create_table(
        "chat_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False, server_default="New chat"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_chat_sessions_user_id", "chat_sessions", ["user_id"])

    # ─── chat_messages ──────────────────────────────────────────────────
    op.create_table(
        "chat_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", CHAT_ROLE, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("tool_calls", postgresql.JSONB, nullable=True),
        sa.Column("tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_chat_messages_session_id", "chat_messages", ["session_id"])


def downgrade() -> None:
    op.drop_index("ix_chat_messages_session_id", table_name="chat_messages")
    op.drop_table("chat_messages")
    op.drop_index("ix_chat_sessions_user_id", table_name="chat_sessions")
    op.drop_table("chat_sessions")

    op.drop_index("ix_insights_kind", table_name="insights")
    op.drop_index("ix_insights_user_id", table_name="insights")
    op.drop_table("insights")

    op.drop_index("ix_git_user_committed", table_name="git_commits")
    op.drop_table("git_commits")

    op.drop_index("ix_coding_user_lang", table_name="coding_sessions")
    op.drop_index("ix_coding_user_started", table_name="coding_sessions")
    op.drop_index("ix_coding_sessions_project", table_name="coding_sessions")
    op.drop_table("coding_sessions")

    op.drop_index("ix_app_usage_user_app", table_name="app_usage_events")
    op.drop_index("ix_app_usage_user_started", table_name="app_usage_events")
    op.drop_index("ix_app_usage_events_app_name", table_name="app_usage_events")
    op.drop_table("app_usage_events")

    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_jti", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")

    op.drop_index("ix_devices_user_id", table_name="devices")
    op.drop_table("devices")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    bind = op.get_bind()
    CHAT_ROLE.drop(bind, checkfirst=True)
    INSIGHT_KIND.drop(bind, checkfirst=True)
    PRODUCTIVITY_CLASS.drop(bind, checkfirst=True)
