"""Crawlee fetcher — guarded optional backend for large-scale crawls.

Crawlee is the right tool when ingestion has to *discover* thousands of supplier
material URLs by following pagination and category links, with built-in request
queues, autoscaling concurrency, retries, and politeness/rate-limiting. The
other three backends fetch a known list of pages; Crawlee is what you reach for
when the URL frontier itself must be crawled.

The ``crawlee`` import is deferred; absence raises a clear
:class:`MissingDependencyError`.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from hyrax_ingestion.fetchers.base import Fetcher, FetchResult, MissingDependencyError


class CrawleeFetcher(Fetcher):
    """Crawlee-backed fetcher (requires the ``crawlee`` extra)."""

    name = "crawlee"

    def __init__(self, *, max_concurrency: int = 10) -> None:
        self.max_concurrency = max_concurrency

    @staticmethod
    def _require_crawlee():  # pragma: no cover - exercised only when installed
        try:
            import crawlee  # noqa: F401
        except ImportError as exc:  # noqa: F841
            raise MissingDependencyError(
                backend="crawlee", extra="crawlee", import_name="crawlee"
            ) from exc
        return crawlee

    def fetch(self, source: str) -> FetchResult:
        self._require_crawlee()

        # For a single static source Crawlee is overkill, so we read the page
        # directly once the dependency check passes. The real value of this
        # backend is fetch_many() over a discovered frontier.
        url = source
        if urlparse(source).scheme in ("http", "https"):  # pragma: no cover
            import requests

            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            html = resp.text
        else:  # pragma: no cover
            html = Path(source).expanduser().read_text(encoding="utf-8")
        return FetchResult(source=source, html=html, backend=self.name)

    def fetch_many(self, sources: list[str]) -> list[FetchResult]:  # pragma: no cover
        # A faithful sketch of the Crawlee request-queue pattern. Kept guarded so
        # the module imports without the extra; real runs need the library.
        self._require_crawlee()
        from crawlee.crawlers import BeautifulSoupCrawler, BeautifulSoupCrawlingContext

        results: list[FetchResult] = []
        crawler = BeautifulSoupCrawler(max_requests_per_crawl=len(sources))

        @crawler.router.default_handler
        async def _handler(context: BeautifulSoupCrawlingContext) -> None:
            results.append(
                FetchResult(
                    source=context.request.url,
                    html=str(context.soup),
                    backend=self.name,
                )
            )

        crawler.run(sources)
        return results
