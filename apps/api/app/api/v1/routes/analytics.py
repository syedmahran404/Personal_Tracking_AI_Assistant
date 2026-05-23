"""Analytics endpoints — read-only aggregations powering the dashboard."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession
from app.schemas.analytics import DashboardSummary
from app.services.analytics import build_dashboard_summary

router = APIRouter()

Range = Literal["today", "7d", "30d", "90d"]
_RANGE_DAYS: dict[Range, int] = {"today": 1, "7d": 7, "30d": 30, "90d": 90}


def _resolve_range(r: Range) -> tuple[datetime, datetime]:
    end = datetime.now(UTC)
    if r == "today":
        start = end.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        start = end - timedelta(days=_RANGE_DAYS[r])
    return start, end


@router.get("/dashboard", response_model=DashboardSummary)
async def dashboard(
    user: CurrentUser,
    db: DbSession,
    range: Range = Query("7d"),
) -> DashboardSummary:
    start, end = _resolve_range(range)
    return await build_dashboard_summary(db, user.id, start, end)
