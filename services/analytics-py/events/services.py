"""Business logic for analytics aggregation.

Kept out of the views so the ORM aggregation and the Mongo cross-reference are
unit-testable in isolation.
"""
from __future__ import annotations

from typing import Any

from django.db.models import Avg, Count, Sum

from . import mongo
from .models import AssetEngagement


def per_metric_summary() -> list[dict[str, Any]]:
    """
    Aggregate the ORM rows into one summary record per metric.

    Returns a list of dicts matching ``MetricSummarySerializer``.
    """
    rows = (
        AssetEngagement.objects.values("metric")
        .annotate(
            count=Count("id"),
            total_value=Sum("value"),
            average_value=Avg("value"),
            unique_assets=Count("asset_id", distinct=True),
        )
        .order_by("metric")
    )
    return [
        {
            "metric": row["metric"],
            "count": row["count"],
            "total_value": round(row["total_value"] or 0.0, 4),
            "average_value": round(row["average_value"] or 0.0, 4),
            "unique_assets": row["unique_assets"],
        }
        for row in rows
    ]


def summary_payload(top_n: int = 5) -> dict[str, Any]:
    """
    Build the full ``/api/analytics/summary`` payload: per-metric ORM
    aggregates plus the top assets sourced from the Mongo raw log.
    """
    return {
        "per_metric": per_metric_summary(),
        "top_assets": mongo.top_assets(limit=top_n),
        "raw_event_count": mongo.count(),
        "mongo_backend": mongo.active_backend(),
    }
