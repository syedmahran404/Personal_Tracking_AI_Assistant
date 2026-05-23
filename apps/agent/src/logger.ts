/**
 * Tiny structured logger — JSON lines to stdout. Sufficient for an agent;
 * piping to a file is the OS's job.
 */
type Level = "debug" | "info" | "warn" | "error";

function emit(level: Level, msg: string, extra?: unknown) {
  const line = {
    ts: new Date().toISOString(),
    level,
    msg,
    ...(extra && typeof extra === "object" ? extra : extra !== undefined ? { extra } : {}),
  };
  // eslint-disable-next-line no-console
  console[level === "debug" ? "log" : level](JSON.stringify(line));
}

export const logger = {
  debug: (msg: string, extra?: unknown) => emit("debug", msg, extra),
  info: (msg: string, extra?: unknown) => emit("info", msg, extra),
  warn: (msg: string, extra?: unknown) => emit("warn", msg, extra),
  error: (msg: string, extra?: unknown) => emit("error", msg, extra),
};
