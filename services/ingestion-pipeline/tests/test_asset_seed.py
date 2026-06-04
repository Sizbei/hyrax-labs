"""Tests for the metrics-dashboard asset-seed bridge."""

from __future__ import annotations

import json
from pathlib import Path

from hyrax_ingestion.asset_seed import (
    _ASSET_TYPES,
    build_asset_seed,
    material_to_asset,
    write_asset_seed,
)
from hyrax_ingestion.models import NormalizedMaterial, PbrTexture, MapType


def _material(material_id: str = "e9b7ab3d9be33f5b") -> NormalizedMaterial:
    return NormalizedMaterial(
        material_id=material_id,
        supplier="Aurora Surfaces",
        source_url="/fixtures/aurora.html",
        name="Weathered Granite 03",
        slug="weathered-granite-03",
        category="stone",
        resolution_px=4096,
        physical_size_cm=200.0,
        textures=(
            PbrTexture(map_type=MapType.ALBEDO, url="/a.png", original_label="albedo"),
        ),
    )


def test_material_to_asset_matches_dashboard_shape() -> None:
    asset = material_to_asset(_material())
    assert set(asset) == {"id", "title", "type", "channel", "publishedAt"}
    assert asset["id"] == "e9b7ab3d9be33f5b"
    assert asset["title"] == "Weathered Granite 03"
    assert asset["channel"] == "Aurora Surfaces"
    assert asset["type"] in _ASSET_TYPES


def test_mapping_is_deterministic() -> None:
    m = _material()
    assert material_to_asset(m) == material_to_asset(m)


def test_published_at_is_iso_date() -> None:
    asset = material_to_asset(_material())
    # YYYY-MM-DD
    assert len(asset["publishedAt"]) == 10
    assert asset["publishedAt"][4] == "-" and asset["publishedAt"][7] == "-"


def test_build_and_write_seed(tmp_path: Path) -> None:
    materials = [_material("aaaa1111bbbb2222"), _material("cccc3333dddd4444")]
    seed = build_asset_seed(materials)
    assert len(seed) == 2

    out = tmp_path / "assets.json"
    written = write_asset_seed(materials, out)
    assert written == out
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded == seed
    assert [a["id"] for a in loaded] == ["aaaa1111bbbb2222", "cccc3333dddd4444"]
