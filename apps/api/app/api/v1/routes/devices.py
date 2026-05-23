"""Device registration & listing for the desktop agent."""
from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models.device import Device
from app.schemas.tracking import DevicePublic, DeviceRegister

router = APIRouter()


@router.post("", response_model=DevicePublic, status_code=status.HTTP_201_CREATED)
async def register_device(
    payload: DeviceRegister,
    user: CurrentUser,
    db: DbSession,
) -> DevicePublic:
    device = Device(
        user_id=user.id,
        name=payload.name,
        platform=payload.platform,
        hostname=payload.hostname,
        agent_version=payload.agent_version,
        last_seen_at=datetime.now(UTC),
    )
    db.add(device)
    await db.commit()
    await db.refresh(device)
    return DevicePublic.model_validate(device)


@router.get("", response_model=list[DevicePublic])
async def list_devices(user: CurrentUser, db: DbSession) -> list[DevicePublic]:
    rows = (await db.scalars(select(Device).where(Device.user_id == user.id))).all()
    return [DevicePublic.model_validate(d) for d in rows]
