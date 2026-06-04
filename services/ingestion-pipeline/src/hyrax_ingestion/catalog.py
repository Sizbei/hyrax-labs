"""Catalog writers — persist normalized materials to JSON / JSONL."""

from __future__ import annotations

import json
from pathlib import Path

from hyrax_ingestion.models import NormalizedMaterial


def _to_record(material: NormalizedMaterial) -> dict:
    return material.model_dump(mode="json")


def write_json(materials: list[NormalizedMaterial], path: str | Path) -> Path:
    """Write the catalog as a single pretty-printed JSON array."""

    out = Path(path).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    records = [_to_record(m) for m in materials]
    out.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def write_jsonl(materials: list[NormalizedMaterial], path: str | Path) -> Path:
    """Write the catalog as newline-delimited JSON (one material per line)."""

    out = Path(path).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(_to_record(m), ensure_ascii=False) for m in materials]
    out.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return out


def write_catalog(
    materials: list[NormalizedMaterial], path: str | Path
) -> Path:
    """Dispatch to a writer based on the output file extension."""

    out = Path(path)
    if out.suffix.lower() == ".jsonl":
        return write_jsonl(materials, out)
    return write_json(materials, out)
