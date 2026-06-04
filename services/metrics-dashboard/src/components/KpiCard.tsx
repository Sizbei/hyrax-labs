/** Compact KPI card showing a single live aggregate value. */
import type { MetricDef } from "../types";
import { formatMetricValue } from "../data/format";

export interface KpiCardProps {
  metric: MetricDef;
  value: number;
  /** Percentage change vs the previous tick. */
  delta?: number;
}

export function KpiCard({ metric, value, delta }: KpiCardProps) {
  const positive = (delta ?? 0) >= 0;
  const goodDirection = positive === metric.higherIsBetter;
  return (
    <div className="kpi-card" data-testid={`kpi-${metric.id}`}>
      <div className="kpi-label" title={metric.description}>
        {metric.label}
      </div>
      <div className="kpi-value">{formatMetricValue(value, metric.format)}</div>
      {delta !== undefined && (
        <div className={`kpi-delta ${goodDirection ? "good" : "bad"}`}>
          {positive ? "▲" : "▼"} {Math.abs(delta).toFixed(2)}%
        </div>
      )}
    </div>
  );
}
