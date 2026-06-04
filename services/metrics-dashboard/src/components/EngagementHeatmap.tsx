/**
 * Engagement-by-hour heatmap (day-of-week x hour-of-day).
 *
 * Cell intensity = deterministic synthetic engagement-rate for that slot.
 * D3 supplies band scales and a sequential color scale.
 */
import { useEffect, useMemo, useRef } from "react";
import * as d3 from "d3";
import { createRng, hashString } from "../data/random";
import { useResizeObserver } from "./useResizeObserver";

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const HOURS = Array.from({ length: 24 }, (_, h) => h);
const MARGIN = { top: 8, right: 8, bottom: 22, left: 40 };

interface Cell {
  day: number;
  hour: number;
  value: number;
}

function buildCells(seed: number): Cell[] {
  const cells: Cell[] = [];
  for (let day = 0; day < 7; day += 1) {
    for (const hour of HOURS) {
      const rng = createRng(hashString(`${seed}:${day}:${hour}`));
      // Daytime + weekday bias for a realistic engagement curve.
      const daypart = Math.exp(-((hour - 13) ** 2) / 40);
      const weekday = day < 5 ? 1 : 0.7;
      const noise = 0.6 + rng() * 0.4;
      cells.push({ day, hour, value: daypart * weekday * noise });
    }
  }
  return cells;
}

export interface EngagementHeatmapProps {
  seed?: number;
}

export function EngagementHeatmap({ seed = 1337 }: EngagementHeatmapProps) {
  const hostRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const { width, height } = useResizeObserver(hostRef);
  const cells = useMemo(() => buildCells(seed), [seed]);

  useEffect(() => {
    if (!svgRef.current || width === 0 || height === 0) return;
    const innerW = width - MARGIN.left - MARGIN.right;
    const innerH = height - MARGIN.top - MARGIN.bottom;

    const x = d3
      .scaleBand<number>()
      .domain(HOURS)
      .range([0, innerW])
      .padding(0.05);
    const y = d3
      .scaleBand<number>()
      .domain(d3.range(7))
      .range([0, innerH])
      .padding(0.08);
    const color = d3
      .scaleSequential(d3.interpolateInferno)
      .domain([0, d3.max(cells, (c) => c.value) ?? 1]);

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();
    const g = svg
      .append("g")
      .attr("transform", `translate(${MARGIN.left},${MARGIN.top})`);

    g.selectAll("rect")
      .data(cells)
      .join("rect")
      .attr("x", (d) => x(d.hour) ?? 0)
      .attr("y", (d) => y(d.day) ?? 0)
      .attr("width", x.bandwidth())
      .attr("height", y.bandwidth())
      .attr("rx", 2)
      .attr("fill", (d) => color(d.value));

    g.append("g")
      .attr("transform", `translate(0,${innerH})`)
      .call(d3.axisBottom(x).tickValues(HOURS.filter((h) => h % 3 === 0)).tickSizeOuter(0))
      .call((sel) => sel.selectAll("text").attr("fill", "#94a3b8").style("font-size", "9px"))
      .call((sel) => sel.selectAll("line,path").attr("stroke", "transparent"));

    g.append("g")
      .call(d3.axisLeft(y).tickFormat((d) => DAYS[Number(d)]).tickSizeOuter(0))
      .call((sel) => sel.selectAll("text").attr("fill", "#94a3b8").style("font-size", "9px"))
      .call((sel) => sel.selectAll("line,path").attr("stroke", "transparent"));
  }, [cells, width, height]);

  return (
    <div ref={hostRef} className="chart-host" data-testid="engagement-heatmap">
      <svg ref={svgRef} width={width} height={height} role="img" aria-label="Engagement by hour and day" />
    </div>
  );
}
