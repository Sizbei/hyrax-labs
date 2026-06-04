/**
 * React hook supplying a rolling window of live aggregate ticks so charts can
 * animate the "real-time" claim.
 *
 * - HTTP mode: subscribes to the server's SSE stream (EventSource).
 * - Static mode (VITE_STATIC=1): subscribes to a client-side interval over the
 *   same `liveTick` generator the server uses — identical data, no backend.
 */
import { useEffect, useState } from "react";
import type { LiveTick } from "../types";
import { IS_STATIC, api } from "./client";

export type StreamStatus = "connecting" | "live" | "error";

export interface LiveStreamState {
  status: StreamStatus;
  ticks: LiveTick[];
  latest: LiveTick | null;
}

export function useLiveStream(windowSize = 60): LiveStreamState {
  const [status, setStatus] = useState<StreamStatus>("connecting");
  const [ticks, setTicks] = useState<LiveTick[]>([]);

  useEffect(() => {
    const pushTick = (tick: LiveTick) => {
      setStatus("live");
      setTicks((prev) => {
        const next = [...prev, tick];
        return next.length > windowSize ? next.slice(-windowSize) : next;
      });
    };

    // ── Static mode: client-side ticks, no server. ──
    if (IS_STATIC) {
      let unsubscribe: (() => void) | undefined;
      let cancelled = false;
      import("./staticSource").then(({ staticSource }) => {
        if (cancelled) return;
        unsubscribe = staticSource.subscribe(pushTick);
      });
      return () => {
        cancelled = true;
        unsubscribe?.();
      };
    }

    // ── HTTP mode: real Server-Sent Events. ──
    const source = new EventSource(api.streamUrl());
    source.onopen = () => setStatus("live");
    source.onmessage = (event) => {
      try {
        pushTick(JSON.parse(event.data) as LiveTick);
      } catch {
        // Ignore malformed frames; keep the connection alive.
      }
    };
    source.onerror = () => setStatus("error");
    return () => {
      source.close();
    };
  }, [windowSize]);

  return { status, ticks, latest: ticks.at(-1) ?? null };
}
