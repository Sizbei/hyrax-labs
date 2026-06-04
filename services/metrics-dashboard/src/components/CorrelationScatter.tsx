/**
 * Scatter plot correlating two metrics across all assets.
 * Point color encodes asset type; D3 builds linear scales and axes.
 */
import { useEffect, useRef } from "react";
import * as d3 from "d3";
import type { Asset, AssetMetricSnapshot, MetricDef } from "../types";
import { formatMetricValue } from "../data/format";
import { useResizeObserver } from "./useResizeObserver";

export interface CorrelationScatterProps {
  xMetric: MetricDef;
  yMetric: MetricDef;
  assets: Asset[];
  snapshots: AssetMetricSnapshot[];
}

const MARGIN = { top: 12, right: 16, bottom: 36, left: 56 };
const TYPE_COLORS: Record<string, string> = {
  video: "#f472b6",
  article: "#34d399",
  image: "#60a5fa",
  short: "#fbbf24",
  carousel: "#a78bfa",
};

export function CorrelationScatter({
  xMetric,
  yMetric,
  assets,
  snapshots,
}: CorrelationScatterProps) {
  const hostRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const { width, height } = useResizeObserver(hostRef);

  useEffect(() => {
    if (!svgRef.current || width === 0 || height === 0 || snapshots.length === 0) {
      return;
    }
    const typeById = new Map(assets.map((a) => [a.id, a.type]));
    const points = snapshots.map((s) => ({
      id: s.assetId,
      type: typeById.get(s.assetId) ?? "image",
      x: s.values[xMetric.id] ?? 0,
      y: s.values[yMetric.id] ?? 0,
    }));

    const innerW = width - MARGIN.left - MARGIN.right;
    const innerH = height - MARGIN.top - MARGIN.bottom;

    const x = d3
      .scaleLinear()
      .domain([0, (d3.max(points, (p) => p.x) ?? 1) * 1.05])
      .range([0, innerW]);
    const y = d3
      .scaleLinear()
      .domain([0, (d3.max(points, (p) => p.y) ?? 1) * 1.05])
      .range([innerH, 0]);

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();
    const g = svg
      .append("g")
      .attr("transform", `translate(${MARGIN.left},${MARGIN.top})`);

    g.append("g")
      .attr("transform", `translate(0,${innerH})`)
      .call(d3.axisBottom(x).ticks(5).tickFormat((d) => formatMetricValue(Number(d), xMetric.format)))
      .call((sel) => sel.selectAll("text").attr("fill", "#94a3b8"))
      .call((sel) => sel.selectAll("line,path").attr("stroke", "#334155"));

    g.append("g")
      .call(d3.axisLeft(y).ticks(5).tickFormat((d) => formatMetricValue(Number(d), yMetric.format)))
      .call((sel) => sel.selectAll("text").attr("fill", "#94a3b8"))
      .call((sel) => sel.selectAll("line,path").attr("stroke", "#334155"));

    g.selectAll("circle")
      .data(points)
      .join("circle")
      .attr("cx", (d) => x(d.x))
      .attr("cy", (d) => y(d.y))
      .attr("r", 4)
      .attr("fill", (d) => TYPE_COLORS[d.type] ?? "#94a3b8")
      .attr("fill-opacity", 0.7)
      .attr("stroke", "#0f172a")
      .attr("stroke-width", 0.5);
  }, [xMetric, yMetric, assets, snapshots, width, height]);

  return (
    <div ref={hostRef} className="chart-host" data-testid="correlation-scatter">
      <svg ref={svgRef} width={width} height={height} role="img" aria-label={`${yMetric.label} vs ${xMetric.label}`} />
    </div>
  );
}
