"""Tests for the Mongo raw-event repository against mongomock."""
from __future__ import annotations

from events import mongo


def test_backend_is_mongomock_in_tests():
    mongo.get_collection()
    assert mongo.active_backend() == "mongomock"


def test_insert_and_count():
    mongo.insert_event({"asset_id": "mat-1", "metric": "view", "value": 1.0})
    mongo.insert_event({"asset_id": "mat-1", "metric": "download", "value": 1.0})
    assert mongo.count() == 2
    assert mongo.count(metric="view") == 1


def test_insert_many_and_clear():
    inserted = mongo.insert_many(
        [{"asset_id": "mat-x", "metric": "view", "value": 1.0} for _ in range(5)]
    )
    assert inserted == 5
    assert mongo.count() == 5
    mongo.clear()
    assert mongo.count() == 0


def test_top_assets_aggregation_pipeline():
    docs = (
        [{"asset_id": "mat-hot", "metric": "view", "value": 1.0}] * 5
        + [{"asset_id": "mat-mid", "metric": "view", "value": 1.0}] * 3
        + [{"asset_id": "mat-cold", "metric": "view", "value": 1.0}] * 1
    )
    mongo.insert_many(docs)

    top = mongo.top_assets(limit=2)
    assert top == [
        {"asset_id": "mat-hot", "event_count": 5},
        {"asset_id": "mat-mid", "event_count": 3},
    ]


def test_reset_client_isolation():
    mongo.insert_event({"asset_id": "mat-1", "metric": "view", "value": 1.0})
    assert mongo.count() == 1
    mongo.reset_client()
    # Fresh in-memory collection after reset.
    assert mongo.count() == 0
