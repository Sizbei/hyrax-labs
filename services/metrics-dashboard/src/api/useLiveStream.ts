/**
 * React hook subscribing to the SSE live-tick stream.
 *
 * Maintains a rolling window of recent aggregate ticks so charts can animate
 * the "real-time" claim. Falls back gracefully if the stream disconnects.
 */
import { useEffect, useRef, useState } from "react";
import type { LiveTick } from "../types";
import { api } from "./client";

export type StreamStatus = "connecting" | "live" | "error";

export interface LiveStreamState {
  status: StreamStatus;
  ticks: LiveTick[];
  latest: LiveTick | null;
}

export function useLiveStream(windowSize = 60): LiveStreamState {
  const [status, setStatus] = useState<StreamStatus>("connecting");
  const [ticks, setTicks] = useState<LiveTick[]>([]);
  const sourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    const source = new EventSource(api.streamUrl());
    sourceRef.current = source;

    source.onopen = () => setStatus("live");
    source.onmessage = (event) => {
      try {
        const tick = JSON.parse(event.data) as LiveTick;
        setStatus("live");
        setTicks((prev) => {
          const next = [...prev, tick];
          return next.length > windowSize ? next.slice(-windowSize) : next;
        });
      } catch {
        // Ignore malformed frames; keep the connection alive.
      }
    };
    source.onerror = () => setStatus("error");

    return () => {
      source.close();
      sourceRef.current = null;
    };
  }, [windowSize]);

  return { status, ticks, latest: ticks.at(-1) ?? null };
}
