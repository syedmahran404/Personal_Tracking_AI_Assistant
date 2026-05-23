/**
 * Sync loop: drains the local SQLite buffer to the API in batches.
 *
 * - Batches up to 200 events per call.
 * - Flushes the in-flight tracker event first so nothing lingers >flushPeriod.
 * - Removes only the events that were successfully shipped.
 * - On error, leaves the buffer intact and logs — next tick retries.
 */
import { api } from "./api";
import { config } from "./config";
import { logger } from "./logger";
import { storage } from "./storage";
import { tracker } from "./tracker";

let timer: NodeJS.Timeout | null = null;

async function flushOnce(): Promise<{ pushed: number; pending: number }> {
  tracker.flushOpen();

  const pending = storage.pending(200);
  if (pending.length === 0) return { pushed: 0, pending: 0 };

  const deviceId = config.get("deviceId");
  try {
    await api.ingestEvents(
      pending.map((e) => ({
        app_name: e.app_name,
        window_title: e.window_title,
        bundle_id: e.bundle_id,
        started_at: e.started_at,
        ended_at: e.ended_at,
        is_idle: e.is_idle === 1,
      })),
      deviceId,
    );
    storage.remove(pending.map((e) => e.id));
    return { pushed: pending.length, pending: storage.count() };
  } catch (err) {
    logger.warn("sync.push_failed", { error: (err as Error).message });
    return { pushed: 0, pending: storage.count() };
  }
}

export const sync = {
  start() {
    if (timer) return;
    const period = config.get("flushPeriodMs");
    logger.info("sync.start", { flushPeriodMs: period });
    timer = setInterval(async () => {
      const r = await flushOnce();
      if (r.pushed > 0) logger.info("sync.flushed", r);
    }, period);
    // Trigger a first flush shortly after boot so any leftover offline
    // events ship promptly.
    setTimeout(() => void flushOnce(), 5_000);
  },

  stop() {
    if (timer) clearInterval(timer);
    timer = null;
    logger.info("sync.stop");
  },

  flushNow: flushOnce,
};
