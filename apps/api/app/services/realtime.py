"""Realtime broadcast helpers.

Wraps the WebSocket connection registry so route handlers don't need
to import the WS module directly. All broadcasts are fire-and-forget:
ingestion latency never depends on slow WebSocket clients.

Event envelope:
    {"type": "<topic>", "ts": "<iso>", **payload}
The frontend uses `type` as a cache-invalidation hint — payloads are
intentionally tiny; clients refetch through normal HTTP endpoints
(keeps a single source of truth and avoids drift).
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)

# Strong refs to in-flight broadcasts. Without this the event loop's
# weak reference to the task can be GC'd before it runs (RUF006).
_pending: set[asyncio.Task[None]] = set()


def _envelope(event_type: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "type": event_type,
        "ts": datetime.now(UTC).isoformat(),
        **(payload or {}),
    }


def notify(user_id: uuid.UUID, event_type: str, payload: dict[str, Any] | None = None) -> None:
    """Schedule a broadcast to the user's WS connections.

    Safe to call from any async handler. If no event loop is running
    (e.g. during a sync script), the call is silently dropped — this is
    by design: realtime is a best-effort enhancement, never required
    for correctness.
    """
    # Local import avoids a circular dep: ws.py imports security which
    # depends on config which is imported very early.
    from app.api.v1.routes.ws import registry

    msg = _envelope(event_type, payload)
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        logger.debug("realtime.no_loop_skipping", user_id=str(user_id), event_type=event_type)
        return

    task = loop.create_task(registry.broadcast(user_id, msg))
    _pending.add(task)
    task.add_done_callback(_pending.discard)
