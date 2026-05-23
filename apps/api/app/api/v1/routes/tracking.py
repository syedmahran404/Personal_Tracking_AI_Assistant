"""Tracking ingestion endpoints (used by the desktop agent).

Critical path: must be cheap (batch insert, minimal validation overhead),
since the agent flushes every ~30 seconds for many users.
"""
from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models.app_usage import AppUsageEvent
from app.models.coding import CodingSession, GitCommit
from app.models.device import Device
from app.schemas.tracking import (
    AppUsageEventBatch,
    CodingSessionIn,
    CodingSessionPublic,
    GitCommitIn,
)
from app.services.classification import classify_app
from app.services.realtime import notify

router = APIRouter()


@router.post("/events", status_code=status.HTTP_202_ACCEPTED)
async def ingest_events(
    batch: AppUsageEventBatch,
    user: CurrentUser,
    db: DbSession,
) -> dict:
    """Ingest a batch of app-usage events from the agent."""
    rows: list[AppUsageEvent] = []
    for ev in batch.events:
        duration = max(int((ev.ended_at - ev.started_at).total_seconds()), 0)
        if duration == 0:
            continue
        category = classify_app(ev.app_name, ev.window_title)
        rows.append(
            AppUsageEvent(
                user_id=user.id,
                device_id=batch.device_id,
                app_name=ev.app_name,
                window_title=ev.window_title,
                bundle_id=ev.bundle_id,
                category=category,
                started_at=ev.started_at,
                ended_at=ev.ended_at,
                duration_seconds=duration,
                is_idle=ev.is_idle,
            )
        )
    if rows:
        db.add_all(rows)

    if batch.device_id:
        device = await db.get(Device, batch.device_id)
        if device and device.user_id == user.id:
            device.last_seen_at = datetime.now(UTC)

    await db.commit()

    if rows:
        notify(user.id, "dashboard.invalidate", {"reason": "events", "count": len(rows)})

    return {"accepted": len(rows)}


@router.post("/coding-sessions", response_model=CodingSessionPublic, status_code=201)
async def submit_coding_session(
    payload: CodingSessionIn,
    user: CurrentUser,
    db: DbSession,
) -> CodingSessionPublic:
    duration = max(int((payload.ended_at - payload.started_at).total_seconds()), 0)
    s = CodingSession(
        user_id=user.id,
        project=payload.project,
        language=payload.language,
        editor=payload.editor,
        branch=payload.branch,
        started_at=payload.started_at,
        ended_at=payload.ended_at,
        duration_seconds=duration,
        active_seconds=min(payload.active_seconds, duration),
        keystrokes=payload.keystrokes,
        files_touched=payload.files_touched,
    )
    db.add(s)
    await db.commit()
    await db.refresh(s)

    notify(user.id, "dashboard.invalidate", {"reason": "coding_session"})

    return CodingSessionPublic.model_validate(s)


@router.post("/git-commits", status_code=201)
async def submit_git_commit(
    payload: GitCommitIn,
    user: CurrentUser,
    db: DbSession,
) -> dict:
    # Idempotency by (user_id, repo, sha)
    existing = await db.scalar(
        select(GitCommit).where(
            GitCommit.user_id == user.id,
            GitCommit.repo == payload.repo,
            GitCommit.sha == payload.sha,
        )
    )
    if existing:
        return {"id": str(existing.id), "duplicate": True}

    commit = GitCommit(
        user_id=user.id,
        repo=payload.repo,
        branch=payload.branch,
        sha=payload.sha,
        message=payload.message,
        additions=payload.additions,
        deletions=payload.deletions,
        files_changed=payload.files_changed,
        committed_at=payload.committed_at,
    )
    db.add(commit)
    await db.commit()
    await db.refresh(commit)
    return {"id": str(commit.id), "duplicate": False}
