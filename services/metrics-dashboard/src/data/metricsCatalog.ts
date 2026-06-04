/**
 * Typed catalog of tracked engagement metrics.
 *
 * 18 metrics span four categories: reach, engagement, retention, conversion.
 * The synthetic generator uses baseMin/baseMax to produce plausible values.
 * All numbers are illustrative — nothing here represents real performance.
 */
import type { MetricDef } from "../types";

export const METRICS: readonly MetricDef[] = [
  // --- Reach ---
  {
    id: "impressions",
    label: "Impressions",
    description: "Total times the asset was rendered on a screen.",
    format: "integer",
    category: "reach",
    baseMin: 2000,
    baseMax: 90000,
    higherIsBetter: true,
  },
  {
    id: "reach",
    label: "Reach",
    description: "Unique accounts that saw the asset.",
    format: "integer",
    category: "reach",
    baseMin: 1500,
    baseMax: 60000,
    higherIsBetter: true,
  },
  {
    id: "views",
    label: "Views",
    description: "Counted plays/opens of the asset.",
    format: "integer",
    category: "reach",
    baseMin: 800,
    baseMax: 45000,
    higherIsBetter: true,
  },
  {
    id: "uniqueViewers",
    label: "Unique Viewers",
    description: "Distinct viewers across the period.",
    format: "integer",
    category: "reach",
    baseMin: 600,
    baseMax: 30000,
    higherIsBetter: true,
  },
  // --- Engagement ---
  {
    id: "clicks",
    label: "Clicks",
    description: "Interactions on links or CTAs within the asset.",
    format: "integer",
    category: "engagement",
    baseMin: 50,
    baseMax: 6000,
    higherIsBetter: true,
  },
  {
    id: "ctr",
    label: "Click-Through Rate",
    description: "Clicks divided by impressions.",
    format: "percent",
    category: "engagement",
    baseMin: 0.5,
    baseMax: 9,
    higherIsBetter: true,
  },
  {
    id: "likes",
    label: "Likes",
    description: "Positive reactions on the asset.",
    format: "integer",
    category: "engagement",
    baseMin: 20,
    baseMax: 8000,
    higherIsBetter: true,
  },
  {
    id: "shares",
    label: "Shares",
    description: "Times the asset was reshared.",
    format: "integer",
    category: "engagement",
    baseMin: 5,
    baseMax: 2000,
    higherIsBetter: true,
  },
  {
    id: "comments",
    label: "Comments",
    description: "Comments left on the asset.",
    format: "integer",
    category: "engagement",
    baseMin: 2,
    baseMax: 1500,
    higherIsBetter: true,
  },
  {
    id: "saves",
    label: "Saves",
    description: "Times the asset was bookmarked.",
    format: "integer",
    category: "engagement",
    baseMin: 1,
    baseMax: 1200,
    higherIsBetter: true,
  },
  {
    id: "engagementRate",
    label: "Engagement Rate",
    description: "Total interactions divided by reach.",
    format: "percent",
    category: "engagement",
    baseMin: 0.8,
    baseMax: 14,
    higherIsBetter: true,
  },
  // --- Retention ---
  {
    id: "avgWatchTime",
    label: "Avg Watch Time",
    description: "Average seconds spent on the asset.",
    format: "duration",
    category: "retention",
    baseMin: 4,
    baseMax: 240,
    higherIsBetter: true,
  },
  {
    id: "completionRate",
    label: "Completion Rate",
    description: "Share of viewers who reached the end.",
    format: "percent",
    category: "retention",
    baseMin: 12,
    baseMax: 92,
    higherIsBetter: true,
  },
  {
    id: "dwellTime",
    label: "Dwell Time",
    description: "Average seconds before scrolling away.",
    format: "duration",
    category: "retention",
    baseMin: 2,
    baseMax: 120,
    higherIsBetter: true,
  },
  {
    id: "scrollDepth",
    label: "Scroll Depth",
    description: "Average percent of the asset scrolled.",
    format: "percent",
    category: "retention",
    baseMin: 18,
    baseMax: 98,
    higherIsBetter: true,
  },
  {
    id: "bounceRate",
    label: "Bounce Rate",
    description: "Share of sessions that left immediately.",
    format: "percent",
    category: "retention",
    baseMin: 8,
    baseMax: 78,
    higherIsBetter: false,
  },
  // --- Conversion ---
  {
    id: "conversions",
    label: "Conversions",
    description: "Goal completions attributed to the asset.",
    format: "integer",
    category: "conversion",
    baseMin: 0,
    baseMax: 900,
    higherIsBetter: true,
  },
  {
    id: "conversionRate",
    label: "Conversion Rate",
    description: "Conversions divided by clicks.",
    format: "percent",
    category: "conversion",
    baseMin: 0.2,
    baseMax: 12,
    higherIsBetter: true,
  },
];

/** Lookup a metric definition by id. */
export function getMetric(id: string): MetricDef | undefined {
  return METRICS.find((m) => m.id === id);
}

/** All metric ids in catalog order. */
export const METRIC_IDS: readonly string[] = METRICS.map((m) => m.id);
