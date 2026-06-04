"""Tests for the seed_events management command and deterministic generator."""
from __future__ import annotations

from io import StringIO

import pytest
from django.core.management import call_command

from events import mongo
from events.models import AssetEngagement
from events.seeding import generate_events

pytestmark = pytest.mark.django_db


def test_generator_is_deterministic():
    a = list(generate_events(50, seed=1729))
    b = list(generate_events(50, seed=1729))
    assert a == b
    # A different seed yields a different stream.
    c = list(generate_events(50, seed=2024))
    assert a != c


def test_generator_rating_values_in_range():
    for e in generate_events(200):
        if e["metric"] == "rating":
            assert 1.0 <= e["value"] <= 5.0
        else:
            assert e["value"] == 1.0


def test_seed_command_populates_both_stores():
    out = StringIO()
    call_command("seed_events", "--count", "100", stdout=out)
    assert AssetEngagement.objects.count() == 100
    assert mongo.count() == 100
    assert "Seeded 100 events" in out.getvalue()


def test_seed_command_clear_flag():
    call_command("seed_events", "--count", "20")
    call_command("seed_events", "--count", "10", "--clear")
    # --clear wipes prior data, so only the second batch remains.
    assert AssetEngagement.objects.count() == 10
    assert mongo.count() == 10
