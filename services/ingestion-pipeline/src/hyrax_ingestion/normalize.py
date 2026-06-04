"""RawMaterial -> NormalizedMaterial normalization.

Responsibilities:

* classify each texture link into a canonical :class:`MapType`;
* parse free-text resolution ("2K", "4096x4096") into integer pixels;
* parse free-text physical size ("200 cm", "1.5 m", "2000mm") into centimeters;
* slugify the name;
* compute a stable content hash (``material_id``) used for deduplication.
"""

from __future__ import annotations

import hashlib
import re

from hyrax_ingestion.models import (
    MapType,
    NormalizedMaterial,
    PbrTexture,
    RawMaterial,
)

# --- Map-type classification -------------------------------------------------

# Alias -> canonical map type. Matched against label and filename tokens.
_MAP_ALIASES: dict[MapType, tuple[str, ...]] = {
    MapType.ALBEDO: ("albedo", "basecolor", "base_color", "base color", "diffuse", "col", "color", "diff"),
    MapType.NORMAL: ("normal", "nrm", "norm", "nor", "bump"),
    MapType.ROUGHNESS: ("roughness", "rough", "rgh", "gloss"),
    MapType.METALLIC: ("metallic", "metalness", "metal", "mtl", "met"),
    MapType.AO: ("ao", "ambientocclusion", "ambient_occlusion", "ambient occlusion", "occlusion"),
}

_RESOLUTION_SHORTHAND = {"1k": 1024, "2k": 2048, "4k": 4096, "8k": 8192}

_TILE_UNITS_TO_CM = {"mm": 0.1, "cm": 1.0, "m": 100.0}


def _normalize_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


# Precomputed once: every (normalized-alias, map-type) pair, longest alias first,
# so a specific alias like "basecolor" is matched before a short one like "col".
_ORDERED_ALIASES: tuple[tuple[str, MapType], ...] = tuple(
    (_normalize_token(alias), mtype)
    for alias, mtype in sorted(
        (
            (alias, mtype)
            for mtype, aliases in _MAP_ALIASES.items()
            for alias in aliases
        ),
        key=lambda pair: len(_normalize_token(pair[0])),
        reverse=True,
    )
    if _normalize_token(alias)
)


def classify_map_type(label: str, url: str = "") -> MapType:
    """Classify a texture into a canonical PBR map type.

    Both the human label and the URL/filename are inspected; the label wins.
    Longer aliases are checked first so "basecolor" is not shadowed by "col".
    """

    label_norm = _normalize_token(label)
    url_norm = _normalize_token(url)

    # _ORDERED_ALIASES is precomputed once (longest-first) at import time.
    for token, mtype in _ORDERED_ALIASES:
        if token in label_norm:
            return mtype
    for token, mtype in _ORDERED_ALIASES:
        if token in url_norm:
            return mtype
    return MapType.UNKNOWN


# --- Unit parsing ------------------------------------------------------------

def parse_resolution(raw: str | None) -> int | None:
    """Parse free-text resolution into a square pixel count.

    Accepts "4096x4096", "4096 x 2048" (takes the larger axis), "4096", "2K".
    """

    if not raw:
        return None
    text = raw.strip().lower()

    if text in _RESOLUTION_SHORTHAND:
        return _RESOLUTION_SHORTHAND[text]

    # Explicit pixel dimensions win when present, e.g. "4096x4096",
    # "1920 x 1080", or a bare "4096". A "k"-shorthand token (the 2 in "2k") is
    # NOT an explicit dimension, so a stray "2k thumb" can't override real dims.
    explicit = [
        int(m.group(1))
        for m in re.finditer(r"(\d+)(?!\s*k\b)", text)
    ]
    if explicit:
        return max(explicit)

    # Otherwise fall back to "<n>k" shorthand anywhere in the string.
    shorthand = re.search(r"\b(\d+)\s*k\b", text)
    if shorthand:
        return int(shorthand.group(1)) * 1024
    return None


def parse_physical_size_cm(raw: str | None) -> float | None:
    """Parse a free-text tileable size into centimeters.

    Accepts "200 cm", "1.5 m", "2000mm", "200" (assumed cm).
    """

    if not raw:
        return None
    text = raw.strip().lower()
    match = re.search(r"([\d.]+)\s*(mm|cm|m)?", text)
    if not match:
        return None
    try:
        value = float(match.group(1))
    except ValueError:
        return None
    unit = match.group(2) or "cm"
    return round(value * _TILE_UNITS_TO_CM[unit], 4)


# --- Slug + identity ---------------------------------------------------------

def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "material"


def content_hash(supplier: str, name: str, texture_urls: tuple[str, ...]) -> str:
    """Stable identity hash for dedup.

    Two records from the same supplier with the same name and the same set of
    texture URLs are considered the same material, regardless of source page.
    """

    payload = "|".join(
        [supplier.strip().lower(), slugify(name), *sorted(u.strip().lower() for u in texture_urls)]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


# --- Top-level normalization -------------------------------------------------

def normalize_material(raw: RawMaterial) -> NormalizedMaterial:
    """Convert a single :class:`RawMaterial` into a catalog record."""

    textures = tuple(
        PbrTexture(
            map_type=classify_map_type(link.label, link.url),
            url=link.url,
            original_label=link.label,
        )
        for link in raw.texture_links
    )

    material_id = content_hash(raw.supplier, raw.name, tuple(t.url for t in textures))

    return NormalizedMaterial(
        material_id=material_id,
        supplier=raw.supplier,
        source_url=raw.source_url,
        name=raw.name.strip(),
        slug=slugify(raw.name),
        category=raw.category,
        resolution_px=parse_resolution(raw.resolution_raw),
        physical_size_cm=parse_physical_size_cm(raw.physical_size_raw),
        tags=raw.tags,
        textures=textures,
    )


def normalize_and_dedup(
    raws: list[RawMaterial],
) -> tuple[list[NormalizedMaterial], int]:
    """Normalize a batch and drop duplicates by ``material_id``.

    Returns ``(unique_materials, duplicates_dropped)``. First occurrence wins.
    """

    seen: dict[str, NormalizedMaterial] = {}
    duplicates = 0
    for raw in raws:
        material = normalize_material(raw)
        if material.material_id in seen:
            duplicates += 1
            continue
        seen[material.material_id] = material
    return list(seen.values()), duplicates
