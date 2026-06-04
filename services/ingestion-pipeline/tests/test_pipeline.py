"""End-to-end pipeline and catalog tests over the fixtures."""

from __future__ import annotations

import json
from pathlib import Path

from hyrax_ingestion.catalog import write_jsonl
from hyrax_ingestion.models import MapType
from hyrax_ingestion.pipeline import discover_fixtures, main, run_pipeline


def test_discover_fixtures_finds_html(fixtures_dir: Path) -> None:
    found = discover_fixtures(fixtures_dir)
    assert len(found) >= 5
    assert all(f.endswith(".html") for f in found)


def test_full_pipeline_over_fixtures(fixture_files, tmp_path: Path) -> None:
    out = tmp_path / "catalog.json"
    materials, result = run_pipeline(
        fixture_files,
        fetcher_name="soup",
        catalog_path=out,
        max_workers=4,
    )

    assert result.sources_fetched == len(fixture_files)
    assert result.normalized_materials == len(materials)
    # The mirror fixture re-lists Weathered Granite 03 -> at least one dedup.
    assert result.duplicates_dropped >= 1
    assert not result.errors

    # Catalog file exists and parses back to the same count.
    assert out.is_file()
    records = json.loads(out.read_text())
    assert len(records) == len(materials)

    # Every record has a classified texture set and stable id.
    for rec in records:
        assert rec["material_id"]
        assert rec["textures"]
        for tex in rec["textures"]:
            assert tex["map_type"] in {m.value for m in MapType}


def test_pipeline_classifies_full_pbr_set(fixtures_dir: Path) -> None:
    cobalt = str(fixtures_dir / "cobalt-materials.html")
    materials, _ = run_pipeline([cobalt], fetcher_name="soup")
    concrete = next(m for m in materials if m.name == "Polished Concrete Floor")
    types = set(concrete.map_types)
    assert {
        MapType.ALBEDO,
        MapType.NORMAL,
        MapType.ROUGHNESS,
        MapType.METALLIC,
        MapType.AO,
    } <= types


def test_write_jsonl_roundtrip(fixture_files, tmp_path: Path) -> None:
    materials, _ = run_pipeline(fixture_files, fetcher_name="soup")
    out = write_jsonl(materials, tmp_path / "catalog.jsonl")
    lines = [json.loads(line) for line in out.read_text().splitlines()]
    assert len(lines) == len(materials)


def test_cli_main_over_fixtures(tmp_path: Path) -> None:
    out = tmp_path / "cli_catalog.json"
    code = main(["--output", str(out), "--fetcher", "soup"])
    assert code == 0
    assert out.is_file()
    records = json.loads(out.read_text())
    assert len(records) >= 5
