"""HTML -> RawMaterial extraction using BeautifulSoup.

The synthetic supplier fixtures share a deliberately simple, consistent markup
contract so extraction is deterministic:

    <article class="material" data-category="...">
        <h2 class="material-name">...</h2>
        <ul class="material-meta">
            <li data-field="resolution">...</li>
            <li data-field="size">...</li>
        </ul>
        <ul class="material-tags"><li>tag</li>...</ul>
        <ul class="texture-maps">
            <li><a class="map-link" data-map="albedo" href="...">label</a></li>
            ...
        </ul>
    </article>

The supplier name comes from ``<meta name="supplier">``. Real supplier pages
vary; in practice you would write one small extractor per supplier template, all
producing the same :class:`RawMaterial`.
"""

from __future__ import annotations

from bs4 import BeautifulSoup

from hyrax_ingestion.fetchers.base import FetchResult
from hyrax_ingestion.models import RawMaterial, RawTextureLink


def _text(node) -> str:
    return node.get_text(strip=True) if node is not None else ""


def extract_materials(result: FetchResult) -> list[RawMaterial]:
    """Parse a fetched page into zero or more :class:`RawMaterial` records."""

    soup = BeautifulSoup(result.html, "lxml")

    supplier_meta = soup.find("meta", attrs={"name": "supplier"})
    supplier = (
        supplier_meta.get("content", "").strip() if supplier_meta else ""
    ) or "unknown-supplier"

    materials: list[RawMaterial] = []
    for article in soup.select("article.material"):
        name = _text(article.select_one(".material-name"))
        if not name:
            # Skip malformed cards rather than emitting junk records.
            continue

        category = article.get("data-category") or None

        resolution_raw = _meta_field(article, "resolution")
        size_raw = _meta_field(article, "size")

        tags = tuple(
            _text(li) for li in article.select(".material-tags li") if _text(li)
        )

        links: list[RawTextureLink] = []
        for a in article.select("ul.texture-maps a.map-link"):
            href = (a.get("href") or "").strip()
            if not href:
                continue
            # Prefer the explicit data-map hint, fall back to anchor text.
            label = (a.get("data-map") or _text(a)).strip()
            links.append(RawTextureLink(label=label, url=href))

        materials.append(
            RawMaterial(
                supplier=supplier,
                source_url=result.source,
                name=name,
                category=category,
                resolution_raw=resolution_raw,
                physical_size_raw=size_raw,
                tags=tags,
                texture_links=tuple(links),
            )
        )

    return materials


def _meta_field(article, field: str) -> str | None:
    node = article.select_one(f'.material-meta li[data-field="{field}"]')
    if node is None:
        return None
    text = node.get_text(strip=True)
    # Meta items look like "Resolution: 4096x4096"; keep only the value part.
    if ":" in text:
        text = text.split(":", 1)[1].strip()
    return text or None
