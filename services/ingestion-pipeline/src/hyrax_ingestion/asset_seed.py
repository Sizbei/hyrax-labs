"""Bridge to the metrics-dashboard.

Maps the normalized material catalog onto the dashboard's `Asset` shape so the
two services form one end-to-end flow: scraped supplier materials become the
content assets whose engagement the dashboard visualizes.

The dashboard `Asset` shape (see services/metrics-dashboard/src/types.ts):
    { id, title, type, channel, publishedAt }
where `type` is one of: video | article | image | short | carousel.

All output is synthetic and deterministic — `publishedAt` is derived from the
material's stable content hash, not a real timestamp.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from hyrax_ingestion.models import NormalizedMaterial

# Dashboard asset types (mirrors the TS union).
_ASSET_TYPES = ("video", "article", "image", "short", "carousel")

# A stable epoch the deterministic publish dates are offset from.
_EPOCH = datetime(2025, 1, 1, tzinfo=timezone.utc)


def _asset_type_for(material: NormalizedMaterial) -> str:
    """Pick a dashboard asset type deterministically from the material hash."""
    idx = int(material.material_id[:8], 16) % len(_ASSET_TYPES)
    return _ASSET_TYPES[idx]


def _published_at(material: NormalizedMaterial) -> str:
    """Derive a deterministic ISO publish date from the material hash.

    `material_id` is a 16-char hex content-hash slice, so [8:12] is always four
    valid hex digits; this is purely synthetic, not a real publish timestamp.
    """
    days = int(material.material_id[8:12], 16) % 365
    return (_EPOCH + timedelta(days=days)).date().isoformat()


def material_to_asset(material: NormalizedMaterial) -> dict:
    """Map one normalized material to a dashboard `Asset` record."""
    return {
        "id": material.material_id,
        "title": material.name,
        "type": _asset_type_for(material),
        "channel": material.supplier,
        "publishedAt": _published_at(material),
    }


def build_asset_seed(materials: list[NormalizedMaterial]) -> list[dict]:
    """Map the whole catalog to dashboard assets."""
    return [material_to_asset(m) for m in materials]


def write_asset_seed(
    materials: list[NormalizedMaterial], path: str | Path
) -> Path:
    """Write a dashboard-compatible asset-seed JSON array."""
    out = Path(path).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    assets = build_asset_seed(materials)
    out.write_text(
        json.dumps(assets, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return out
