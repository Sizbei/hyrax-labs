/** Thin typed client for the synthetic metrics API. */
import type {
  ApiResponse,
  Asset,
  AssetMetricSnapshot,
  MetricDef,
  TimeSeries,
} from "../types";

const BASE = import.meta.env.VITE_API_BASE ?? "/api";

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`Request failed: ${res.status} ${path}`);
  const body = (await res.json()) as ApiResponse<T>;
  if (!body.success || body.data === null) {
    throw new Error(body.error ?? "Unknown API error");
  }
  return body.data;
}

export interface SnapshotResponse {
  timestamp: number;
  snapshots: AssetMetricSnapshot[];
  aggregates: Record<string, number>;
}

export const api = {
  metrics: () => getJson<MetricDef[]>("/metrics"),
  assets: () => getJson<Asset[]>("/assets"),
  snapshot: () => getJson<SnapshotResponse>("/snapshot"),
  timeseries: (metricId: string, points = 60) =>
    getJson<TimeSeries>(`/timeseries/${metricId}?points=${points}`),
  /** Absolute URL for the SSE stream endpoint. */
  streamUrl: () => `${BASE}/stream`,
};
