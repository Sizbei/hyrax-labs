/** Thin typed client for the synthetic metrics API. */
import type {
  ApiResponse,
  Asset,
  AssetMetricSnapshot,
  MetricDef,
  TimeSeries,
} from "../types";

const BASE = import.meta.env.VITE_API_BASE ?? "/api";

/**
 * Static mode (no backend) is selected at build time with `VITE_STATIC=1`.
 * In static mode all calls are served from the in-browser generator so the
 * dashboard can be hosted on a static CDN (e.g. GitHub Pages).
 */
export const IS_STATIC = import.meta.env.VITE_STATIC === "1";

export interface SnapshotResponse {
  timestamp: number;
  snapshots: AssetMetricSnapshot[];
  aggregates: Record<string, number>;
}

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`Request failed: ${res.status} ${path}`);
  const body = (await res.json()) as ApiResponse<T>;
  if (!body.success || body.data === null) {
    throw new Error(body.error ?? "Unknown API error");
  }
  return body.data;
}

// Lazy import keeps the generator out of the critical path until static mode needs it.
async function staticApi() {
  const { staticSource } = await import("./staticSource");
  return staticSource;
}

export const api = {
  metrics: async (): Promise<MetricDef[]> =>
    IS_STATIC ? (await staticApi()).metrics() : getJson<MetricDef[]>("/metrics"),
  assets: async (): Promise<Asset[]> =>
    IS_STATIC ? (await staticApi()).assets() : getJson<Asset[]>("/assets"),
  snapshot: async (): Promise<SnapshotResponse> =>
    IS_STATIC
      ? (await staticApi()).snapshot()
      : getJson<SnapshotResponse>("/snapshot"),
  timeseries: async (metricId: string, points = 60): Promise<TimeSeries> =>
    IS_STATIC
      ? (await staticApi()).timeseries(metricId, points)
      : getJson<TimeSeries>(`/timeseries/${metricId}?points=${points}`),
  /** Absolute URL for the SSE stream endpoint (HTTP mode only). */
  streamUrl: () => `${BASE}/stream`,
};
