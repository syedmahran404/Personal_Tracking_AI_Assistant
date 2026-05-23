"""v1 router aggregator — single mount point for the API surface."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.routes import analytics, auth, chat, devices, insights, tracking, users
from app.api.v1.routes import ws as ws_routes

api_router = APIRouter(prefix="/v1")

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(devices.router, prefix="/devices", tags=["devices"])
api_router.include_router(tracking.router, prefix="/tracking", tags=["tracking"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(insights.router, prefix="/insights", tags=["insights"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(ws_routes.router, prefix="/ws", tags=["ws"])
