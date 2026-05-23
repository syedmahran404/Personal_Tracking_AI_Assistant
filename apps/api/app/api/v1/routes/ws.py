"""WebSocket realtime channel.

Broadcasts dashboard updates to connected clients. Authenticated by a
short-lived JWT passed as the `?token=` query parameter (the standard
browser WebSocket API doesn't support custom headers).

Implementation: an in-memory connection registry. For multi-replica
deployments swap to Redis pub/sub (the redis client is already wired up).
"""
from __future__ import annotations

import asyncio
import contextlib
import uuid
from collections import defaultdict
from typing import Any

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status
from jose import JWTError

from app.core.security import decode_token

router = APIRouter()


class ConnectionRegistry:
    def __init__(self) -> None:
        self._conns: dict[uuid.UUID, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def add(self, user_id: uuid.UUID, ws: WebSocket) -> None:
        async with self._lock:
            self._conns[user_id].add(ws)

    async def remove(self, user_id: uuid.UUID, ws: WebSocket) -> None:
        async with self._lock:
            self._conns[user_id].discard(ws)
            if not self._conns[user_id]:
                self._conns.pop(user_id, None)

    async def broadcast(self, user_id: uuid.UUID, payload: dict[str, Any]) -> None:
        async with self._lock:
            targets = list(self._conns.get(user_id, ()))
        for ws in targets:
            with contextlib.suppress(Exception):
                # Best-effort delivery; let the client reconnect.
                await ws.send_json(payload)


registry = ConnectionRegistry()


@router.websocket("/dashboard")
async def dashboard_ws(websocket: WebSocket, token: str = Query(...)) -> None:
    try:
        payload = decode_token(token, expected_type="access")
        user_id = uuid.UUID(payload["sub"])
    except (JWTError, KeyError, ValueError):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    await registry.add(user_id, websocket)
    try:
        await websocket.send_json({"type": "hello", "user_id": str(user_id)})
        while True:
            # Keepalive — clients send pings, server echoes.
            msg = await websocket.receive_text()
            if msg == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        pass
    finally:
        await registry.remove(user_id, websocket)
