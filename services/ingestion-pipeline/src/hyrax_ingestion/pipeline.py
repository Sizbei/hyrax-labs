"""Pipeline orchestration: fetch -> extract -> normalize -> dedup -> catalog.

The pipeline is backend-agnostic: it asks the registry for a fetcher by name and
runs the rest of the stages identically regardless of which of the four tools
produced the HTML. Fetching is parallelized with a thread pool, which is the
right model here because every backend stage is I/O-bound (disk, network, or a
browser round-trip).
"""

from __future__ import annotations

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from hyrax_ingestion.asset_seed import write_asset_seed
from hyrax_ingestion.catalog import write_catalog
from hyrax_ingestion.extract import extract_materials
from hyrax_ingestion.fetchers.base import Fetcher, FetchResult
from hyrax_ingestion.fetchers.registry import (
    DEFAULT_FETCHER,
    available_fetchers,
    get_fetcher,
)
from hyrax_ingestion.models import IngestionResult, NormalizedMaterial, RawMaterial
from hyrax_ingestion.normalize import normalize_and_dedup

DEFAULT_FIXTURES_DIR = Path(__file__).resolve().parents[2] / "fixtures"


def discover_fixtures(directory: str | Path) -> list[str]:
    """Return sorted ``*.html`` fixture paths under ``directory``."""

    root = Path(directory).expanduser()
    if not root.is_dir():
        raise NotADirectoryError(f"fixtures directory not found: {root}")
    return [str(p) for p in sorted(root.glob("*.html"))]


def run_pipeline(
    sources: list[str],
    *,
    fetcher: Fetcher | None = None,
    fetcher_name: str = DEFAULT_FETCHER,
    catalog_path: str | Path | None = None,
    max_workers: int = 4,
) -> tuple[list[NormalizedMaterial], IngestionResult]:
    """Run the full ingestion pipeline over ``sources``.

    Returns the catalog (list of normalized materials) and a run summary.
    """

    active = fetcher or get_fetcher(fetcher_name)
    errors: list[str] = []
    fetched: list[FetchResult] = []

    # --- Stage 1: concurrent fetch ---
    with ThreadPoolExecutor(max_workers=max(1, max_workers)) as pool:
        future_to_source = {pool.submit(active.fetch, src): src for src in sources}
        for future in as_completed(future_to_source):
            src = future_to_source[future]
            try:
                fetched.append(future.result())
            except Exception as exc:  # noqa: BLE001 - record, don't crash the run
                errors.append(f"fetch failed for {src}: {exc}")

    # --- Stage 2: extract ---
    raws: list[RawMaterial] = []
    for result in fetched:
        try:
            raws.extend(extract_materials(result))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"extract failed for {result.source}: {exc}")

    # --- Stage 3 + 4: normalize + dedup ---
    materials, duplicates = normalize_and_dedup(raws)

    # --- Stage 5: catalog ---
    written_path: str | None = None
    if catalog_path is not None:
        written_path = str(write_catalog(materials, catalog_path))

    result = IngestionResult(
        sources_fetched=len(fetched),
        raw_materials=len(raws),
        normalized_materials=len(materials),
        duplicates_dropped=duplicates,
        errors=tuple(errors),
        catalog_path=written_path,
    )
    return materials, result


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hyrax-ingest",
        description=(
            "Hyrax Labs ingestion pipeline: scrape synthetic supplier material "
            "pages and emit a normalized PBR-texture catalog. "
            "All sample data is synthetic and scraping targets are local fixtures."
        ),
    )
    parser.add_argument(
        "sources",
        nargs="*",
        help="HTML files/URLs to ingest. Defaults to the bundled fixtures.",
    )
    parser.add_argument(
        "--fetcher",
        default=DEFAULT_FETCHER,
        choices=available_fetchers(),
        help="Fetcher backend to use (default: %(default)s).",
    )
    parser.add_argument(
        "--fixtures-dir",
        default=str(DEFAULT_FIXTURES_DIR),
        help="Directory of *.html fixtures used when no sources are given.",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="catalog.json",
        help="Catalog output path (.json or .jsonl). Default: %(default)s.",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=4,
        help="Concurrent fetch workers (default: %(default)s).",
    )
    parser.add_argument(
        "--asset-seed",
        metavar="PATH",
        default=None,
        help=(
            "Also write a metrics-dashboard-compatible asset seed (JSON) to PATH, "
            "mapping each material to a dashboard content asset."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)

    sources = args.sources or discover_fixtures(args.fixtures_dir)
    if not sources:
        print("no sources to ingest", file=sys.stderr)
        return 1

    try:
        fetcher = get_fetcher(args.fetcher)
    except KeyError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    materials, result = run_pipeline(
        sources,
        fetcher=fetcher,
        catalog_path=args.output,
        max_workers=args.max_workers,
    )

    print(f"backend={args.fetcher} {result.as_summary()}")
    if result.catalog_path:
        print(f"catalog written to {result.catalog_path}")

    if args.asset_seed:
        seed_path = write_asset_seed(materials, args.asset_seed)
        print(f"dashboard asset seed written to {seed_path} ({len(materials)} assets)")

    for err in result.errors:
        print(f"  ! {err}", file=sys.stderr)

    return 0 if not result.errors else 3


if __name__ == "__main__":
    raise SystemExit(main())
