from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.insight import InsightKind


class InsightPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    kind: InsightKind
    title: str
    body: str
    severity: str
    score: float | None
    metrics: dict | None
    period_start: date | None
    period_end: date | None
    created_at: datetime
