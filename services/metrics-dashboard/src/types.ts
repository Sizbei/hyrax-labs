/**
 * Shared domain types for the metrics dashboard.
 *
 * NOTE: All data in this project is SYNTHETIC. There are no real analytics,
 * credentials, or company-identifying values anywhere in the codebase.
 */

/** How a metric value should be formatted for display. */
export type MetricFormat = "integer" | "percent" | "duration" | "decimal";

/** A single tracked engagement metric in the catalog. */
export interface MetricDef {
  /** Stable machine key, e.g. "views". */
  id: string;
  /** Human-readable label, e.g. "Views". */
  label: string;
  /** Short description of what the metric represents. */
  description: string;
  /** Display formatting hint. */
  format: MetricFormat;
  /** Logical grouping for UI organization. */
  category: "reach" | "engagement" | "retention" | "conversion";
  /** Typical lower bound used by the synthetic generator. */
  baseMin: number;
  /** Typical upper bound used by the synthetic generator. */
  baseMax: number;
  /** Whether higher is better (affects ranking colors). */
  higherIsBetter: boolean;
}

/** Content type for a synthetic asset/post. */
export type AssetType = "video" | "article" | "image" | "short" | "carousel";

/** A synthetic content asset (a "post"). */
export interface Asset {
  id: string;
  title: string;
  type: AssetType;
  channel: string;
  /** ISO date the asset was published. */
  publishedAt: string;
}

/** A snapshot of all metric values for a single asset at a point in time. */
export interface AssetMetricSnapshot {
  assetId: string;
  /** Epoch milliseconds. */
  timestamp: number;
  /** Keyed by MetricDef.id. */
  values: Record<string, number>;
}

/** One point in a time series for a single metric. */
export interface TimeSeriesPoint {
  timestamp: number;
  value: number;
}

/** A named time series, e.g. aggregate views over time. */
export interface TimeSeries {
  metricId: string;
  points: TimeSeriesPoint[];
}

/** Payload streamed over SSE on each tick. */
export interface LiveTick {
  timestamp: number;
  /** Aggregate (summed/averaged) value per metric id across all assets. */
  aggregates: Record<string, number>;
}

/** Standard API envelope. */
export interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  error: string | null;
}
