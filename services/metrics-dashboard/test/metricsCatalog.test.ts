import { describe, it, expect } from "vitest";
import { METRICS, METRIC_IDS, getMetric } from "../src/data/metricsCatalog";

describe("metrics catalog", () => {
  it("defines at least 15 metrics", () => {
    expect(METRICS.length).toBeGreaterThanOrEqual(15);
  });

  it("has unique metric ids", () => {
    expect(new Set(METRIC_IDS).size).toBe(METRIC_IDS.length);
  });

  it("uses valid ranges and formats", () => {
    for (const m of METRICS) {
      expect(m.baseMin).toBeLessThan(m.baseMax);
      expect(["integer", "percent", "duration", "decimal"]).toContain(m.format);
      expect(["reach", "engagement", "retention", "conversion"]).toContain(m.category);
    }
  });

  it("looks up a metric by id", () => {
    expect(getMetric("views")?.label).toBe("Views");
    expect(getMetric("nope")).toBeUndefined();
  });
});
