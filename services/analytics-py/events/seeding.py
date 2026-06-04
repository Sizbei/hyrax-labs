"""Deterministic synthetic-event generation.

All data here is fabricated for demonstration only. A fixed RNG seed makes the
output reproducible across runs and machines.
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from typing import Any, Iterator

from .models import Metric

DEFAULT_SEED = 1729
# A small synthetic catalog of material/texture asset ids.
ASSET_POOL = [f"mat-{i:06d}" for i in range(1, 21)]
_EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)


def generate_events(count: int, seed: int = DEFAULT_SEED) -> Iterator[dict[str, Any]]:
    """
    Yield ``count`` synthetic engagement events deterministically.

    Each event is a plain dict with ``asset_id``, ``metric``, ``value`` and a
    timezone-aware ``recorded_at`` datetime.
    """
    rng = random.Random(seed)
    metrics = [Metric.VIEW.value, Metric.DOWNLOAD.value, Metric.RATING.value]
    weights = [0.6, 0.3, 0.1]  # views dominate, ratings are rare

    for i in range(count):
        asset_id = rng.choice(ASSET_POOL)
        metric = rng.choices(metrics, weights=weights, k=1)[0]
        if metric == Metric.RATING.value:
            value = float(rng.randint(1, 5))
        else:
            value = 1.0
        recorded_at = _EPOCH + timedelta(minutes=rng.randint(0, 60 * 24 * 90))
        yield {
            "asset_id": asset_id,
            "metric": metric,
            "value": value,
            "recorded_at": recorded_at,
        }
