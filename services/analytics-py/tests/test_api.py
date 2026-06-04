"""DRF endpoint tests using APIClient."""
from __future__ import annotations

import pytest

from events.models import AssetEngagement, Metric

pytestmark = pytest.mark.django_db


def test_list_events_is_paginated(api_client, make_engagement):
    for _ in range(3):
        make_engagement()
    resp = api_client.get("/api/events/")
    assert resp.status_code == 200
    body = resp.json()
    # PageNumberPagination envelope.
    assert set(body) >= {"count", "next", "previous", "results"}
    assert body["count"] == 3
    assert len(body["results"]) == 3


def test_create_event_writes_orm_and_mongo(api_client):
    from events import mongo

    payload = {
        "asset_id": "mat-000042",
        "metric": Metric.DOWNLOAD.value,
        "value": 1.0,
        "recorded_at": "2026-03-01T12:00:00Z",
    }
    resp = api_client.post("/api/events/", payload, format="json")
    assert resp.status_code == 201
    assert AssetEngagement.objects.filter(asset_id="mat-000042").exists()
    # The create path mirrors into the Mongo raw log.
    assert mongo.count() == 1


def test_create_rejects_out_of_range_rating(api_client):
    payload = {
        "asset_id": "mat-1",
        "metric": Metric.RATING.value,
        "value": 9.0,
        "recorded_at": "2026-03-01T12:00:00Z",
    }
    resp = api_client.post("/api/events/", payload, format="json")
    assert resp.status_code == 400
    assert "value" in resp.json()


def test_create_rejects_blank_asset_id(api_client):
    payload = {
        "asset_id": "   ",
        "metric": Metric.VIEW.value,
        "value": 1.0,
        "recorded_at": "2026-03-01T12:00:00Z",
    }
    resp = api_client.post("/api/events/", payload, format="json")
    assert resp.status_code == 400
    assert "asset_id" in resp.json()


def test_filter_by_metric_and_asset(api_client, make_engagement):
    make_engagement(asset_id="mat-A", metric=Metric.VIEW.value)
    make_engagement(asset_id="mat-A", metric=Metric.DOWNLOAD.value)
    make_engagement(asset_id="mat-B", metric=Metric.VIEW.value)

    resp = api_client.get("/api/events/?metric=view")
    assert resp.json()["count"] == 2

    resp = api_client.get("/api/events/?asset_id=mat-A")
    assert resp.json()["count"] == 2

    resp = api_client.get("/api/events/?asset_id=mat-A&metric=download")
    assert resp.json()["count"] == 1


def test_retrieve_single_event(api_client, make_engagement):
    e = make_engagement(asset_id="mat-99")
    resp = api_client.get(f"/api/events/{e.id}/")
    assert resp.status_code == 200
    assert resp.json()["asset_id"] == "mat-99"


def test_healthcheck(api_client):
    resp = api_client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
