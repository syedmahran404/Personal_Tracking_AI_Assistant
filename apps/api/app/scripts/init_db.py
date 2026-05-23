"""Initialize the database schema.

For first-time setup we use `Base.metadata.create_all`. After this, use
Alembic for incremental migrations:
    alembic revision --autogenerate -m "describe change"
    alembic upgrade head
"""
from __future__ import annotations

import asyncio

from app.core.database import Base, get_engine
from app.core.logging import configure_logging, get_logger
from app.models import *  # noqa: F403  — register all tables

configure_logging()
log = get_logger(__name__)


async def init_db() -> None:
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info("init_db.complete")


if __name__ == "__main__":
    asyncio.run(init_db())
