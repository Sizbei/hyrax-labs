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
  ASSET_COUNT,
  DEFAULT_SEED,
  aggregate,
  generateAssets,
  generateTimeSeries,
  liveTick,
  snapshotAll,
} from "../data/generator.ts";
import type { Asset, LiveTick, MetricDef, TimeSeries } from "../types";
import type { SnapshotResponse } from "./client";

const generated: Asset[] = generateAssets(DEFAULT_SEED);

// Assets default to the generated set, but may be augmented at load time with a
// real ingestion-pipeline seed (assets-seed.json) so the live dashboard shows
// the actual scraped supplier-material names — the end-to-end flow, in browser.
let assets: Asset[] = generated;

/**
 * Try to load an ingestion-pipeline asset seed and prepend it to the generated
 * assets. The result is capped at max(ASSET_COUNT, seed length) so a normal
 * (small) seed stays within the usual ~120-asset view. No-ops if the file is
 * absent or invalid. Idempotent; safe to call once at startup.
 */
export async function hydrateFromSeed(
  url = `${import.meta.env.BASE_URL}assets-seed.json`,
): Promise<number> {
  try {
    const res = await fetch(url);
    if (!res.ok) return 0;
    const seed = (await res.json()) as Asset[];
    if (!Array.isArray(seed) || seed.length === 0) return 0;
    const seeded = seed.filter(
      (a) => a && typeof a.id === "string" && typeof a.title === "string",
    );
    if (seeded.length === 0) return 0;
    const seededIds = new Set(seeded.map((a) => a.id));
    const filler = generated.filter((a) => !seededIds.has(a.id));
    assets = [...seeded, ...filler].slice(0, Math.max(ASSET_COUNT, seeded.length));
    return seeded.length;
  } catch {
    return 0; // network/JSON failure → keep generated assets
  }
}

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
