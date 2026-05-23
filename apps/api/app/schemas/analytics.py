from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel


class TimeRange(BaseModel):
    start: datetime
    end: datetime


class ProductivityScore(BaseModel):
    """Aggregated score for a period."""

    score: float            # 0..100
    focus_score: float      # 0..100
    productive_seconds: int
    distracting_seconds: int
    neutral_seconds: int
    total_tracked_seconds: int


class AppShare(BaseModel):
    app_name: str
    duration_seconds: int
    share: float            # 0..1
    category: str


class HourBucket(BaseModel):
    hour: int               # 0..23
    productive_seconds: int
    distracting_seconds: int


class DayBucket(BaseModel):
    day: date
    productive_seconds: int
    distracting_seconds: int
    coding_seconds: int
    score: float


class CodingSummary(BaseModel):
    total_seconds: int
    active_seconds: int
    sessions: int
    languages: list[dict]   # [{language, seconds}]
    projects: list[dict]    # [{project, seconds}]


class StreakInfo(BaseModel):
    current_streak_days: int
    longest_streak_days: int
    today_productive_seconds: int


class DashboardSummary(BaseModel):
    productivity: ProductivityScore
    coding: CodingSummary
    top_apps: list[AppShare]
    by_hour: list[HourBucket]
    by_day: list[DayBucket]
    streak: StreakInfo
    period: TimeRange
