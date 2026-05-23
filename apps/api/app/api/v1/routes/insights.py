"""Insights — list, generate weekly summary, run distraction detector."""
from __future__ import annotations

from fastapi import APIRouter, status
from sqlalchemy import desc, select

from app.ai.insights import detect_distraction_alert, generate_weekly_summary
from app.api.deps import CurrentUser, DbSession
from app.models.insight import Insight
from app.schemas.insight import InsightPublic
from app.services.realtime import notify

router = APIRouter()


@router.get("", response_model=list[InsightPublic])
async def list_insights(user: CurrentUser, db: DbSession) -> list[InsightPublic]:
    rows = (
        await db.scalars(
            select(Insight)
            .where(Insight.user_id == user.id)
            .order_by(desc(Insight.created_at))
            .limit(50)
        )
    ).all()
    return [InsightPublic.model_validate(r) for r in rows]


@router.post(
    "/generate/weekly",
    response_model=InsightPublic,
    status_code=status.HTTP_201_CREATED,
)
async def generate_weekly(user: CurrentUser, db: DbSession) -> InsightPublic:
    insight = await generate_weekly_summary(db, user.id)
    notify(user.id, "insights.created", {"kind": insight.kind.value})
    return InsightPublic.model_validate(insight)


@router.post("/scan/distraction", response_model=InsightPublic | None)
async def scan_distraction(user: CurrentUser, db: DbSession) -> InsightPublic | None:
    insight = await detect_distraction_alert(db, user.id)
    if insight:
        notify(user.id, "insights.created", {"kind": insight.kind.value})
    return InsightPublic.model_validate(insight) if insight else None
