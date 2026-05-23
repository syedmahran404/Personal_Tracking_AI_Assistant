"use client";

import { useRealtime } from "@/hooks/use-realtime";

/**
 * Mounts the realtime hook for the entire authenticated app surface.
 *
 * Lives in its own client component so the (app) layout can stay a
 * server component for route-level prefetch/streaming benefits.
 */
export function RealtimeBridge() {
  useRealtime();
  return null;
}
