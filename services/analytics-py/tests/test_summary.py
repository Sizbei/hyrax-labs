"""Tests for the aggregate analytics summary endpoint and service layer."""
from __future__ import annotations

import pytest

from events import mongo, services
from events.models import Metric

pytestmark = pytest.mark.django_db


def _seed_orm_and_mongo(make_engagement):
    # 3 views on mat-A, 1 download on mat-A, 2 ratings on mat-B
    make_engagement(asset_id="mat-A", metric=Metric.VIEW.value)
    make_engagement(asset_id="mat-A", metric=Metric.VIEW.value)
    make_engagement(asset_id="mat-A", metric=Metric.VIEW.value)
    make_engagement(asset_id="mat-A", metric=Metric.DOWNLOAD.value)
    make_engagement(asset_id="mat-B", metric=Metric.RATING.value, value=4.0)
    make_engagement(asset_id="mat-B", metric=Metric.RATING.value, value=2.0)

    mongo.insert_many(
        [{"asset_id": "mat-A", "metric": "view", "value": 1.0}] * 4
        + [{"asset_id": "mat-B", "metric": "rating", "value": 3.0}] * 2
    )


def test_per_metric_summary_service(make_engagement):
    _seed_orm_and_mongo(make_engagement)
    summary = {row["metric"]: row for row in services.per_metric_summary()}

    assert summary["view"]["count"] == 3
    assert summary["view"]["unique_assets"] == 1
    assert summary["download"]["count"] == 1
    assert summary["rating"]["count"] == 2
    assert summary["rating"]["total_value"] == 6.0
    assert summary["rating"]["average_value"] == 3.0


def test_summary_endpoint(api_client, make_engagement):
    _seed_orm_and_mongo(make_engagement)
    resp = api_client.get("/api/analytics/summary/")
    assert resp.status_code == 200
    body = resp.json()

    assert {r["metric"] for r in body["per_metric"]} == {"view", "download", "rating"}
    assert body["raw_event_count"] == 6
    assert body["mongo_backend"] == "mongomock"
    # Top asset by raw event count is mat-A (4 events).
    assert body["top_assets"][0]["asset_id"] == "mat-A"
    assert body["top_assets"][0]["event_count"] == 4


def test_summary_top_n_param(api_client, make_engagement):
    _seed_orm_and_mongo(make_engagement)
    resp = api_client.get("/api/analytics/summary/?top_n=1")
    assert resp.status_code == 200
    assert len(resp.json()["top_assets"]) == 1
