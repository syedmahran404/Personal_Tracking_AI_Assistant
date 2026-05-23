# PTAA API — FastAPI Backend

## Local development

```bash
# 1. Create venv + install
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Configure env
cp .env.example .env

# 3. Bring up Postgres + Redis (from repo root)
docker compose up -d postgres redis

# 4. Apply migrations + seed demo data
alembic upgrade head
python -m app.scripts.seed   # creates demo@ptaa.dev + 14 days of data

# 5. Run dev server
uvicorn app.main:app --reload
```

API docs: <http://localhost:8000/docs>

## Schema migrations

The schema baseline lives at `alembic/versions/20260101_0000_a1b2c3d4e5f6_initial_schema.py`.
After modifying any model in `app/models/`:

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

For a clean dev environment (no migrations), `python -m app.scripts.init_db` will
`create_all` the tables directly from the ORM metadata.

## Demo credentials (after seed)

```
email:    demo@ptaa.dev
password: demo12345
```

## API surface (v1)

| Method | Path | Description |
|--------|------|-------------|
| POST   | `/v1/auth/signup`            | Create account |
| POST   | `/v1/auth/login`             | Get tokens |
| POST   | `/v1/auth/refresh`           | Rotate refresh token |
| POST   | `/v1/auth/logout`            | Revoke all tokens |
| GET    | `/v1/users/me`               | Current user |
| PATCH  | `/v1/users/me`               | Update profile |
| POST   | `/v1/devices`                | Register device |
| GET    | `/v1/devices`                | List devices |
| POST   | `/v1/tracking/events`        | Batch ingest app-usage events |
| POST   | `/v1/tracking/coding-sessions` | Submit a coding session |
| POST   | `/v1/tracking/git-commits`   | Submit a git commit (idempotent) |
| GET    | `/v1/analytics/dashboard`    | Dashboard summary |
| GET    | `/v1/insights`               | List insights |
| POST   | `/v1/insights/generate/weekly` | Generate weekly summary (LLM) |
| POST   | `/v1/insights/scan/distraction` | Run heuristic distraction scan |
| GET    | `/v1/chat/sessions`          | List chat sessions |
| GET    | `/v1/chat/sessions/{id}`     | Chat session detail |
| POST   | `/v1/chat/send`              | Send a chat message |
| WS     | `/v1/ws/dashboard?token=…`   | Realtime updates |

## Design notes

- **Auth**: JWT access (30 min) + refresh (30 day) with strict rotation.
  Refresh tokens are persisted; replay of a revoked one revokes all
  tokens for the user.
- **Tracking ingestion** is `202 Accepted` and batched. The agent buffers
  events locally and flushes every ~30s.
- **Analytics** queries push aggregation down to Postgres; for very large
  installs swap the events table for a TimescaleDB hypertable without
  changing the public API.
- **AI** is provider-abstracted (`app/ai/providers.py`). Default is a
  deterministic mock so the system runs end-to-end without an API key.
- **Rate limiting** keys on user_id when authenticated, falls back to IP.
