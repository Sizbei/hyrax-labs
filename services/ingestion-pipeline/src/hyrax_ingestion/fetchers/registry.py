"""Fetcher registry — selects a backend by name.

Importing an adapter module does *not* import its heavyweight dependency (those
imports are deferred to ``fetch`` time), so the registry can safely know about
all four backends regardless of which extras are installed.
"""

from __future__ import annotations

from hyrax_ingestion.fetchers.base import Fetcher
from hyrax_ingestion.fetchers.crawlee_fetcher import CrawleeFetcher
from hyrax_ingestion.fetchers.playwright_fetcher import PlaywrightFetcher
from hyrax_ingestion.fetchers.selenium_fetcher import SeleniumFetcher
from hyrax_ingestion.fetchers.soup_fetcher import SoupFetcher

_REGISTRY: dict[str, type[Fetcher]] = {
    SoupFetcher.name: SoupFetcher,
    PlaywrightFetcher.name: PlaywrightFetcher,
    SeleniumFetcher.name: SeleniumFetcher,
    CrawleeFetcher.name: CrawleeFetcher,
}

DEFAULT_FETCHER = SoupFetcher.name


def available_fetchers() -> tuple[str, ...]:
    """Return the sorted names of all registered backends."""

    return tuple(sorted(_REGISTRY))


def get_fetcher(name: str, **kwargs: object) -> Fetcher:
    """Instantiate a fetcher backend by name.

    Raises:
        KeyError: if ``name`` is not a registered backend.
    """

    try:
        cls = _REGISTRY[name]
    except KeyError as exc:
        raise KeyError(
            f"unknown fetcher '{name}'. "
            f"available: {', '.join(available_fetchers())}"
        ) from exc
    return cls(**kwargs)  # type: ignore[arg-type]
