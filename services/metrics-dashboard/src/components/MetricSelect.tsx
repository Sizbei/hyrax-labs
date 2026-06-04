/** Labeled dropdown for choosing a metric from the catalog. */
import type { MetricDef } from "../types";

export interface MetricSelectProps {
  label: string;
  metrics: MetricDef[];
  value: string;
  onChange: (id: string) => void;
}

export function MetricSelect({ label, metrics, value, onChange }: MetricSelectProps) {
  return (
    <label className="metric-select">
      <span>{label}</span>
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        {metrics.map((m) => (
          <option key={m.id} value={m.id}>
            {m.label}
          </option>
        ))}
      </select>
    </label>
  );
}
