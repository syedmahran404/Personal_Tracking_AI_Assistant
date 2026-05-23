/**
 * Active-window tracker.
 *
 * Strategy:
 *  - Sample the foreground window every `samplePeriodMs` (default 5s).
 *  - Coalesce contiguous samples of the same (app, title) into one event.
 *  - When the window changes (or a flush boundary is crossed), persist
 *    the closed event to local SQLite.
 *  - Idle is detected via Electron's powerMonitor.getSystemIdleTime() —
 *    when idle exceeds a threshold the event is marked `is_idle=true`.
 *
 * This loop is intentionally simple and synchronous w.r.t. its own state
 * machine — it should never miss or double-count an event.
 */
import { powerMonitor } from "electron";
import { config } from "./config";
import { logger } from "./logger";
import { storage } from "./storage";

interface ActiveWindowInfo {
  owner: { name: string; bundleId?: string; processId: number };
  title: string;
  id: number;
  bounds: unknown;
}

type ActiveWinFn = () => Promise<ActiveWindowInfo | undefined>;

interface OpenEvent {
  app_name: string;
  window_title: string | null;
  bundle_id: string | null;
  started_at: Date;
  is_idle: boolean;
}

let openEvent: OpenEvent | null = null;
let timer: NodeJS.Timeout | null = null;
let activeWin: ActiveWinFn | null = null;

async function loadActiveWin(): Promise<ActiveWinFn | null> {
  if (activeWin) return activeWin;
  try {
    // active-win is ESM-only; we lazy-import.
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const mod = await import("active-win");
    activeWin = mod.default as unknown as ActiveWinFn;
    return activeWin;
  } catch (err) {
    logger.error("tracker.active_win_unavailable", err);
    return null;
  }
}

function sameWindow(a: OpenEvent, info: ActiveWindowInfo, isIdle: boolean): boolean {
  return (
    a.app_name === info.owner.name &&
    a.window_title === (info.title ?? null) &&
    a.is_idle === isIdle
  );
}

function closeAndStore(end: Date) {
  if (!openEvent) return;
  // Skip zero-duration events (clock skew, etc).
  const duration = end.getTime() - openEvent.started_at.getTime();
  if (duration < 1000) {
    openEvent = null;
    return;
  }
  storage.insert({
    app_name: openEvent.app_name,
    window_title: openEvent.window_title,
    bundle_id: openEvent.bundle_id,
    started_at: openEvent.started_at.toISOString(),
    ended_at: end.toISOString(),
    is_idle: openEvent.is_idle ? 1 : 0,
  });
  openEvent = null;
}

async function tick() {
  const fn = await loadActiveWin();
  if (!fn) return;

  let info: ActiveWindowInfo | undefined;
  try {
    info = await fn();
  } catch (err) {
    logger.warn("tracker.poll_failed", err);
    return;
  }
  if (!info?.owner) return;

  const idleSec = powerMonitor.getSystemIdleTime();
  const isIdle = idleSec >= config.get("idleThresholdSec");
  const now = new Date();

  if (openEvent && sameWindow(openEvent, info, isIdle)) {
    return; // still the same focused window — extend implicitly
  }

  // Window or idle-state changed — close the previous open event.
  closeAndStore(now);

  openEvent = {
    app_name: info.owner.name,
    window_title: info.title ?? null,
    bundle_id: info.owner.bundleId ?? null,
    started_at: now,
    is_idle: isIdle,
  };
}

export const tracker = {
  start() {
    if (timer) return;
    const period = config.get("samplePeriodMs");
    logger.info("tracker.start", { samplePeriodMs: period });
    timer = setInterval(() => void tick(), period);
    void tick();
  },

  stop() {
    if (timer) clearInterval(timer);
    timer = null;
    closeAndStore(new Date());
    logger.info("tracker.stop");
  },

  /** Force-close the open event so it's eligible for sync. */
  flushOpen() {
    if (openEvent) closeAndStore(new Date());
  },
};
