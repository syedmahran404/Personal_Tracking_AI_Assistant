/**
 * Agent runtime configuration.
 *
 * Persisted via electron-store. The window for first-time setup is
 * the API URL + access token; users sign in once via the web app and
 * paste the token, or use the in-app sign-in flow.
 */
import os from "node:os";
import Store from "electron-store";

export interface AgentConfig {
  apiUrl: string;
  accessToken: string | null;
  refreshToken: string | null;
  deviceId: string | null;
  deviceName: string;
  // Sampling: poll active-window every `samplePeriodMs`; flush events every `flushPeriodMs`
  samplePeriodMs: number;
  flushPeriodMs: number;
  // Idle threshold: if user input is idle for this long, mark events as is_idle
  idleThresholdSec: number;
}

const DEFAULTS: AgentConfig = {
  apiUrl: process.env.PTAA_API_URL ?? "http://localhost:8000",
  accessToken: null,
  refreshToken: null,
  deviceId: null,
  deviceName: os.hostname(),
  samplePeriodMs: 5_000,
  flushPeriodMs: 30_000,
  idleThresholdSec: 90,
};

const store = new Store<AgentConfig>({
  name: "ptaa-agent",
  defaults: DEFAULTS,
  // Encrypt at rest. Not bulletproof — prevents casual filesystem reads.
  encryptionKey: "ptaa-local-keying",
  clearInvalidConfig: true,
});

export const config = {
  get<K extends keyof AgentConfig>(key: K): AgentConfig[K] {
    return store.get(key);
  },
  set<K extends keyof AgentConfig>(key: K, value: AgentConfig[K]): void {
    store.set(key, value);
  },
  all(): AgentConfig {
    return store.store;
  },
  reset(): void {
    store.clear();
  },
};
