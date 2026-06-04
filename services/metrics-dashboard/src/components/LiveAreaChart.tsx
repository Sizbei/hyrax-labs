/**
 * Live time-series area + line chart.
 *
 * D3 owns the scales, axes and area/line generators; React owns the SVG host
 * element. Re-renders whenever the live tick window changes.
 */
import { useEffect, useRef } from "react";
import * as d3 from "d3";
import type { MetricDef } from "../types";
import { formatMetricValue } from "../data/format";
import { useResizeObserver } from "./useResizeObserver";

export interface LiveAreaChartProps {
  metric: MetricDef;
  series: { timestamp: number; value: number }[];
}

const MARGIN = { top: 16, right: 16, bottom: 28, left: 56 };

export function LiveAreaChart({ metric, series }: LiveAreaChartProps) {
  const hostRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const { width, height } = useResizeObserver(hostRef);

  useEffect(() => {
    if (!svgRef.current || width === 0 || height === 0 || series.length === 0) {
      return;
    }
    const svg = d3.select(svgRef.current);
    const innerW = width - MARGIN.left - MARGIN.right;
    const innerH = height - MARGIN.top - MARGIN.bottom;

    const x = d3
      .scaleTime()
      .domain(d3.extent(series, (d) => new Date(d.timestamp)) as [Date, Date])
      .range([0, innerW]);

    const yMax = d3.max(series, (d) => d.value) ?? 1;
    const yMin = d3.min(series, (d) => d.value) ?? 0;
    const y = d3
      .scaleLinear()
      .domain([yMin * 0.95, yMax * 1.05])
      .nice()
      .range([innerH, 0]);

    svg.selectAll("*").remove();
    const g = svg
      .append("g")
      .attr("transform", `translate(${MARGIN.left},${MARGIN.top})`);

    const gradId = `area-grad-${metric.id}`;
    const grad = svg
      .append("defs")
      .append("linearGradient")
      .attr("id", gradId)
      .attr("x1", "0")
      .attr("y1", "0")
      .attr("x2", "0")
      .attr("y2", "1");
    grad.append("stop").attr("offset", "0%").attr("stop-color", "#6366f1").attr("stop-opacity", 0.45);
    grad.append("stop").attr("offset", "100%").attr("stop-color", "#6366f1").attr("stop-opacity", 0);

    g.append("g")
      .attr("transform", `translate(0,${innerH})`)
      .call(d3.axisBottom(x).ticks(5).tickSizeOuter(0))
      .call((sel) => sel.selectAll("text").attr("fill", "#94a3b8"))
      .call((sel) => sel.selectAll("line,path").attr("stroke", "#334155"));

    g.append("g")
      .call(
        d3
          .axisLeft(y)
          .ticks(5)
          .tickFormat((d) => formatMetricValue(Number(d), metric.format)),
      )
      .call((sel) => sel.selectAll("text").attr("fill", "#94a3b8"))
      .call((sel) => sel.selectAll("line,path").attr("stroke", "#334155"));

    const area = d3
      .area<{ timestamp: number; value: number }>()
      .x((d) => x(new Date(d.timestamp)))
      .y0(innerH)
      .y1((d) => y(d.value))
      .curve(d3.curveMonotoneX);

    const line = d3
      .line<{ timestamp: number; value: number }>()
      .x((d) => x(new Date(d.timestamp)))
      .y((d) => y(d.value))
      .curve(d3.curveMonotoneX);

    g.append("path").datum(series).attr("fill", `url(#${gradId})`).attr("d", area);
    g.append("path")
      .datum(series)
      .attr("fill", "none")
      .attr("stroke", "#818cf8")
      .attr("stroke-width", 2)
      .attr("d", line);

    const last = series[series.length - 1];
    g.append("circle")
      .attr("cx", x(new Date(last.timestamp)))
      .attr("cy", y(last.value))
      .attr("r", 4)
      .attr("fill", "#c7d2fe")
      .attr("stroke", "#1e1b4b")
      .attr("stroke-width", 2);
  }, [series, width, height, metric]);

  return (
    <div ref={hostRef} className="chart-host" data-testid="live-area-chart">
      <svg ref={svgRef} width={width} height={height} role="img" aria-label={`${metric.label} over time`} />
    </div>
  );
}
