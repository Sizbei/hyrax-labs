"""Fetcher registry and guarded-backend tests."""

from __future__ import annotations

import importlib.util

import pytest

from hyrax_ingestion.fetchers.base import Fetcher, MissingDependencyError
from hyrax_ingestion.fetchers.registry import (
    available_fetchers,
    get_fetcher,
)
from hyrax_ingestion.fetchers.soup_fetcher import SoupFetcher


def test_registry_lists_all_four_backends() -> None:
    names = available_fetchers()
    assert set(names) == {"soup", "playwright", "selenium", "crawlee"}


def test_get_fetcher_returns_instances() -> None:
    fetcher = get_fetcher("soup")
    assert isinstance(fetcher, SoupFetcher)
    assert isinstance(fetcher, Fetcher)


def test_get_unknown_fetcher_raises() -> None:
    with pytest.raises(KeyError):
        get_fetcher("does-not-exist")


@pytest.mark.parametrize("backend,module", [
    ("playwright", "playwright"),
    ("selenium", "selenium"),
    ("crawlee", "crawlee"),
])
def test_guarded_backends_raise_clear_error_when_absent(backend, module) -> None:
    """If the optional lib is not installed, fetch() must explain the fix."""

    if importlib.util.find_spec(module) is not None:
        pytest.skip(f"{module} is installed; skipping missing-dependency check")

    fetcher = get_fetcher(backend)
    with pytest.raises(MissingDependencyError) as excinfo:
        fetcher.fetch("file://whatever.html")
    msg = str(excinfo.value)
    assert backend in msg
    assert "pip install" in msg
