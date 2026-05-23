"""Chat agent — answers questions grounded in the user's analytics.

Approach: retrieve a compact, structured "context pack" from analytics
for the user, embed it in a system message, then run the LLM. Keeping
the context compact (vs. shipping raw events) keeps token costs flat
and answers grounded.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.providers import get_provider, safe_json_dumps
from app.services.analytics import build_dashboard_summary

_SYS = (
    "You are 'Pulse', a friendly, sharp productivity assistant. "
    "Answer using ONLY the user's analytics context provided in [CONTEXT]. "
    "If the answer isn't in the context, say so briefly. "
    "Keep responses short (2-4 sentences) unless the user asks for detail. "
    "Use natural language; never output JSON or code unless asked."
)


async def build_context_pack(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    days: int = 7,
) -> dict[str, Any]:
    """Compact analytics snapshot used as grounding context for the agent."""
    end = datetime.now(UTC)
    start = end - timedelta(days=days)
    s = await build_dashboard_summary(db, user_id, start, end)
    return {
        "period_days": days,
        "productivity_score": s.productivity.score,
        "focus_score": s.productivity.focus_score,
        "productive_minutes": s.productivity.productive_seconds // 60,
        "distracting_minutes": s.productivity.distracting_seconds // 60,
        "coding_minutes": s.coding.active_seconds // 60,
        "coding_sessions": s.coding.sessions,
        "top_languages": s.coding.languages[:5],
        "top_projects": s.coding.projects[:5],
        "top_apps": [
            {"app": a.app_name, "minutes": a.duration_seconds // 60, "category": a.category}
            for a in s.top_apps[:8]
        ],
        "by_hour": [
            {"hour": h.hour, "productive_min": h.productive_seconds // 60}
            for h in s.by_hour
            if h.productive_seconds > 0
        ],
        "current_streak_days": s.streak.current_streak_days,
        "longest_streak_days": s.streak.longest_streak_days,
    }


async def chat_complete(
    db: AsyncSession,
    user_id: uuid.UUID,
    history: list[dict[str, str]],
    user_message: str,
) -> str:
    """Run one turn of the chat agent.

    history: previously persisted [{role, content}, ...] (most recent N)
    """
    ctx = await build_context_pack(db, user_id)
    provider = get_provider()
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": f"[CONTEXT] {safe_json_dumps(ctx)}"},
        *history[-10:],  # cap turn history for token control
        {"role": "user", "content": user_message},
    ]
    return await provider.complete(system=_SYS, messages=messages, temperature=0.4, max_tokens=500)
