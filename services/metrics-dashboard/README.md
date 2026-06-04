# metrics-dashboard

A real-time content performance dashboard built with **React + TypeScript + D3.js**, backed by a small **Node/Express** API that streams synthetic engagement metrics over **Server-Sent Events (SSE)**.

> **All data is synthetic.** Every value is generated deterministically from a fixed seed. There are no real analytics, no credentials, and no real company names anywhere in this project. This is a representative portfolio scaffold, not a production analytics product, and it does not report any real performance numbers.

## What it does

The dashboard tracks **18 engagement metrics** across **120 synthetic content assets ("posts")** and surfaces them through several D3-driven visualizations that update in real time:

- **KPI cards** — live aggregate values with per-tick deltas.
- **Live aggregate trend** — a time-series area + line chart that animates as new SSE ticks arrive.
- **Top assets** — a horizontal bar chart ranking assets by a selectable metric.
- **Engagement by hour** — a day-of-week × hour-of-day heatmap.
- **Metric correlation** — a scatter plot of any two metrics across all assets, colored by asset type.
- **Per-asset metrics table** — sortable and filterable, one row per asset.

## Metric catalog (18 metrics)

Defined in [`src/data/metricsCatalog.ts`](src/data/metricsCatalog.ts), typed via `MetricDef`:

| Category    | Metrics |
|-------------|---------|
| Reach       | Impressions, Reach, Views, Unique Viewers |
| Engagement  | Clicks, Click-Through Rate (CTR), Likes, Shares, Comments, Saves, Engagement Rate |
| Retention   | Avg Watch Time, Completion Rate, Dwell Time, Scroll Depth, Bounce Rate |
| Conversion  | Conversions, Conversion Rate |

Each metric carries a label, description, display format (`integer` / `percent` / `duration` / `decimal`), category, value bounds, and a `higherIsBetter` flag used for ranking and delta coloring.

## Architecture

```
metrics-dashboard/
├── index.html
├── server/
│   └── index.js              # Express API + SSE stream (imports the .ts data layer)
├── src/
│   ├── types.ts              # Shared domain types
│   ├── App.tsx               # Composition root
│   ├── main.tsx              # React entry
│   ├── styles.css
│   ├── data/
│   │   ├── random.ts         # Seedable mulberry32 PRNG + helpers
│   │   ├── metricsCatalog.ts # Typed catalog of 18 metrics
│   │   ├── generator.ts      # Deterministic synthetic data generator
│   │   └── format.ts         # Value formatters
│   ├── api/
│   │   ├── client.ts         # Typed fetch client
│   │   └── useLiveStream.ts  # React hook subscribing to the SSE stream
│   └── components/
│       ├── useResizeObserver.ts
│       ├── LiveAreaChart.tsx       # D3 time-series area/line
│       ├── AssetRankBarChart.tsx   # D3 ranked bar chart
│       ├── EngagementHeatmap.tsx   # D3 heatmap
│       ├── CorrelationScatter.tsx  # D3 scatter
│       ├── MetricsTable.tsx        # Sortable/filterable table
│       ├── KpiCard.tsx
│       └── MetricSelect.tsx
└── test/                     # Vitest + Testing Library tests
```

The data generator is **shared** between the browser and the API server. Both import the same `.ts` modules — the server runs them directly under Node v22+/v24 (which strips TypeScript types natively), so the client and server always agree on the dataset for a given seed.

**Charts** use real D3 (no charting wrapper): D3 owns scales, axes, and shape generators inside a React-hosted `<svg>` ref; React owns component state and the surrounding DOM.

## How the real-time streaming works

1. The Express server generates the asset set once at startup from `DEFAULT_SEED`.
2. `GET /api/stream` opens an SSE connection and emits a `data:` frame every `STREAM_INTERVAL_MS` (default 2000 ms).
3. Each frame is a `LiveTick` containing aggregate metric values for the current timestamp + tick counter. A slow sine wobble drives smooth, bounded variation so values animate organically rather than jumping randomly.
4. On the client, `useLiveStream` subscribes via `EventSource`, keeps a rolling window of the last 60 ticks, and feeds the KPI cards and live trend chart. It surfaces a `connecting / live / error` status and reconnects gracefully.

### API endpoints

| Method | Path                          | Description |
|--------|-------------------------------|-------------|
| GET    | `/api/health`                 | Liveness + counts |
| GET    | `/api/metrics`                | Metric catalog |
| GET    | `/api/assets`                 | All synthetic assets |
| GET    | `/api/snapshot`               | Current values for every asset + aggregates |
| GET    | `/api/timeseries/:metricId`   | Historical aggregate series (`?points=N`) |
| GET    | `/api/stream`                 | SSE stream of live aggregate ticks |

All responses use a consistent envelope: `{ success, data, error }`.

## How to run

```bash
npm install

# Run the API server and Vite dev server together (recommended):
npm run dev
# Web:  http://localhost:5173   (Vite proxies /api -> :4000)
# API:  http://localhost:4000

# Or run them separately:
npm run server   # Express synthetic API on :4000
npm run dev      # (still starts both; use `vite` directly for web-only)
```

Configuration via environment variables (optional):

- `PORT` — API server port (default `4000`).
- `STREAM_INTERVAL_MS` — SSE tick interval (default `2000`).
- `VITE_API_BASE` — override the API base the frontend calls (default `/api`).

## How to test

```bash
npm test         # run the Vitest suite once
npm run test:watch
```

The suite covers the seeded PRNG, the synthetic data generator (determinism, bounds, time series, live ticks), the metric catalog, the formatters, and the sortable/filterable table component (rendering, filtering, sort toggling).

## Build & lint

```bash
npm run build    # tsc type-check + vite production build
npm run preview  # serve the production build
npm run lint     # eslint
```
