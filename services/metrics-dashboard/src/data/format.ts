/** Value formatting helpers driven by MetricDef.format. */
import type { MetricFormat } from "../types";

/** Compact integer formatting, e.g. 12_500 -> "12.5K". */
export function formatCompact(value: number): string {
  const abs = Math.abs(value);
  if (abs >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (abs >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
  return `${Math.round(value)}`;
}

/** Seconds -> "m:ss" or "ss s". */
export function formatDuration(seconds: number): string {
  const s = Math.round(seconds);
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  const rem = s % 60;
  return `${m}:${rem.toString().padStart(2, "0")}`;
}

/** Format a value according to a metric's display format. */
export function formatMetricValue(value: number, format: MetricFormat): string {
  switch (format) {
    case "integer":
      return formatCompact(value);
    case "percent":
      return `${value.toFixed(1)}%`;
    case "duration":
      return formatDuration(value);
    case "decimal":
      return value.toFixed(2);
    default:
      return String(value);
  }
}
