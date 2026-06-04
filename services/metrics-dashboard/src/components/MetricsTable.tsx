/**
 * Sortable, filterable per-asset metrics table.
 * Pure React (no D3 needed) — complements the SVG charts.
 */
import { useMemo, useState } from "react";
import type { Asset, AssetMetricSnapshot, MetricDef } from "../types";
import { formatMetricValue } from "../data/format";

export interface MetricsTableProps {
  metrics: MetricDef[];
  assets: Asset[];
  snapshots: AssetMetricSnapshot[];
  /** Metric ids shown as columns. */
  columnIds: string[];
}

type SortDir = "asc" | "desc";

export function MetricsTable({ metrics, assets, snapshots, columnIds }: MetricsTableProps) {
  const [query, setQuery] = useState("");
  const [sortKey, setSortKey] = useState<string>(columnIds[0] ?? "title");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  const columns = useMemo(
    () => columnIds.map((id) => metrics.find((m) => m.id === id)).filter(Boolean) as MetricDef[],
    [columnIds, metrics],
  );

  const rows = useMemo(() => {
    const valueById = new Map(snapshots.map((s) => [s.assetId, s.values]));
    const built = assets.map((a) => ({
      asset: a,
      values: valueById.get(a.id) ?? {},
    }));
    const filtered = query.trim()
      ? built.filter(
          (r) =>
            r.asset.title.toLowerCase().includes(query.toLowerCase()) ||
            r.asset.channel.toLowerCase().includes(query.toLowerCase()) ||
            r.asset.type.toLowerCase().includes(query.toLowerCase()),
        )
      : built;

    const sorted = [...filtered].sort((a, b) => {
      let av: number | string;
      let bv: number | string;
      if (sortKey === "title") {
        av = a.asset.title;
        bv = b.asset.title;
      } else {
        av = a.values[sortKey] ?? 0;
        bv = b.values[sortKey] ?? 0;
      }
      const cmp = typeof av === "string" ? av.localeCompare(bv as string) : av - (bv as number);
      return sortDir === "asc" ? cmp : -cmp;
    });
    return sorted.slice(0, 30);
  }, [assets, snapshots, query, sortKey, sortDir]);

  const toggleSort = (key: string) => {
    if (key === sortKey) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  };

  const arrow = (key: string) => (key === sortKey ? (sortDir === "asc" ? " ▲" : " ▼") : "");

  return (
    <div className="table-wrap" data-testid="metrics-table">
      <input
        className="table-filter"
        type="search"
        placeholder="Filter assets by title, channel, or type…"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        aria-label="Filter assets"
      />
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th onClick={() => toggleSort("title")} className="sortable">
                Asset{arrow("title")}
              </th>
              {columns.map((c) => (
                <th key={c.id} onClick={() => toggleSort(c.id)} className="sortable num" title={c.description}>
                  {c.label}
                  {arrow(c.id)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.asset.id}>
                <td>
                  <span className={`pill pill-${r.asset.type}`}>{r.asset.type}</span>
                  {r.asset.title}
                </td>
                {columns.map((c) => (
                  <td key={c.id} className="num">
                    {formatMetricValue(r.values[c.id] ?? 0, c.format)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="table-note">
        Showing {rows.length} of {assets.length} synthetic assets.
      </p>
    </div>
  );
}
