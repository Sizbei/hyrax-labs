import { describe, it, expect } from "vitest";
import {
  formatCompact,
  formatDuration,
  formatMetricValue,
} from "../src/data/format";

describe("formatters", () => {
  it("formats compact integers", () => {
    expect(formatCompact(950)).toBe("950");
    expect(formatCompact(12500)).toBe("12.5K");
    expect(formatCompact(2_400_000)).toBe("2.4M");
  });

  it("formats durations", () => {
    expect(formatDuration(45)).toBe("45s");
    expect(formatDuration(125)).toBe("2:05");
  });

  it("routes formatting by metric format", () => {
    expect(formatMetricValue(3.456, "percent")).toBe("3.5%");
    expect(formatMetricValue(1500, "integer")).toBe("1.5K");
    expect(formatMetricValue(90, "duration")).toBe("1:30");
    expect(formatMetricValue(2.5, "decimal")).toBe("2.50");
  });
});
