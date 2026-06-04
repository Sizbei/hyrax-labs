# ingestion-pipeline

A multi-tool supplier-material ingestion pipeline that scrapes supplier material
listings, extracts raw records, and normalizes them into a **PBR-texture
catalog** (Physically Based Rendering maps: albedo / normal / roughness /
metallic / ambient-occlusion).

> **Representative scaffold.** This is a portfolio/reference implementation of
> the architecture behind a real ingestion system. **All sample data is
> synthetic** and **all scraping targets are local HTML fixtures committed in
> this repo** — the pipeline runs deterministically, offline, and in CI with no
> network access, no real vendor names, and no credentials. PBR maps are modeled
> as metadata only; no image files are generated or downloaded.

## What it does

```
sources (local fixtures)
        │
   ┌────▼─────┐   pluggable backend selected by name
   │  Fetcher │   (soup | playwright | selenium | crawlee)
   └────┬─────┘
        │ HTML
   ┌────▼─────┐
   │ Extract  │   HTML -> RawMaterial   (BeautifulSoup)
   └────┬─────┘
        │ RawMaterial[]
   ┌────▼─────┐
   │Normalize │   units, map-type classification, slug, content hash
   └────┬─────┘
        │
   ┌────▼─────┐
   │  Dedup   │   drop duplicates by content hash
   └────┬─────┘
        │ NormalizedMaterial[]
   ┌────▼─────┐
   │ Catalog  │   write JSON / JSONL
   └──────────┘
```

The normalization stage does the real data-engineering work:

- **Unit normalization** — free-text resolution (`"2K"`, `"4096x4096"`) → pixels;
  tileable size (`"200 cm"`, `"1.5 m"`, `"2000mm"`) → centimeters.
- **Map-type classification** — vendor-specific labels and filenames
  (`diffuse`, `BaseColor`, `col`, `nrm`, `gloss`, `metalness`, `occlusion`, …)
  are collapsed onto canonical PBR channels.
- **Deduplication** — a stable content hash (supplier + name + texture URL set)
  removes the same material re-listed across pages (e.g. syndicated/mirror
  pages).

## Multi-tool adapter architecture

Each scraping/automation tool is a pluggable **fetcher** behind one tiny
interface (`fetchers/base.py`). The pipeline is identical regardless of which
backend produced the HTML; you pick one with `--fetcher` or via the registry.
Heavyweight browser libraries are **optional extras** and imported lazily, so the
core install stays light and the multi-tool design is shown honestly rather than
forcing four browser installs.

| Tool          | Backend name | Status in this scaffold        | When you'd use it |
|---------------|--------------|--------------------------------|-------------------|
| BeautifulSoup | `soup`       | **Fully functional** (default) | Static, server-rendered supplier catalogs. Fast, no browser. Used end-to-end against the fixtures. |
| Playwright    | `playwright` | Real, guarded (extra)          | JS-rendered / SPA suppliers, lazy-loaded grids, infinite scroll — needs a real headless browser. |
| Selenium      | `selenium`   | Real, guarded (extra)          | Legacy portals requiring WebDriver / system Chrome, login or interstitial flows. |
| Crawlee       | `crawlee`    | Real, guarded (extra)          | Large-scale crawls that must *discover* the URL frontier (pagination, category trees) with request queues, autoscaling, retries, politeness. |

Guarded backends raise a clear, actionable error if their library is absent:

```
The 'playwright' fetcher requires the optional 'playwright' package, which is
not installed. Install it with:

    pip install 'hyrax-ingestion[playwright]'
```

## Install

Requires Python 3.11+.

```bash
# Core install (BeautifulSoup path only — runs the full pipeline on fixtures)
pip install -e .

# Optional browser backends
pip install -e '.[playwright]'   # + playwright (then: playwright install chromium)
pip install -e '.[selenium]'     # + selenium (needs a system webdriver)
pip install -e '.[crawlee]'      # + crawlee
pip install -e '.[browsers]'     # all three browser backends

# Dev / test tooling
pip install -e '.[dev]'
```

## Run the CLI over the fixtures

```bash
# Ingest every bundled fixture with the default BeautifulSoup backend
hyrax-ingest -o catalog.json

# Equivalent module form
python -m hyrax_ingestion -o catalog.json

# JSONL output, more fetch workers, explicit backend
hyrax-ingest --fetcher soup --max-workers 8 -o catalog.jsonl

# Ingest specific fixture files
hyrax-ingest fixtures/aurora-surfaces.html fixtures/cobalt-materials.html -o out.json
```

Example output:

```
backend=soup fetched=6 raw=11 normalized=10 duplicates_dropped=1 errors=0
catalog written to catalog.json
```

A catalog record looks like:

```json
{
  "material_id": "…16-hex…",
  "supplier": "Cobalt Materials",
  "name": "Polished Concrete Floor",
  "slug": "polished-concrete-floor",
  "category": "concrete",
  "resolution_px": 8192,
  "physical_size_cm": 300.0,
  "tags": ["concrete", "interior", "floor"],
  "textures": [
    { "map_type": "albedo", "url": "/tex/.../BaseColor.png", "original_label": "BaseColor" },
    { "map_type": "normal", "url": "/tex/.../Normal.png", "original_label": "Normal" }
  ]
}
```

## Test

```bash
pip install -e '.[dev]'
pytest
```

The suite covers fixture parsing, unit normalization, map-type classification,
cross-page dedup, the fetcher registry (including guarded-backend errors), and
the full pipeline producing a catalog from the fixtures.

## Layout

```
ingestion-pipeline/
├── pyproject.toml
├── README.md
├── fixtures/                     # synthetic supplier HTML pages
└── src/hyrax_ingestion/
    ├── models.py                 # pydantic v2 ETL models
    ├── extract.py                # HTML -> RawMaterial (BeautifulSoup)
    ├── normalize.py              # cleaning, classification, dedup
    ├── catalog.py                # JSON / JSONL writers
    ├── pipeline.py               # orchestration + CLI
    └── fetchers/
        ├── base.py               # Fetcher ABC + FetchResult
        ├── registry.py           # select a backend by name
        ├── soup_fetcher.py       # functional default
        ├── playwright_fetcher.py # guarded extra
        ├── selenium_fetcher.py   # guarded extra
        └── crawlee_fetcher.py    # guarded extra
```
