/**
 * Local SQLite buffer for offline resilience.
 *
 * All sampled events go here first. The sync loop reads pending events,
 * ships them to the API, and removes them on success. If the device is
 * offline, events accumulate safely until connectivity returns.
 */
import path from "node:path";
import os from "node:os";
import fs from "node:fs";
import Database from "better-sqlite3";

export interface PendingEvent {
  id: number;
  app_name: string;
  window_title: string | null;
  bundle_id: string | null;
  started_at: string; // ISO
  ended_at: string;   // ISO
  is_idle: number;    // 0/1
}

const DATA_DIR =
  process.env.PTAA_DATA_DIR ?? path.join(os.homedir(), ".ptaa-agent");
fs.mkdirSync(DATA_DIR, { recursive: true });

const DB_PATH = path.join(DATA_DIR, "agent.sqlite");

const db = new Database(DB_PATH);
db.pragma("journal_mode = WAL");
db.pragma("synchronous = NORMAL");

db.exec(`
  CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    app_name TEXT NOT NULL,
    window_title TEXT,
    bundle_id TEXT,
    started_at TEXT NOT NULL,
    ended_at TEXT NOT NULL,
    is_idle INTEGER NOT NULL DEFAULT 0
  );
  CREATE INDEX IF NOT EXISTS ix_events_started ON events(started_at);
`);

const insertStmt = db.prepare(`
  INSERT INTO events (app_name, window_title, bundle_id, started_at, ended_at, is_idle)
  VALUES (@app_name, @window_title, @bundle_id, @started_at, @ended_at, @is_idle)
`);

const selectPendingStmt = db.prepare(
  `SELECT * FROM events ORDER BY id ASC LIMIT ?`,
);

const deleteByIdsStmt = (n: number) =>
  db.prepare(`DELETE FROM events WHERE id IN (${Array(n).fill("?").join(",")})`);

export const storage = {
  insert(event: Omit<PendingEvent, "id">) {
    insertStmt.run(event);
  },

  pending(limit = 500): PendingEvent[] {
    return selectPendingStmt.all(limit) as PendingEvent[];
  },

  remove(ids: number[]) {
    if (ids.length === 0) return;
    deleteByIdsStmt(ids.length).run(...ids);
  },

  count(): number {
    const row = db.prepare(`SELECT COUNT(*) AS c FROM events`).get() as { c: number };
    return row.c;
  },

  close() {
    db.close();
  },
};
