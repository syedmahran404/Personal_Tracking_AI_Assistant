"""Generate AI-powered insights from analytics summaries."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.providers import get_provider, safe_json_dumps
from app.models.insight import Insight, InsightKind
from app.services.analytics import build_dashboard_summary

_SYS_WEEKLY = (
    "You are a productivity coach analyzing a user's tracked activity. "
    "Be concise, supportive, and concrete. Refer to specific metrics. "
    "Output 3-5 short paragraphs, no headers, no markdown lists."
)


async def generate_weekly_summary(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> Insight:
    end = datetime.now(UTC)
    start = end - timedelta(days=7)

    summary = await build_dashboard_summary(db, user_id, start, end)
    payload = summary.model_dump(mode="json")

    provider = get_provider()
    text = await provider.complete(
        system=_SYS_WEEKLY,
        messages=[
            {
                "role": "system",
                "content": f"[CONTEXT] User analytics for past 7 days:\n{safe_json_dumps(payload)}",
            },
            {
                "role": "user",
                "content": "Write my weekly productivity summary.",
            },
        ],
        temperature=0.5,
        max_tokens=600,
    )

    insight = Insight(
        user_id=user_id,
        kind=InsightKind.WEEKLY_SUMMARY,
        title="Your weekly productivity summary",
        body=text.strip(),
        severity="info",
        score=summary.productivity.score,
        metrics={
            "productive_seconds": summary.productivity.productive_seconds,
            "distracting_seconds": summary.productivity.distracting_seconds,
            "focus_score": summary.productivity.focus_score,
            "coding_seconds": summary.coding.active_seconds,
            "streak": summary.streak.current_streak_days,
        },
        period_start=start.date(),
        period_end=end.date(),
    )
    db.add(insight)
    await db.commit()
    await db.refresh(insight)
    return insight


async def detect_distraction_alert(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> Insight | None:
    """Heuristic alert: if today's distracting time exceeds productive time AND
    distracting > 90 min, raise an alert."""
    end = datetime.now(UTC)
    start = end - timedelta(hours=24)
    s = await build_dashboard_summary(db, user_id, start, end)
    p = s.productivity
    if p.distracting_seconds > p.productive_seconds and p.distracting_seconds > 90 * 60:
        body = (
            f"In the last 24 hours, distracting apps consumed "
            f"{p.distracting_seconds // 60} minutes — more than your productive time "
            f"({p.productive_seconds // 60} minutes). Top culprit categories show up "
            f"in your app breakdown. Try blocking the most-used distraction for "
            f"two hours tomorrow morning."
        )
        insight = Insight(
            user_id=user_id,
            kind=InsightKind.DISTRACTION_ALERT,
            title="High distraction detected",
            body=body,
            severity="warning",
            score=p.score,
            metrics={"distracting_seconds": p.distracting_seconds},
        )
        db.add(insight)
        await db.commit()
        await db.refresh(insight)
        return insight
    return None
