/**
 * Horizontal bar chart ranking the top-N assets by a chosen metric.
 * D3 builds the band/linear scales and axes; transitions animate value changes.
 */
import { useEffect, useRef } from "react";
import * as d3 from "d3";
import type { Asset, AssetMetricSnapshot, MetricDef } from "../types";
import { formatMetricValue } from "../data/format";
import { useResizeObserver } from "./useResizeObserver";

export interface AssetRankBarChartProps {
  metric: MetricDef;
  assets: Asset[];
  snapshots: AssetMetricSnapshot[];
  topN?: number;
}

const MARGIN = { top: 8, right: 64, bottom: 24, left: 150 };

export function AssetRankBarChart({
  metric,
  assets,
  snapshots,
  topN = 12,
}: AssetRankBarChartProps) {
  const hostRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const { width } = useResizeObserver(hostRef);

  useEffect(() => {
    if (!svgRef.current || width === 0 || snapshots.length === 0) return;

    const titleById = new Map(assets.map((a) => [a.id, a.title]));
    const ranked = [...snapshots]
      .map((s) => ({
        id: s.assetId,
        title: titleById.get(s.assetId) ?? s.assetId,
        value: s.values[metric.id] ?? 0,
      }))
      .sort((a, b) =>
        metric.higherIsBetter ? b.value - a.value : a.value - b.value,
      )
      .slice(0, topN);

    const rowH = 26;
    const height = ranked.length * rowH + MARGIN.top + MARGIN.bottom;
    const innerW = width - MARGIN.left - MARGIN.right;
    const innerH = height - MARGIN.top - MARGIN.bottom;

    const svg = d3.select(svgRef.current).attr("height", height);
    const x = d3
      .scaleLinear()
      .domain([0, d3.max(ranked, (d) => d.value) ?? 1])
      .range([0, innerW]);
    const y = d3
      .scaleBand()
      .domain(ranked.map((d) => d.id))
      .range([0, innerH])
      .padding(0.22);

    svg.selectAll("*").remove();
    const g = svg
      .append("g")
      .attr("transform", `translate(${MARGIN.left},${MARGIN.top})`);

    g.append("g")
      .call(
        d3
          .axisLeft(y)
          .tickFormat((id) => {
            const t = ranked.find((r) => r.id === id)?.title ?? String(id);
            return t.length > 22 ? `${t.slice(0, 20)}…` : t;
          })
          .tickSizeOuter(0),
      )
      .call((sel) => sel.selectAll("text").attr("fill", "#cbd5e1").style("font-size", "11px"))
      .call((sel) => sel.selectAll("line,path").attr("stroke", "transparent"));

    g.selectAll("rect.bar")
      .data(ranked)
      .join("rect")
      .attr("class", "bar")
      .attr("x", 0)
      .attr("y", (d) => y(d.id) ?? 0)
      .attr("height", y.bandwidth())
      .attr("rx", 4)
      .attr("fill", "#22d3ee")
      .attr("width", (d) => x(d.value));

    g.selectAll("text.value")
      .data(ranked)
      .join("text")
      .attr("class", "value")
      .attr("x", (d) => x(d.value) + 6)
      .attr("y", (d) => (y(d.id) ?? 0) + y.bandwidth() / 2)
      .attr("dy", "0.35em")
      .attr("fill", "#e2e8f0")
      .style("font-size", "11px")
      .text((d) => formatMetricValue(d.value, metric.format));
  }, [metric, assets, snapshots, topN, width]);

  return (
    <div ref={hostRef} className="chart-host" data-testid="asset-rank-bar-chart">
      <svg ref={svgRef} width={width} role="img" aria-label={`Top assets by ${metric.label}`} />
    </div>
  );
}
