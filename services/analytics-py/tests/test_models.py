"""Model-level tests for AssetEngagement."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from events.models import AssetEngagement, Metric

pytestmark = pytest.mark.django_db


def test_create_and_str(make_engagement):
    e = make_engagement(asset_id="mat-000007", metric=Metric.DOWNLOAD.value)
    assert AssetEngagement.objects.count() == 1
    assert str(e) == "mat-000007 download=1.0"


def test_default_ordering_is_recorded_at_desc(make_engagement):
    older = make_engagement(recorded_at=datetime(2026, 1, 1, tzinfo=timezone.utc))
    newer = make_engagement(recorded_at=datetime(2026, 6, 1, tzinfo=timezone.utc))
    ordered = list(AssetEngagement.objects.all())
    assert ordered[0] == newer
    assert ordered[1] == older


def test_queryset_helpers(make_engagement):
    make_engagement(asset_id="mat-A", metric=Metric.VIEW.value)
    make_engagement(asset_id="mat-A", metric=Metric.RATING.value, value=4.0)
    make_engagement(asset_id="mat-B", metric=Metric.VIEW.value)

    assert AssetEngagement.objects.for_asset("mat-A").count() == 2
    assert AssetEngagement.objects.for_metric(Metric.VIEW.value).count() == 2
    assert (
        AssetEngagement.objects.for_asset("mat-A")
        .for_metric(Metric.RATING.value)
        .count()
        == 1
    )


def test_metric_choices_cover_domain():
    assert {m.value for m in Metric} == {"view", "download", "rating"}
