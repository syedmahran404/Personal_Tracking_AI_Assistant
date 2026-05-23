"""Analytics engine: focus score, productivity score, deep work, streaks.

All queries are async-SQL and pushed down to Postgres for performance.
For high-volume deployments these can be moved to a materialized view or
TimescaleDB hypertable without changing the public API.
"""
from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.app_usage import AppUsageEvent, ProductivityClass
from app.models.coding import CodingSession
from app.schemas.analytics import (
    AppShare,
    CodingSummary,
    DashboardSummary,
    DayBucket,
    HourBucket,
    ProductivityScore,
    StreakInfo,
    TimeRange,
)

# ─── Algorithm constants ───────────────────────────────────
# Productivity score weights (must sum within a sensible range)
_W_PRODUCTIVE = 1.0
_W_NEUTRAL = 0.4
_W_DISTRACTING = -0.7

# Focus score parameters
_DEEP_WORK_MIN_SECONDS = 25 * 60        # 25 minutes uninterrupted = deep work
_CONTEXT_SWITCH_PENALTY = 0.05          # per switch / minute, capped


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def compute_productivity_score(
    productive: int,
    neutral: int,
    distracting: int,
) -> float:
    """Weighted score normalized to 0..100.

    The score is a soft mapping of productive vs distracting time:
      raw = (W_p*P + W_n*N + W_d*D) / max(total, 1)
      score = clamp((raw + 0.5) * 100, 0, 100)
    """
    total = productive + neutral + distracting
    if total == 0:
        return 0.0
    raw = (
        _W_PRODUCTIVE * productive
        + _W_NEUTRAL * neutral
        + _W_DISTRACTING * distracting
    ) / total
    return round(_clamp((raw + 0.5) * 100), 1)


def compute_focus_score(
    productive_seconds: int,
    deep_work_blocks: int,
    context_switches: int,
    tracked_seconds: int,
) -> float:
    """Focus score rewards long uninterrupted productive blocks.

    base   = productive / tracked  (0..1)
    bonus  = deep_work_blocks * 0.05  (capped 0.25)
    penalty= min(context_switches * _CONTEXT_SWITCH_PENALTY, 0.4)
    """
    if tracked_seconds <= 0:
        return 0.0
    base = productive_seconds / tracked_seconds
    bonus = min(deep_work_blocks * 0.05, 0.25)
    penalty = min(context_switches * _CONTEXT_SWITCH_PENALTY, 0.4)
    return round(_clamp((base + bonus - penalty) * 100), 1)


# ─── Aggregation helpers ───────────────────────────────────
async def _events_in_range(
    db: AsyncSession,
    user_id: uuid.UUID,
    start: datetime,
    end: datetime,
) -> list[AppUsageEvent]:
    stmt = (
        select(AppUsageEvent)
        .where(
            and_(
                AppUsageEvent.user_id == user_id,
                AppUsageEvent.started_at >= start,
                AppUsageEvent.started_at < end,
                AppUsageEvent.is_idle.is_(False),
            )
        )
        .order_by(AppUsageEvent.started_at.asc())
    )
    return list((await db.scalars(stmt)).all())


def _aggregate_durations(events: list[AppUsageEvent]) -> dict[ProductivityClass, int]:
    out: dict[ProductivityClass, int] = defaultdict(int)
    for e in events:
        out[e.category] += e.duration_seconds
    return out


def _detect_deep_work_and_switches(events: list[AppUsageEvent]) -> tuple[int, int]:
    """Detect deep-work blocks and context switches from sorted events.

    Deep work block = contiguous run of productive events whose total
    duration >= _DEEP_WORK_MIN_SECONDS, with no gap > 2 minutes between events.
    Context switch = any change in category between consecutive events.
    """
    blocks = 0
    switches = 0
    run_seconds = 0
    last_category: ProductivityClass | None = None
    last_end: datetime | None = None

    for e in events:
        if last_category is not None and e.category != last_category:
            switches += 1

        if e.category == ProductivityClass.PRODUCTIVE and (
            last_end is None or (e.started_at - last_end).total_seconds() <= 120
        ):
            run_seconds += e.duration_seconds
        else:
            if run_seconds >= _DEEP_WORK_MIN_SECONDS:
                blocks += 1
            run_seconds = e.duration_seconds if e.category == ProductivityClass.PRODUCTIVE else 0

        last_category = e.category
        last_end = e.ended_at

    if run_seconds >= _DEEP_WORK_MIN_SECONDS:
        blocks += 1
    return blocks, switches


# ─── Public summary builder ────────────────────────────────
async def build_dashboard_summary(
    db: AsyncSession,
    user_id: uuid.UUID,
    start: datetime,
    end: datetime,
) -> DashboardSummary:
    events = await _events_in_range(db, user_id, start, end)
    durations = _aggregate_durations(events)
    productive = durations.get(ProductivityClass.PRODUCTIVE, 0)
    neutral = durations.get(ProductivityClass.NEUTRAL, 0)
    distracting = durations.get(ProductivityClass.DISTRACTING, 0)
    unknown = durations.get(ProductivityClass.UNKNOWN, 0)
    tracked = productive + neutral + distracting + unknown

    deep_blocks, switches = _detect_deep_work_and_switches(events)
    score = compute_productivity_score(productive, neutral, distracting)
    focus = compute_focus_score(productive, deep_blocks, switches, max(tracked, 1))

    # Top apps
    by_app: dict[str, tuple[int, ProductivityClass]] = defaultdict(
        lambda: (0, ProductivityClass.UNKNOWN)
    )
    for e in events:
        cur, _ = by_app[e.app_name]
        by_app[e.app_name] = (cur + e.duration_seconds, e.category)
    top = sorted(by_app.items(), key=lambda kv: kv[1][0], reverse=True)[:10]
    top_apps = [
        AppShare(
            app_name=name,
            duration_seconds=secs,
            share=(secs / tracked) if tracked else 0.0,
            category=cat.value,
        )
        for name, (secs, cat) in top
    ]

    # By hour
    hour_p: dict[int, int] = defaultdict(int)
    hour_d: dict[int, int] = defaultdict(int)
    for e in events:
        hr = e.started_at.astimezone(UTC).hour
        if e.category == ProductivityClass.PRODUCTIVE:
            hour_p[hr] += e.duration_seconds
        elif e.category == ProductivityClass.DISTRACTING:
            hour_d[hr] += e.duration_seconds
    by_hour = [
        HourBucket(
            hour=h,
            productive_seconds=hour_p.get(h, 0),
            distracting_seconds=hour_d.get(h, 0),
        )
        for h in range(24)
    ]

    # By day (and per-day score)
    day_p: dict[date, int] = defaultdict(int)
    day_d: dict[date, int] = defaultdict(int)
    day_n: dict[date, int] = defaultdict(int)
    for e in events:
        d = e.started_at.astimezone(UTC).date()
        if e.category == ProductivityClass.PRODUCTIVE:
            day_p[d] += e.duration_seconds
        elif e.category == ProductivityClass.DISTRACTING:
            day_d[d] += e.duration_seconds
        elif e.category == ProductivityClass.NEUTRAL:
            day_n[d] += e.duration_seconds

    # Coding aggregates
    coding_stmt = (
        select(CodingSession)
        .where(
            and_(
                CodingSession.user_id == user_id,
                CodingSession.started_at >= start,
                CodingSession.started_at < end,
            )
        )
    )
    sessions = list((await db.scalars(coding_stmt)).all())
    coding_total = sum(s.duration_seconds for s in sessions)
    coding_active = sum(s.active_seconds for s in sessions)

    lang_seconds: dict[str, int] = defaultdict(int)
    proj_seconds: dict[str, int] = defaultdict(int)
    coding_per_day: dict[date, int] = defaultdict(int)
    for s in sessions:
        if s.language:
            lang_seconds[s.language] += s.active_seconds
        if s.project:
            proj_seconds[s.project] += s.active_seconds
        coding_per_day[s.started_at.astimezone(UTC).date()] += s.active_seconds

    languages = sorted(
        ({"language": k, "seconds": v} for k, v in lang_seconds.items()),
        key=lambda x: x["seconds"],
        reverse=True,
    )
    projects = sorted(
        ({"project": k, "seconds": v} for k, v in proj_seconds.items()),
        key=lambda x: x["seconds"],
        reverse=True,
    )

    # Build day buckets covering the full range
    days: list[DayBucket] = []
    cur = start.date()
    end_date = (end - timedelta(seconds=1)).date()
    while cur <= end_date:
        ps = compute_productivity_score(day_p.get(cur, 0), day_n.get(cur, 0), day_d.get(cur, 0))
        days.append(
            DayBucket(
                day=cur,
                productive_seconds=day_p.get(cur, 0),
                distracting_seconds=day_d.get(cur, 0),
                coding_seconds=coding_per_day.get(cur, 0),
                score=ps,
            )
        )
        cur += timedelta(days=1)

    # Streak: consecutive days with productive_seconds >= 30 min, ending today
    streak = await _compute_streak(db, user_id)

    return DashboardSummary(
        productivity=ProductivityScore(
            score=score,
            focus_score=focus,
            productive_seconds=productive,
            distracting_seconds=distracting,
            neutral_seconds=neutral,
            total_tracked_seconds=tracked,
        ),
        coding=CodingSummary(
            total_seconds=coding_total,
            active_seconds=coding_active,
            sessions=len(sessions),
            languages=languages,
            projects=projects,
        ),
        top_apps=top_apps,
        by_hour=by_hour,
        by_day=days,
        streak=streak,
        period=TimeRange(start=start, end=end),
    )


async def _compute_streak(db: AsyncSession, user_id: uuid.UUID) -> StreakInfo:
    """Streak = consecutive days with at least 30 min productive time."""
    threshold = 30 * 60
    today = datetime.now(UTC).date()
    start = today - timedelta(days=180)  # look back 6 months max
    start_dt = datetime.combine(start, datetime.min.time(), tzinfo=UTC)

    stmt = (
        select(
            func.date_trunc("day", AppUsageEvent.started_at).label("d"),
            func.sum(AppUsageEvent.duration_seconds).label("secs"),
        )
        .where(
            and_(
                AppUsageEvent.user_id == user_id,
                AppUsageEvent.category == ProductivityClass.PRODUCTIVE,
                AppUsageEvent.started_at >= start_dt,
            )
        )
        .group_by("d")
    )
    rows = (await db.execute(stmt)).all()
    by_day = {r.d.date() if hasattr(r.d, "date") else r.d: int(r.secs or 0) for r in rows}
    today_secs = by_day.get(today, 0)

    # Current streak (today must qualify or yesterday — graceful)
    cur_streak = 0
    longest = 0
    run = 0
    cur = start
    while cur <= today:
        if by_day.get(cur, 0) >= threshold:
            run += 1
            longest = max(longest, run)
        else:
            run = 0
        cur += timedelta(days=1)

    # Walk back from today to compute current streak
    d = today
    while by_day.get(d, 0) >= threshold:
        cur_streak += 1
        d -= timedelta(days=1)

    return StreakInfo(
        current_streak_days=cur_streak,
        longest_streak_days=longest,
        today_productive_seconds=today_secs,
    )
