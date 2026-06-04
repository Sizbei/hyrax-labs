/**
 * Dashboard composition root.
 *
 * Loads the metric catalog, synthetic assets and an initial snapshot from the
 * API, then layers a live SSE stream on top for the "real-time" panels.
 */
import { useEffect, useMemo, useState } from "react";
import type { Asset, AssetMetricSnapshot, MetricDef } from "./types";
import { IS_STATIC, api, type SnapshotResponse } from "./api/client";

const REPO_URL = "https://github.com/Sizbei/hyrax-labs";
import { useLiveStream } from "./api/useLiveStream";
import { KpiCard } from "./components/KpiCard";
import { MetricSelect } from "./components/MetricSelect";
import { LiveAreaChart } from "./components/LiveAreaChart";
import { AssetRankBarChart } from "./components/AssetRankBarChart";
import { EngagementHeatmap } from "./components/EngagementHeatmap";
import { CorrelationScatter } from "./components/CorrelationScatter";
import { MetricsTable } from "./components/MetricsTable";

const KPI_IDS = ["views", "engagementRate", "ctr", "conversions"];
const TABLE_IDS = ["views", "likes", "shares", "ctr", "engagementRate", "completionRate"];

export default function App() {
  const [metrics, setMetrics] = useState<MetricDef[]>([]);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [snapshot, setSnapshot] = useState<SnapshotResponse | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [liveMetricId, setLiveMetricId] = useState("views");
  const [rankMetricId, setRankMetricId] = useState("engagementRate");
  const [scatterX, setScatterX] = useState("reach");
  const [scatterY, setScatterY] = useState("engagementRate");

  const { status, ticks, latest } = useLiveStream(60);

  useEffect(() => {
    // In static mode, optionally hydrate assets from a real ingestion-pipeline
    // seed before the first snapshot so scraped material names appear.
    const boot = async () => {
      if (IS_STATIC) {
        const { hydrateFromSeed } = await import("./api/staticSource");
        await hydrateFromSeed();
      }
      return Promise.all([api.metrics(), api.assets(), api.snapshot()]);
    };
    boot()
      .then(([m, a, s]) => {
        setMetrics(m);
        setAssets(a);
        setSnapshot(s);
      })
      .catch((e: unknown) => setLoadError(e instanceof Error ? e.message : "Load failed"));
  }, []);

  const metricById = useMemo(
    () => new Map(metrics.map((m) => [m.id, m])),
    [metrics],
  );

  const liveSeries = useMemo(
    () => ticks.map((t) => ({ timestamp: t.timestamp, value: t.aggregates[liveMetricId] ?? 0 })),
    [ticks, liveMetricId],
  );

  const snapshots: AssetMetricSnapshot[] = snapshot?.snapshots ?? [];

  const kpiDelta = (id: string): number | undefined => {
    if (ticks.length < 2) return undefined;
    const prev = ticks[ticks.length - 2].aggregates[id] ?? 0;
    const cur = ticks[ticks.length - 1].aggregates[id] ?? 0;
    if (prev === 0) return undefined;
    return ((cur - prev) / prev) * 100;
  };

  const kpiValue = (id: string): number =>
    latest?.aggregates[id] ?? snapshot?.aggregates[id] ?? 0;

  if (loadError) {
    return (
      <div className="app-error" role="alert">
        <h1>Could not load metrics</h1>
        <p>{loadError}</p>
        {!IS_STATIC && (
          <p>
            Start the synthetic API with <code>npm run server</code> (or{" "}
            <code>npm run dev</code>).
          </p>
        )}
      </div>
    );
  }

  return (
    <div className="app">
      <header className="app-header">
        <div>
          <h1>Content Performance Dashboard</h1>
          <p className="subtitle">
            Real-time engagement analytics · {assets.length} assets · {metrics.length} metrics
            <span className="synthetic-badge">SYNTHETIC DATA</span>
          </p>
        </div>
        <div className="header-right">
          <div className={`status status-${status}`} data-testid="stream-status">
            <span className="dot" /> {status === "live" ? "Live" : status === "connecting" ? "Connecting…" : "Reconnecting…"}
          </div>
          <a className="source-link" href={REPO_URL} target="_blank" rel="noreferrer noopener">
            View source ↗
          </a>
        </div>
      </header>

      <section className="kpi-row">
        {KPI_IDS.map((id) => {
          const m = metricById.get(id);
          return m ? <KpiCard key={id} metric={m} value={kpiValue(id)} delta={kpiDelta(id)} /> : null;
        })}
      </section>

      <section className="panel panel-wide">
        <div className="panel-head">
          <h2>Live Aggregate Trend</h2>
          <MetricSelect label="Metric" metrics={metrics} value={liveMetricId} onChange={setLiveMetricId} />
        </div>
        {metricById.get(liveMetricId) && (
          <LiveAreaChart metric={metricById.get(liveMetricId)!} series={liveSeries} />
        )}
        {liveSeries.length === 0 && <p className="empty-hint">Waiting for live ticks…</p>}
      </section>

      <div className="grid-2">
        <section className="panel">
          <div className="panel-head">
            <h2>Top Assets</h2>
            <MetricSelect label="Rank by" metrics={metrics} value={rankMetricId} onChange={setRankMetricId} />
          </div>
          {metricById.get(rankMetricId) && (
            <AssetRankBarChart metric={metricById.get(rankMetricId)!} assets={assets} snapshots={snapshots} />
          )}
        </section>

        <section className="panel">
          <div className="panel-head">
            <h2>Engagement by Hour</h2>
          </div>
          <EngagementHeatmap />
        </section>
      </div>

      <section className="panel">
        <div className="panel-head">
          <h2>Metric Correlation</h2>
          <div className="select-pair">
            <MetricSelect label="X" metrics={metrics} value={scatterX} onChange={setScatterX} />
            <MetricSelect label="Y" metrics={metrics} value={scatterY} onChange={setScatterY} />
          </div>
        </div>
        {metricById.get(scatterX) && metricById.get(scatterY) && (
          <CorrelationScatter
            xMetric={metricById.get(scatterX)!}
            yMetric={metricById.get(scatterY)!}
            assets={assets}
            snapshots={snapshots}
          />
        )}
      </section>

      <section className="panel">
        <div className="panel-head">
          <h2>Per-Asset Metrics</h2>
        </div>
        <MetricsTable metrics={metrics} assets={assets} snapshots={snapshots} columnIds={TABLE_IDS} />
      </section>

      <footer className="app-footer">
        Representative portfolio scaffold · all metrics are synthetically generated from a fixed seed · no real analytics data.
      </footer>
    </div>
  );
}
