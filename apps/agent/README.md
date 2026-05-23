# PTAA Agent

A lightweight Electron desktop tracker that lives in your system tray.
Tracks active-window focus events, persists them locally, and ships them
to the backend in batches. Designed to run silently with negligible CPU.

## Architecture

```
┌─────────────┐    sample 5s   ┌───────────┐   batch 30s   ┌───────────┐
│  active-win │ ─────────────► │   SQLite  │ ────────────► │  PTAA API │
└─────────────┘                │  (offline │               └───────────┘
                               │   cache)  │
                               └───────────┘
       ▲                            ▲
       │                            │
   tracker.ts (state machine)   storage.ts (better-sqlite3)
```

- `tracker.ts` polls the foreground window every `samplePeriodMs` (5s).
  Contiguous samples of the same `(app, title)` collapse into a single
  event — no per-second spam. Idle is detected via Electron's
  `powerMonitor.getSystemIdleTime()`.
- `storage.ts` keeps events in a local SQLite database (~/.ptaa-agent).
  Survives crashes and offline periods.
- `sync.ts` flushes to the API every `flushPeriodMs` (30s). On error,
  the buffer is preserved and retried.
- `main.ts` is a tray-only Electron app — no main window unless the user
  clicks "Sign in".

## Local development

```bash
cd apps/agent
npm install
npm run build
npm start
```

The first launch opens a small sign-in window. After login the agent
registers itself as a `Device` against the backend and starts tracking.

## Packaging

```bash
npm run package           # Uses electron-builder → ./release/
```

Targets: `dmg` (mac), `nsis` (Windows), `AppImage` (Linux).

## Configuration

Stored in `~/.config/ptaa-agent/ptaa-agent.json` (encrypted at rest by
electron-store):

| Key | Default | Notes |
|-----|---------|-------|
| `apiUrl` | `http://localhost:8000` | Backend base URL |
| `samplePeriodMs` | `5000` | Active-window poll interval |
| `flushPeriodMs` | `30000` | Sync batch interval |
| `idleThresholdSec` | `90` | Mark events idle after N sec of no input |

## Privacy

- All data is owned by the user; the agent only sends to the backend
  configured by them.
- Window titles are forwarded — they're necessary for accurate
  productivity classification (e.g., Chrome on YouTube vs. on GitHub).
  A future "private mode" will redact titles for selected apps.
