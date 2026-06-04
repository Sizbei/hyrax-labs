"""Hyrax Labs multi-tool supplier-material ingestion pipeline.

A representative data-engineering scaffold: it scrapes synthetic supplier
material listings (from committed local HTML fixtures), extracts raw records,
and normalizes them into a Physically Based Rendering (PBR) texture catalog.

The package demonstrates an adapter architecture where four scraping/automation
backends (BeautifulSoup, Playwright, Selenium, Crawlee) are pluggable fetchers
selected at runtime via a registry. Only the BeautifulSoup adapter is required
for the core pipeline; the browser backends are optional extras.
"""

from hyrax_ingestion.models import (
    IngestionResult,
    MapType,
    NormalizedMaterial,
    PbrTexture,
    RawMaterial,
)

__all__ = [
    "IngestionResult",
    "MapType",
    "NormalizedMaterial",
    "PbrTexture",
    "RawMaterial",
    "__version__",
]

__version__ = "0.1.0"
