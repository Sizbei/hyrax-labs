/**
 * Deterministic synthetic data generator.
 *
 * Produces 100+ assets, a metric snapshot per asset, and time series — all
 * derived from a fixed seed so the client and server agree on the dataset.
 * SYNTHETIC ONLY: no real analytics data is used or implied.
 */
import type {
  Asset,
  AssetMetricSnapshot,
  AssetType,
  LiveTick,
  TimeSeries,
} from "../types";
import { METRICS } from "./metricsCatalog.ts";
import { createRng, hashString, pick, randInt, randRange } from "./random.ts";

export const DEFAULT_SEED = 1337;
export const ASSET_COUNT = 120;

const ASSET_TYPES: readonly AssetType[] = [
  "video",
  "article",
  "image",
  "short",
  "carousel",
];

const CHANNELS: readonly string[] = [
  "Web",
  "Mobile App",
  "Newsletter",
  "Social",
  "Partner",
];

const TITLE_NOUNS = [
  "Onboarding",
  "Release Notes",
  "Case Study",
  "Tutorial",
  "Deep Dive",
  "Roundup",
  "Walkthrough",
  "Benchmark",
  "Retrospective",
  "Field Guide",
  "Playbook",
  "Teardown",
];

const TITLE_TOPICS = [
  "Pipelines",
  "Caching",
  "Latency",
  "Schemas",
  "Streaming",
  "Indexing",
  "Telemetry",
  "Throughput",
  "Sharding",
  "Backpressure",
];

/** Quality factor in [0.4, 1.0] that biases an asset's metrics up or down. */
function assetQuality(assetId: string): number {
  const rng = createRng(hashString(`${assetId}:quality`));
  return 0.4 + rng() * 0.6;
}

/** Build the deterministic set of assets. */
export function generateAssets(seed: number = DEFAULT_SEED): Asset[] {
  const rng = createRng(seed);
  const assets: Asset[] = [];
  const start = Date.UTC(2025, 0, 1);
  const dayMs = 86_400_000;

  for (let i = 0; i < ASSET_COUNT; i += 1) {
    const id = `asset-${String(i + 1).padStart(3, "0")}`;
    const publishedAt = new Date(
      start + randInt(rng, 0, 480) * dayMs,
    ).toISOString();
    assets.push({
      id,
      title: `${pick(rng, TITLE_NOUNS)}: ${pick(rng, TITLE_TOPICS)} #${i + 1}`,
      type: pick(rng, ASSET_TYPES),
      channel: pick(rng, CHANNELS),
      publishedAt,
    });
  }
  return assets;
}

/**
 * Compute the metric values for a single asset at a given time.
 * `tick` advances values smoothly so "real-time" updates look organic.
 */
export function snapshotForAsset(
  asset: Asset,
  timestamp: number,
  tick = 0,
): AssetMetricSnapshot {
  const quality = assetQuality(asset.id);
  const values: Record<string, number> = {};

  for (const metric of METRICS) {
    const rng = createRng(hashString(`${asset.id}:${metric.id}`));
    const span = metric.baseMax - metric.baseMin;
    // Base position biased by asset quality.
    const base = metric.baseMin + span * (0.2 + quality * randRange(rng, 0.4, 0.8));
    // Slow sine wobble + tiny per-tick drift => animated but bounded.
    const phase = (hashString(metric.id) % 100) / 100;
    const wobble =
      Math.sin((timestamp / 60000 + tick * 0.35 + phase) * Math.PI) * span * 0.04;
    let value = base + wobble;
    if (!metric.higherIsBetter) {
      // Invert so quality still means "good" for inverse metrics.
      value = metric.baseMax - (value - metric.baseMin);
    }
    value = Math.max(metric.baseMin, Math.min(metric.baseMax, value));
    values[metric.id] =
      metric.format === "integer" ? Math.round(value) : Number(value.toFixed(2));
  }
  return { assetId: asset.id, timestamp, values };
}

/** Snapshot every asset at a point in time. */
export function snapshotAll(
  assets: Asset[],
  timestamp: number,
  tick = 0,
): AssetMetricSnapshot[] {
  return assets.map((a) => snapshotForAsset(a, timestamp, tick));
}

/** Aggregate metric values across assets (sum for counts, mean for rates). */
export function aggregate(
  snapshots: AssetMetricSnapshot[],
): Record<string, number> {
  const totals: Record<string, number> = {};
  for (const metric of METRICS) {
    const isRate = metric.format === "percent" || metric.format === "duration";
    let acc = 0;
    for (const snap of snapshots) acc += snap.values[metric.id] ?? 0;
    totals[metric.id] = isRate
      ? Number((acc / Math.max(1, snapshots.length)).toFixed(2))
      : Math.round(acc);
  }
  return totals;
}

/** Build a historical time series for one metric leading up to `now`. */
export function generateTimeSeries(
  assets: Asset[],
  metricId: string,
  now: number,
  pointCount = 60,
  stepMs = 60_000,
): TimeSeries {
  const points = [];
  for (let i = pointCount - 1; i >= 0; i -= 1) {
    const ts = now - i * stepMs;
    const snaps = snapshotAll(assets, ts, pointCount - i);
    points.push({ timestamp: ts, value: aggregate(snaps)[metricId] ?? 0 });
  }
  return { metricId, points };
}

/** Produce a single live tick aggregate for SSE streaming. */
export function liveTick(assets: Asset[], timestamp: number, tick: number): LiveTick {
  return { timestamp, aggregates: aggregate(snapshotAll(assets, timestamp, tick)) };
}
