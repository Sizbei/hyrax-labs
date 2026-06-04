"""Playwright fetcher — guarded optional backend for JS-rendered suppliers.

Use this backend when a supplier renders its material grid client-side (SPA,
infinite scroll, lazy-loaded texture links) so the static HTML is empty. It
drives a headless Chromium, waits for network idle, and returns the fully
rendered DOM, which then flows through the same extractor as every other
backend.

The ``playwright`` import is deferred to call time. If the extra is not
installed, a clear :class:`MissingDependencyError` is raised that tells the user
exactly which extra to install. This keeps the architecture honest — the code is
real — while keeping the core install lightweight.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from hyrax_ingestion.fetchers.base import Fetcher, FetchResult, MissingDependencyError


class PlaywrightFetcher(Fetcher):
    """Headless-Chromium fetcher (requires the ``playwright`` extra)."""

    name = "playwright"

    def __init__(self, *, wait_until: str = "networkidle", timeout_ms: int = 15000) -> None:
        self.wait_until = wait_until
        self.timeout_ms = timeout_ms

    @staticmethod
    def _require_playwright():  # pragma: no cover - exercised only when installed
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:  # noqa: F841
            raise MissingDependencyError(
                backend="playwright", extra="playwright", import_name="playwright"
            ) from exc
        return sync_playwright

    def fetch(self, source: str) -> FetchResult:
        sync_playwright = self._require_playwright()

        # Local fixtures are addressed via file:// so the same code path works
        # in tests once the extra is installed.
        url = source
        if urlparse(source).scheme not in ("http", "https", "file"):
            url = Path(source).expanduser().resolve().as_uri()

        with sync_playwright() as p:  # pragma: no cover - needs browser binaries
            browser = p.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                page.goto(url, wait_until=self.wait_until, timeout=self.timeout_ms)
                html = page.content()
            finally:
                browser.close()
        return FetchResult(source=source, html=html, backend=self.name)
