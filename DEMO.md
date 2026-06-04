# Hyrax Labs — End-to-End Demo

A guided walkthrough of the three services. Everything runs **offline** with
**synthetic data**. The fastest path is `make demo`; the sections below show what
each stage does and the real output it produces.

```bash
make demo        # runs ingestion → backend → dashboard, then opens the dashboard
```

`make demo` degrades gracefully: if a toolchain is missing (e.g. no JDK), that
stage prints what it *would* do and the demo continues.

---

## Stage 1 — Ingestion pipeline (Python)

Scrapes the bundled supplier-listing fixtures, extracts raw materials, classifies
each texture into a canonical PBR map type, normalizes units, deduplicates across
mirror pages, and writes a catalog.

```bash
cd services/ingestion-pipeline
pip install -e .
hyrax-ingest --fetcher soup --output catalog.json
```

**Output:**

```
backend=soup fetched=6 raw=11 normalized=10 duplicates_dropped=1 errors=0
catalog written to catalog.json
```

The cross-page duplicate (`aurora-surfaces.html` vs `aurora-surfaces-mirror.html`)
is collapsed by content hash — that's the `duplicates_dropped=1`. A sample
catalog record:

```json
{
  "material_id": "e9b7ab3d9be33f5b",
  "supplier": "Aurora Surfaces",
  "name": "Weathered Granite 03",
  "slug": "weathered-granite-03",
  "category": "stone",
  "resolution_px": 4096,
  "physical_size_cm": 200.0,
  "tags": ["granite", "featured"],
  "textures": [
    { "map_type": "albedo", "url": "/assets/weathered-granite-03/albedo.png", "original_label": "albedo" },
    { "map_type": "normal", "url": "/assets/weathered-granite-03/normal.png", "original_label": "nrm" }
  ]
}
```

Swap the backend with `--fetcher playwright|selenium|crawlee` — those adapters are
real but guarded behind optional extras (`pip install "hyrax-ingestion[playwright]"`).
Without the extra they print an actionable install message rather than crashing.

---

## Stage 2 — JVM backend (Kotlin + Java)

Runs one ingestion cycle: fetches each synthetic partner feed **concurrently**
(one coroutine per partner), normalizes the records into the canonical model,
deduplicates the cross-partner overlap, and tracks every feed as an
individually-recorded, failure-isolated job.

```bash
cd services/backend-jvm
./gradlew run        # requires JDK 17
```

What you'll see in the log: each partner's job transitioning
`PENDING → RUNNING → COMPLETED` (or `FAILED` in isolation), then a cycle summary
of raw-vs-deduped counts. The two synthetic partners both report
`Aluminum Sheet 6061`; dedup collapses it to one canonical material.

> No JDK locally? The backend builds and runs in CI on JDK 17 (see the green CI
> badge). `make demo` will skip this stage with a clear note.

---

## Stage 3 — Metrics dashboard (React + D3 + SSE)

A real-time content-performance dashboard: 18 engagement metrics across 120
synthetic assets, streamed live from a Node/Express SSE endpoint and rendered
with hand-written D3 visualizations.

```bash
cd services/metrics-dashboard
npm install
npm run dev          # API (:4000) + web (:5173) together
# open http://localhost:5173
```

The API is genuinely streaming — not a client-side `setInterval`. Verify directly:

```bash
curl -s http://localhost:4000/api/health
# {"success":true,"data":{"status":"ok","assets":120,"metrics":18},"error":null}

curl -N http://localhost:4000/api/stream
# data: {"timestamp":1780564151957,"aggregates":{"impressions":7114779,"reach":4421693,
#        "views":3419755,"clicks":471278,"ctr":6.14,"likes":583256,"engagementRate":9.65,
#        "completionRate":63.75,"conversions":64765,"conversionRate":7.91, ...}}
# data: { ... next tick ... }
```

In the browser you get live KPI cards with per-tick deltas, an animating
time-series area chart, a top-assets bar chart, a day×hour engagement heatmap, a
metric-correlation scatter, and a sortable/filterable per-asset table.

All values come from a seeded PRNG shared by client and server, so the data is
reproducible and identical on every run.

---

## Run the test suites

```bash
make test            # all three: JVM (26) + Python (49) + dashboard (22)
# or individually:
make test-ingest
make test-dashboard
make test-backend    # requires JDK 17
```

## Containerized demo

```bash
docker compose up --build
# dashboard → http://localhost:5173
```

The compose file runs the ingestion pipeline once into a shared volume, runs the
backend ingestion cycle, and serves the dashboard.

---

> **Reminder:** all data here is synthetic and every external dependency is
> stubbed, so the entire platform runs offline. The architecture is real; the
> data is not.
