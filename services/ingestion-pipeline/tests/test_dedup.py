"""Deduplication tests."""

from __future__ import annotations

from hyrax_ingestion.models import RawMaterial, RawTextureLink
from hyrax_ingestion.normalize import content_hash, normalize_and_dedup


def _raw(source: str, name: str = "Weathered Granite 03") -> RawMaterial:
    return RawMaterial(
        supplier="Aurora Surfaces",
        source_url=source,
        name=name,
        texture_links=(
            RawTextureLink(label="albedo", url="/a/albedo.png"),
            RawTextureLink(label="normal", url="/a/normal.png"),
        ),
    )


def test_content_hash_is_stable_across_pages() -> None:
    h1 = content_hash("Aurora Surfaces", "Weathered Granite 03", ("/a/albedo.png", "/a/normal.png"))
    # Order of urls must not matter.
    h2 = content_hash("Aurora Surfaces", "Weathered Granite 03", ("/a/normal.png", "/a/albedo.png"))
    assert h1 == h2


def test_dedup_drops_cross_page_duplicate() -> None:
    raws = [_raw("page-a.html"), _raw("page-b.html")]
    materials, dropped = normalize_and_dedup(raws)
    assert dropped == 1
    assert len(materials) == 1
    # First occurrence wins.
    assert materials[0].source_url == "page-a.html"


def test_distinct_materials_are_not_deduped() -> None:
    raws = [_raw("page-a.html", "Granite A"), _raw("page-b.html", "Granite B")]
    materials, dropped = normalize_and_dedup(raws)
    assert dropped == 0
    assert len(materials) == 2
