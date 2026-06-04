# Hyrax Labs — Materials Data Platform

A monorepo of three services that together ingest **supplier material** data from
the open web and third-party partner APIs, normalize it into a canonical
**PBR-texture catalog** (Physically Based Rendering maps), and surface content
performance through a **real-time analytics dashboard**.

### ▶ Live demo: **https://sizbei.github.io/hyrax-labs/**

The dashboard runs live in your browser (real-time D3 charts, 18 metrics across
120 assets). No backend required — the same deterministic generator the API uses
runs client-side, so the numbers are identical but synthetic.

> **Representative portfolio scaffold.** This repository demonstrates the
> architecture and engineering practices behind a materials-data platform.
> **All data is synthetic** — there are no real partner names, API endpoints,
> credentials, scraped sites, or analytics. Web scraping runs against local HTML
> fixtures; partner APIs return hard-coded sample records; dashboard metrics are
> generated deterministically from a seed. Everything builds and runs offline.

[![CI](https://github.com/Sizbei/hyrax-labs/actions/workflows/ci.yml/badge.svg)](https://github.com/Sizbei/hyrax-labs/actions/workflows/ci.yml)
[![Deploy dashboard](https://github.com/Sizbei/hyrax-labs/actions/workflows/deploy-dashboard.yml/badge.svg)](https://github.com/Sizbei/hyrax-labs/actions/workflows/deploy-dashboard.yml)
[![Live demo](https://img.shields.io/badge/live%20demo-online-22c55e)](https://sizbei.github.io/hyrax-labs/)
![Kotlin](https://img.shields.io/badge/Kotlin-1.9-7F52FF?logo=kotlin&logoColor=white)
![Java](https://img.shields.io/badge/Java-17-007396?logo=openjdk&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white)

---

## Architecture

```
                            ┌──────────────────────────────────────────┐
                            │              HYRAX LABS                   │
                            │         materials data platform           │
                            └──────────────────────────────────────────┘

   web sources                  partner APIs                  analytics consumers
 (local fixtures)            (synthetic clients)               (browser, real-time)
        │                            │                                  ▲
        ▼                            ▼                                  │
┌───────────────────┐      ┌───────────────────┐            ┌──────────────────────┐
│ ingestion-pipeline │      │    backend-jvm    │            │   metrics-dashboard  │
│      (Python)      │      │  (Kotlin + Java)  │            │  (React + D3 + Node) │
│                    │      │                   │            │                      │
│ Playwright/Crawlee │      │ partner clients   │            │  18 metrics × 120    │
│ BeautifulSoup/     │─────▶│ normalize + dedup │───────────▶│  assets, SSE live    │
│ Selenium adapters  │ JSON │ async scheduler   │  catalog   │  D3 visualizations   │
│ → PBR catalog      │      │ (coroutines)      │            │                      │
└───────────────────┘      └───────────────────┘            └──────────────────────┘
        │                            │                                  ▲
        └──────── normalized ────────┴──────── canonical catalog ───────┘
                  PBR catalog (JSON / JSONL)
```

The three services are independently buildable and independently useful, but the
**data flows left-to-right**: the ingestion pipeline scrapes and normalizes raw
supplier listings into a PBR catalog, the JVM backend ingests partner-API records
into the same canonical model (normalizing, deduplicating, and scheduling the work
asynchronously), and the dashboard visualizes engagement across the resulting
catalog of assets in real time.

The pipeline and dashboard are wired together end-to-end:
`hyrax-ingest --asset-seed` maps scraped materials onto the dashboard's asset
shape, and the [live site](https://sizbei.github.io/hyrax-labs/) is seeded with
that real pipeline output — the supplier-material names you see on the dashboard
came through the ingestion stage.

---

## Services

| Service | Stack | What it does | Tests |
|---------|-------|--------------|-------|
| [`backend-jvm`](services/backend-jvm) | Kotlin 1.9 + Java 17, Gradle, coroutines, JUnit 5 | Ingests supplier-material records from third-party partner APIs; normalizes, deduplicates, and runs the work as asynchronous, scheduled jobs — each partner feed processed concurrently and failure-isolated via structured concurrency. | 27 |
| [`ingestion-pipeline`](services/ingestion-pipeline) | Python 3.11+, pydantic v2, pytest | Multi-tool scraping pipeline (Playwright · Crawlee · BeautifulSoup · Selenium adapters) that turns supplier listings into a normalized PBR-texture catalog. | 52 |
| [`metrics-dashboard`](services/metrics-dashboard) | React 18 + TypeScript + D3.js, Node/Express SSE, Vitest | Real-time content-performance dashboard tracking 18 engagement metrics across 120 synthetic assets with live D3 visualizations. | 22 |

---

## Quick start

Each service is self-contained. From the repo root:

```bash
# 1. Ingestion pipeline (Python) — scrape fixtures → PBR catalog
make ingest          # or: cd services/ingestion-pipeline && pip install -e . && hyrax-ingest

# 2. JVM backend — run a demo ingestion cycle over synthetic partner APIs
make backend         # or: cd services/backend-jvm && ./gradlew run     (requires JDK 17)

# 3. Metrics dashboard — live dashboard at http://localhost:5173
make dashboard       # or: cd services/metrics-dashboard && npm install && npm run dev
```

Run the **full end-to-end demo** (ingestion → backend → dashboard) with one command:

```bash
make demo
```

See [`DEMO.md`](DEMO.md) for the guided walkthrough and what to look at.

### Run all tests

```bash
make test            # runs JVM + Python + dashboard test suites
```

---

## Repository layout

```
hyrax-labs/
├── README.md                 # this file
├── DEMO.md                   # guided end-to-end demo
├── Makefile                  # build / run / test / demo targets
├── docker-compose.yml        # containerized demo
├── .github/workflows/ci.yml  # builds + tests all three services
└── services/
    ├── backend-jvm/          # Kotlin + Java ingestion service
    ├── ingestion-pipeline/   # Python multi-tool scraping pipeline
    └── metrics-dashboard/    # React + D3 real-time dashboard
```

---

## Engineering notes

- **Honest scope.** Every external dependency is stubbed with synthetic data so
  the whole platform runs offline and in CI. The architecture is real; the data
  is not.
- **Async-first backend.** The JVM service uses Kotlin coroutines and structured
  concurrency — one coroutine per partner feed, `Mutex`-guarded job state, and
  failure isolation so a single bad feed never aborts a cycle.
- **Pluggable ingestion.** The Python pipeline models all four scraping tools as
  interchangeable fetcher adapters selected by name; the BeautifulSoup adapter is
  fully functional against fixtures, the browser-based adapters are lazily
  imported and guarded behind optional extras.
- **Real-time, honestly.** The dashboard's "real-time" is a genuine SSE stream
  from the Node API, not a `setInterval` faking it client-side.

## License

[MIT](LICENSE)
