"""Seed the database with a demo user and ~14 days of plausible activity.

Generates realistic patterns: stronger productivity midweek, a midday
distraction dip, evening coding sessions. Useful for screenshots, demos,
and verifying the analytics pipeline end-to-end.
"""
from __future__ import annotations

import asyncio
import random
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core.database import get_sessionmaker
from app.core.logging import configure_logging, get_logger
from app.core.security import hash_password
from app.models.app_usage import AppUsageEvent
from app.models.coding import CodingSession, GitCommit
from app.models.user import User
from app.scripts.init_db import init_db
from app.services.classification import classify_app

configure_logging()
log = get_logger(__name__)

DEMO_EMAIL = "demo@ptaa.dev"
DEMO_PASSWORD = "demo12345"

PRODUCTIVE_APPS = ["VS Code", "iTerm", "Cursor", "Notion", "Figma"]
NEUTRAL_APPS = ["Chrome", "Slack", "Mail"]
DISTRACTING_APPS = ["YouTube", "Twitter", "Discord", "Reddit"]
LANGUAGES = ["TypeScript", "Python", "Rust", "Go"]
PROJECTS = ["ptaa-web", "ptaa-api", "ptaa-agent", "side-project"]


def _random_intervals(
    day: datetime,
    slots: list[tuple[int, int, list[str]]],
) -> list[AppUsageEvent]:
    """Generate non-overlapping random app intervals for a given day.

    slots is a list of (hour_start, hour_end, app_pool) triples. We fill
    each slot with 3-8 intervals of 5-45 minutes.
    """
    out: list[AppUsageEvent] = []
    for hour_start, hour_end, pool in slots:
        cur = day.replace(hour=hour_start, minute=random.randint(0, 15), second=0, microsecond=0)
        end_of_slot = day.replace(hour=hour_end, minute=0, second=0, microsecond=0)
        while cur < end_of_slot:
            dur = timedelta(minutes=random.randint(5, 45))
            end = min(cur + dur, end_of_slot)
            app = random.choice(pool)
            title = {
                "VS Code": "main.py — ptaa-api",
                "Cursor": "page.tsx — ptaa-web",
                "Chrome": random.choice(["GitHub", "MDN", "Stack Overflow", "Hacker News"]),
                "YouTube": random.choice(["Lo-fi mix", "Conference talk", "Tutorial"]),
            }.get(app)
            out.append(
                AppUsageEvent(
                    user_id=None,  # set below
                    app_name=app,
                    window_title=title,
                    category=classify_app(app, title),
                    started_at=cur,
                    ended_at=end,
                    duration_seconds=int((end - cur).total_seconds()),
                )
            )
            cur = end + timedelta(minutes=random.randint(0, 5))
    return out


async def seed() -> None:
    await init_db()
    SessionLocal = get_sessionmaker()
    async with SessionLocal() as db:
        existing = await db.scalar(select(User).where(User.email == DEMO_EMAIL))
        if existing:
            log.info("seed.demo_user_exists", email=DEMO_EMAIL)
            user = existing
        else:
            user = User(
                email=DEMO_EMAIL,
                full_name="Demo User",
                hashed_password=hash_password(DEMO_PASSWORD),
                timezone="UTC",
                is_verified=True,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            log.info("seed.demo_user_created", email=DEMO_EMAIL)

        # Wipe past demo data to keep seed idempotent.
        from sqlalchemy import delete
        await db.execute(delete(AppUsageEvent).where(AppUsageEvent.user_id == user.id))
        await db.execute(delete(CodingSession).where(CodingSession.user_id == user.id))
        await db.execute(delete(GitCommit).where(GitCommit.user_id == user.id))
        await db.commit()

        now = datetime.now(UTC)
        events: list[AppUsageEvent] = []
        coding: list[CodingSession] = []
        commits: list[GitCommit] = []

        for d in range(14):
            day = (now - timedelta(days=d)).replace(hour=0, minute=0, second=0, microsecond=0)
            weekday = day.weekday()  # 0=Mon

            # Skip weekends partially
            if weekday >= 5 and random.random() < 0.4:
                continue

            slots = [
                (9, 12, [*PRODUCTIVE_APPS, random.choice(NEUTRAL_APPS)]),
                (12, 13, [*NEUTRAL_APPS, *DISTRACTING_APPS]),  # lunch dip
                (13, 17, [*PRODUCTIVE_APPS, random.choice(NEUTRAL_APPS)]),
                (17, 19, [*DISTRACTING_APPS, random.choice(NEUTRAL_APPS)]),
            ]
            day_events = _random_intervals(day, slots)
            for e in day_events:
                e.user_id = user.id
            events.extend(day_events)

            # Coding sessions: 1-3 per day, 30-120 min
            for _ in range(random.randint(1, 3)):
                start_h = random.choice([9, 10, 14, 20])
                start = day.replace(hour=start_h, minute=random.randint(0, 30))
                duration = timedelta(minutes=random.randint(30, 120))
                end = start + duration
                active = int(duration.total_seconds() * random.uniform(0.55, 0.9))
                coding.append(
                    CodingSession(
                        user_id=user.id,
                        project=random.choice(PROJECTS),
                        language=random.choice(LANGUAGES),
                        editor=random.choice(["vscode", "cursor", "jetbrains"]),
                        branch=random.choice(["main", "feat/dashboard", "fix/auth"]),
                        started_at=start,
                        ended_at=end,
                        duration_seconds=int(duration.total_seconds()),
                        active_seconds=active,
                        keystrokes=random.randint(500, 8000),
                        files_touched=random.sample(
                            ["main.py", "page.tsx", "App.tsx", "models.py", "config.ts"],
                            k=random.randint(1, 4),
                        ),
                    )
                )

            # 0-3 commits per day
            for _ in range(random.randint(0, 3)):
                commit_at = day.replace(
                    hour=random.randint(10, 22),
                    minute=random.randint(0, 59),
                )
                commits.append(
                    GitCommit(
                        user_id=user.id,
                        repo=random.choice(PROJECTS),
                        branch=random.choice(["main", "feat/x", "fix/y"]),
                        sha="".join(random.choices("0123456789abcdef", k=10)),
                        message=random.choice(
                            [
                                "feat: add dashboard charts",
                                "fix: race condition in auth refresh",
                                "chore: bump deps",
                                "refactor: extract analytics service",
                                "test: cover focus score edge cases",
                            ]
                        ),
                        additions=random.randint(5, 200),
                        deletions=random.randint(0, 80),
                        files_changed=random.randint(1, 8),
                        committed_at=commit_at,
                    )
                )

        db.add_all(events)
        db.add_all(coding)
        db.add_all(commits)
        await db.commit()
        log.info(
            "seed.complete",
            events=len(events),
            coding_sessions=len(coding),
            commits=len(commits),
            email=DEMO_EMAIL,
            password=DEMO_PASSWORD,
        )


if __name__ == "__main__":
    asyncio.run(seed())
