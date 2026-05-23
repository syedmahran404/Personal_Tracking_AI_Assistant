"use client";

/**
 * Realtime client — subscribes to the API's WS channel and turns
 * server events into TanStack Query cache invalidations.
 *
 * Design notes:
 *  - One WS per browser tab; mounted from the protected app layout.
 *  - Auto-reconnect with capped exponential backoff (max 30s).
 *  - Pings every 25s (server echoes "pong") to keep proxies alive.
 *  - When the access token rotates, the socket is closed and re-opened
 *    so the new token is honored.
 *  - Uses `wss://` automatically on https pages.
 */
import * as React from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "@/stores/auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface RealtimeEvent {
  type: string;
  ts?: string;
  [k: string]: unknown;
}

function buildWsUrl(token: string): string {
  // Strip protocol, then prepend ws/wss based on origin.
  const url = new URL(API_URL);
  const proto = url.protocol === "https:" ? "wss:" : "ws:";
  return `${proto}//${url.host}/v1/ws/dashboard?token=${encodeURIComponent(token)}`;
}

export function useRealtime(): { connected: boolean } {
  const qc = useQueryClient();
  const accessToken = useAuthStore((s) => s.accessToken);
  const [connected, setConnected] = React.useState(false);

  React.useEffect(() => {
    if (!accessToken) {
      setConnected(false);
      return;
    }

    let ws: WebSocket | null = null;
    let pingTimer: ReturnType<typeof setInterval> | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let attempt = 0;
    let cancelled = false;

    const handle = (evt: RealtimeEvent) => {
      switch (evt.type) {
        case "dashboard.invalidate":
          qc.invalidateQueries({ queryKey: ["dashboard"] });
          break;
        case "insights.created":
          qc.invalidateQueries({ queryKey: ["insights"] });
          break;
        case "chat.message":
          qc.invalidateQueries({ queryKey: ["chat", "sessions"] });
          if (typeof evt.session_id === "string") {
            qc.invalidateQueries({ queryKey: ["chat", "session", evt.session_id] });
          }
          break;
        case "hello":
        case "pong":
          // No-op; just liveness.
          break;
        default:
          // Unknown event types are ignored to allow forward-compat.
          break;
      }
    };

    const connect = () => {
      if (cancelled) return;
      try {
        ws = new WebSocket(buildWsUrl(accessToken));
      } catch {
        scheduleReconnect();
        return;
      }

      ws.onopen = () => {
        attempt = 0;
        setConnected(true);
        pingTimer = setInterval(() => {
          if (ws?.readyState === WebSocket.OPEN) ws.send("ping");
        }, 25_000);
      };

      ws.onmessage = (e) => {
        // Server may send "pong" as plain text or JSON envelopes.
        if (typeof e.data !== "string") return;
        if (e.data === "pong") return;
        try {
          const parsed = JSON.parse(e.data) as RealtimeEvent;
          if (parsed && typeof parsed.type === "string") handle(parsed);
        } catch {
          // Non-JSON; ignore.
        }
      };

      ws.onerror = () => {
        // The 'close' handler will run; nothing else to do here.
      };

      ws.onclose = () => {
        setConnected(false);
        if (pingTimer) clearInterval(pingTimer);
        pingTimer = null;
        scheduleReconnect();
      };
    };

    const scheduleReconnect = () => {
      if (cancelled) return;
      attempt = Math.min(attempt + 1, 6);
      const delay = Math.min(1000 * 2 ** attempt, 30_000);
      reconnectTimer = setTimeout(connect, delay);
    };

    connect();

    return () => {
      cancelled = true;
      if (pingTimer) clearInterval(pingTimer);
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (ws && ws.readyState <= WebSocket.OPEN) ws.close();
    };
  }, [accessToken, qc]);

  return { connected };
}
