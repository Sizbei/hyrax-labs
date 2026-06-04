"""Normalization, unit parsing, and map-type classification tests."""

from __future__ import annotations

import pytest

from hyrax_ingestion.models import MapType, RawMaterial, RawTextureLink
from hyrax_ingestion.normalize import (
    classify_map_type,
    normalize_material,
    parse_physical_size_cm,
    parse_resolution,
    slugify,
)


@pytest.mark.parametrize(
    "label,url,expected",
    [
        ("Base Color", "", MapType.ALBEDO),
        ("Diffuse", "", MapType.ALBEDO),
        ("col", "", MapType.ALBEDO),
        ("Normal", "", MapType.NORMAL),
        ("nrm", "", MapType.NORMAL),
        ("Bump", "", MapType.NORMAL),
        ("Roughness", "", MapType.ROUGHNESS),
        ("Gloss", "", MapType.ROUGHNESS),
        ("Metalness", "", MapType.METALLIC),
        ("AO", "", MapType.AO),
        ("Occlusion", "", MapType.AO),
        ("map 1", "/x/cracked_mud_albedo.png", MapType.ALBEDO),
        ("map 2", "/x/cracked_mud_normal.png", MapType.NORMAL),
        ("totally unknown", "/x/whatever.png", MapType.UNKNOWN),
    ],
)
def test_classify_map_type(label: str, url: str, expected: MapType) -> None:
    assert classify_map_type(label, url) is expected


def test_basecolor_not_shadowed_by_col() -> None:
    # "basecolor" contains "col"; longer alias must win and still be albedo.
    assert classify_map_type("BaseColor") is MapType.ALBEDO


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("4096x4096", 4096),
        ("4096 x 2048", 4096),
        ("2K", 2048),
        ("4K", 4096),
        ("8K", 8192),
        ("4096", 4096),
        (None, None),
        ("n/a", None),
        # Mixed tokens: explicit pixel dimensions win over an embedded "k"
        # shorthand (e.g. a small preview label), so real dims aren't overridden.
        ("1024 x 768, 2k thumb", 1024),
        ("1920x1080 (preview)", 1920),
        # Pure shorthand still resolves when no explicit dimensions are present.
        ("4k preview only", 4096),
    ],
)
def test_parse_resolution(raw, expected) -> None:
    assert parse_resolution(raw) == expected


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("200 cm", 200.0),
        ("1.5 m", 150.0),
        ("2000mm", 200.0),
        ("30 cm", 30.0),
        ("3 m", 300.0),
        ("200", 200.0),  # assumed cm
        (None, None),
    ],
)
def test_parse_physical_size_cm(raw, expected) -> None:
    assert parse_physical_size_cm(raw) == expected


def test_slugify() -> None:
    assert slugify("Weathered Granite 03") == "weathered-granite-03"
    assert slugify("  Glazed Hex Tile (Teal)!! ") == "glazed-hex-tile-teal"


def test_normalize_material_end_to_end() -> None:
    raw = RawMaterial(
        supplier="Aurora Surfaces",
        source_url="file://aurora.html",
        name="Brushed Steel Panel",
        category="metal",
        resolution_raw="2K",
        physical_size_raw="1.0 m",
        tags=("steel", "metal"),
        texture_links=(
            RawTextureLink(label="Diffuse", url="/a/diffuse.png"),
            RawTextureLink(label="Metalness", url="/a/metalness.png"),
            RawTextureLink(label="Roughness", url="/a/rough.png"),
        ),
    )
    norm = normalize_material(raw)

    assert norm.resolution_px == 2048
    assert norm.physical_size_cm == 100.0
    assert norm.slug == "brushed-steel-panel"
    assert MapType.ALBEDO in norm.map_types
    assert MapType.METALLIC in norm.map_types
    assert MapType.ROUGHNESS in norm.map_types
    assert len(norm.material_id) == 16
