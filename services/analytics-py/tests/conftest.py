"""Shared pytest fixtures.

Force the mongomock backend for the whole suite so tests never need a real
MongoDB, and reset the memoized Mongo client between tests for isolation.
"""
from __future__ import annotations

import os

os.environ.setdefault("MONGO_USE_MOCK", "1")

import pytest  # noqa: E402

from events import mongo  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_mongo():
    """Give every test a clean in-memory Mongo collection."""
    mongo.reset_client()
    yield
    mongo.reset_client()


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture
def make_engagement(db):
    """Factory that creates an AssetEngagement ORM row."""
    from datetime import datetime, timezone

    from events.models import AssetEngagement, Metric

    def _make(
        asset_id: str = "mat-000001",
        metric: str = Metric.VIEW.value,
        value: float = 1.0,
        recorded_at: datetime | None = None,
    ) -> AssetEngagement:
        return AssetEngagement.objects.create(
            asset_id=asset_id,
            metric=metric,
            value=value,
            recorded_at=recorded_at or datetime(2026, 3, 1, tzinfo=timezone.utc),
        )

    return _make
