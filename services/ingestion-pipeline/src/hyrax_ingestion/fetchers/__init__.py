"""Pluggable fetcher backends.

Each backend implements the :class:`~hyrax_ingestion.fetchers.base.Fetcher`
interface and is registered by name. The BeautifulSoup backend is fully
functional against local fixtures; the Playwright/Selenium/Crawlee backends are
real-but-guarded and require their respective optional extras.
"""

from hyrax_ingestion.fetchers.base import Fetcher, FetchResult, MissingDependencyError

__all__ = ["Fetcher", "FetchResult", "MissingDependencyError"]
