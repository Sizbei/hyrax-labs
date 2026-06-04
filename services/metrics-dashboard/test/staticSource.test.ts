import { afterEach, describe, expect, it, vi } from "vitest";
import { staticSource } from "../src/api/staticSource";
import { METRICS } from "../src/data/metricsCatalog";
import { ASSET_COUNT } from "../src/data/generator";

describe("staticSource (serverless data source)", () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it("exposes the full metric catalog as a mutable copy", () => {
    const metrics = staticSource.metrics();
    expect(metrics).toHaveLength(METRICS.length);
    // Mutating the returned array must not affect the source catalog.
    metrics.pop();
    expect(staticSource.metrics()).toHaveLength(METRICS.length);
  });

  it("generates the full asset set", () => {
    expect(staticSource.assets()).toHaveLength(ASSET_COUNT);
  });

  it("snapshot mirrors the API shape (timestamp, snapshots, aggregates)", () => {
    const snap = staticSource.snapshot();
    expect(typeof snap.timestamp).toBe("number");
    expect(snap.snapshots).toHaveLength(ASSET_COUNT);
    // One aggregate per metric.
    expect(Object.keys(snap.aggregates).length).toBe(METRICS.length);
  });

  it("timeseries returns the requested number of points", () => {
    const series = staticSource.timeseries(METRICS[0].id, 24);
    expect(series.points).toHaveLength(24);
  });

  it("subscribe emits an immediate tick then on the interval, and unsubscribes", () => {
    vi.useFakeTimers();
    const ticks: number[] = [];
    const unsubscribe = staticSource.subscribe((t) => ticks.push(t.timestamp), 1000);

    expect(ticks).toHaveLength(1); // immediate first frame
    vi.advanceTimersByTime(3000);
    expect(ticks).toHaveLength(4); // + 3 interval frames

    unsubscribe();
    vi.advanceTimersByTime(5000);
    expect(ticks).toHaveLength(4); // no more after unsubscribe
  });
});
