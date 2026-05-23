# Personal Tracking AI Assistant

> A production-grade, AI-powered productivity intelligence system. Track app usage, coding sessions, and habits — get personalized insights, focus scores, and an AI assistant that understands your work patterns.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org)
[![Electron](https://img.shields.io/badge/Electron-29-47848F)](https://electronjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791)](https://postgresql.org)

## Architecture

```
┌────────────────────┐      ┌──────────────────────┐      ┌────────────────────┐
│  Desktop Agent     │      │   Web Dashboard      │      │   AI Assistant     │
│  (Electron + TS)   │      │  (Next.js 14 + TS)   │      │  (Chat + Insights) │
│                    │      │                      │      │                    │
│ • active-window    │      │ • Dashboard          │      │ • Tool calling     │
│ • idle detection   │      │ • Analytics          │      │ • Memory/context   │
│ • offline cache    │      │ • Charts/Heatmaps    │      │ • Weekly reports   │
│ • encrypted sync   │      │ • AI Chat UI         │      │ • Recommendations  │
└─────────┬──────────┘      └──────────┬───────────┘      └─────────┬──────────┘
          │ HTTPS + JWT                │ HTTPS + JWT                │
          │                            │                            │
          └────────────────┬───────────┴────────────────────────────┘
                           │
                ┌──────────▼──────────────┐
                │   FastAPI Backend       │
                │                         │
                │ • Auth (JWT + refresh)  │
                │ • Tracking ingestion    │
                │ • Analytics engine      │
                │ • AI service layer      │
                │ • WebSocket realtime    │
                │ • Rate limiting         │
                └──────────┬──────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
   ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
   │ PostgreSQL  │  │   Redis     │  │  LLM API    │
   │ (primary)   │  │ (cache+pub) │  │ (provider   │
   │             │  │             │  │  abstracted)│
   └─────────────┘  └─────────────┘  └─────────────┘
```

## Monorepo layout

```
Personal_Tracking_AI_Assistant/
├── apps/
│   ├── api/              # FastAPI backend (Python 3.11)
│   ├── web/              # Next.js 14 frontend (TypeScript)
│   └── agent/            # Electron desktop tracker (TypeScript)
├── packages/
│   └── shared/           # Shared TS types between web + agent
├── infra/
│   ├── nginx/            # Reverse proxy config
│   └── postgres/         # Init scripts
├── docker-compose.yml    # Full local stack
├── .env.example          # Root env template
└── README.md
```

## Quick start

```bash
# 1. Copy env files
cp .env.example .env
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env.local

# 2. Spin up backend stack (Postgres + Redis + API + Web)
docker compose up -d --build

# 3. Run migrations + seed
docker compose exec api alembic upgrade head
docker compose exec api python -m app.scripts.seed

# 4. Run desktop agent locally (after creating an account in the web UI)
cd apps/agent && npm install && npm run dev
```

Visit:
- Web dashboard: http://localhost:3000
- API docs:      http://localhost:8000/docs
- API health:    http://localhost:8000/health

## Tech stack

| Layer            | Choice                                           |
|------------------|--------------------------------------------------|
| Frontend         | Next.js 14 (App Router), TypeScript, TailwindCSS |
| UI components    | ShadCN UI, Radix, Framer Motion, Recharts        |
| Backend          | FastAPI, Pydantic v2, SQLAlchemy 2.0 (async)     |
| Database         | PostgreSQL 16                                    |
| Cache / pub-sub  | Redis 7                                          |
| Auth             | JWT (access + refresh), bcrypt, Argon2 ready     |
| Realtime         | WebSockets                                       |
| Desktop agent    | Electron 29, active-win, better-sqlite3          |
| AI               | Provider-abstracted (OpenAI / Anthropic / local) |
| Infra            | Docker, docker-compose, Nginx                    |

## Features

- Secure JWT auth (access + refresh, rotation, device binding)
- App usage tracking with productivity classification
- Coding session tracking (language detection, project tracking, git commits)
- Focus score & productivity score algorithms
- Deep work detection, idle detection, session segmentation
- AI insights: weekly summaries, distraction analysis, burnout detection
- AI chat assistant with tool calling over your own analytics
- Real-time dashboard with charts, heatmaps, streaks
- Dark/light theme, responsive, premium SaaS UI
- Background desktop agent (Windows/macOS/Linux) with offline cache

## Documentation

- [Backend API reference](apps/api/README.md)
- [Frontend guide](apps/web/README.md)
- [Desktop agent guide](apps/agent/README.md)

## License

MIT
