import { describe, it, expect } from "vitest";
import {
  ASSET_COUNT,
  DEFAULT_SEED,
  aggregate,
  generateAssets,
  generateTimeSeries,
  liveTick,
  snapshotAll,
  snapshotForAsset,
} from "../src/data/generator";
import { METRICS } from "../src/data/metricsCatalog";

describe("synthetic data generator", () => {
  it("produces 100+ assets", () => {
    const assets = generateAssets(DEFAULT_SEED);
    expect(assets.length).toBe(ASSET_COUNT);
    expect(assets.length).toBeGreaterThanOrEqual(100);
  });

  it("is deterministic for a given seed", () => {
    const a = generateAssets(42);
    const b = generateAssets(42);
    expect(a).toEqual(b);
  });

  it("produces different assets for different seeds", () => {
    const a = generateAssets(1);
    const b = generateAssets(2);
    expect(a[0]).not.toEqual(b[0]);
  });

  it("snapshots every metric within its catalog bounds", () => {
    const [asset] = generateAssets(DEFAULT_SEED);
    const snap = snapshotForAsset(asset, Date.now(), 0);
    for (const metric of METRICS) {
      const v = snap.values[metric.id];
      expect(v).toBeGreaterThanOrEqual(metric.baseMin);
      expect(v).toBeLessThanOrEqual(metric.baseMax);
    }
  });

  it("aggregates a value for every metric in the catalog", () => {
    const assets = generateAssets(DEFAULT_SEED);
    const totals = aggregate(snapshotAll(assets, Date.now(), 0));
    for (const metric of METRICS) {
      expect(totals).toHaveProperty(metric.id);
      expect(Number.isFinite(totals[metric.id])).toBe(true);
    }
  });

  it("builds time series of the requested length", () => {
    const assets = generateAssets(DEFAULT_SEED);
    const ts = generateTimeSeries(assets, "views", Date.now(), 24);
    expect(ts.metricId).toBe("views");
    expect(ts.points).toHaveLength(24);
    expect(ts.points[0].timestamp).toBeLessThan(ts.points[23].timestamp);
  });

  it("changes live tick aggregates as the tick advances", () => {
    const assets = generateAssets(DEFAULT_SEED);
    const now = Date.now();
    const t1 = liveTick(assets, now, 1);
    const t2 = liveTick(assets, now + 60000, 8);
    expect(t1.aggregates.views).not.toBe(t2.aggregates.views);
  });
});
