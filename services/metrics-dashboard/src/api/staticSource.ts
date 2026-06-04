/**
 * Static (serverless) data source.
 *
 * Mirrors the Express API contract exactly, but generates everything in the
 * browser from the same deterministic generator the server uses. This lets the
 * dashboard run as a pure static SPA (e.g. on GitHub Pages) with no backend —
 * the "live" stream is driven by a client-side interval over `liveTick`, the
 * identical function the server's SSE endpoint calls.
 *
 * SYNTHETIC ONLY: no real analytics; same seed → same data as the server.
 */
import { METRICS } from "../data/metricsCatalog.ts";
import {
  DEFAULT_SEED,
  aggregate,
  generateAssets,
  generateTimeSeries,
  liveTick,
  snapshotAll,
} from "../data/generator.ts";
import type { Asset, LiveTick, MetricDef, TimeSeries } from "../types";
import type { SnapshotResponse } from "./client";

const assets: Asset[] = generateAssets(DEFAULT_SEED);

export const staticSource = {
  metrics(): MetricDef[] {
    return [...METRICS];
  },
  assets(): Asset[] {
    return assets;
  },
  snapshot(): SnapshotResponse {
    const now = Date.now();
    const snapshots = snapshotAll(assets, now, 0);
    return { timestamp: now, snapshots, aggregates: aggregate(snapshots) };
  },
  timeseries(metricId: string, points = 60): TimeSeries {
    return generateTimeSeries(assets, metricId, Date.now(), points);
  },
  /**
   * Subscribe to client-generated live ticks. Returns an unsubscribe fn.
   * `intervalMs` mirrors the server's STREAM_INTERVAL_MS default.
   */
  subscribe(onTick: (tick: LiveTick) => void, intervalMs = 2000): () => void {
    let n = 0;
    const emit = () => {
      n += 1;
      onTick(liveTick(assets, Date.now(), n));
    };
    emit(); // immediate first frame, like the SSE endpoint
    const timer = setInterval(emit, intervalMs);
    return () => clearInterval(timer);
  },
};
