"""Fixture parsing / extraction tests."""

from __future__ import annotations

from hyrax_ingestion.extract import extract_materials
from hyrax_ingestion.fetchers.soup_fetcher import SoupFetcher


def test_extract_parses_aurora_fixture(aurora_fixture: str) -> None:
    result = SoupFetcher().fetch(aurora_fixture)
    materials = extract_materials(result)

    assert len(materials) == 2
    granite = next(m for m in materials if m.name == "Weathered Granite 03")
    assert granite.supplier == "Aurora Surfaces"
    assert granite.category == "stone"
    assert granite.resolution_raw == "4096x4096"
    assert granite.physical_size_raw == "200 cm"
    assert "granite" in granite.tags
    assert len(granite.texture_links) == 4


def test_extract_skips_malformed_card(fixtures_dir) -> None:
    result = SoupFetcher().fetch(str(fixtures_dir / "everest-stone.html"))
    materials = extract_materials(result)

    # Two <article.material> cards exist, but one has no name and is skipped.
    assert len(materials) == 1
    assert materials[0].name == "Slate Roof Tiles"


def test_extract_keeps_links_without_data_map(fixtures_dir) -> None:
    result = SoupFetcher().fetch(str(fixtures_dir / "dune-supply.html"))
    materials = extract_materials(result)
    mud = next(m for m in materials if m.name == "Cracked Mud Flat")
    # No data-map hints, but the links are still captured (label falls back).
    assert len(mud.texture_links) == 3
    assert all(link.url for link in mud.texture_links)
