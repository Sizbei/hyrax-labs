"""Selenium fetcher — guarded optional backend.

Selenium is the pragmatic choice for legacy supplier portals that gate their
catalog behind a login form, an "I am not a robot" interstitial, or a
WebDriver-only flow that Playwright's bundled browsers don't reproduce. It uses
an existing system Chrome/Chromedriver, which is sometimes the only browser
allowed inside a corporate network.

The ``selenium`` import is deferred; absence raises a clear
:class:`MissingDependencyError`.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from hyrax_ingestion.fetchers.base import Fetcher, FetchResult, MissingDependencyError


class SeleniumFetcher(Fetcher):
    """WebDriver-based fetcher (requires the ``selenium`` extra)."""

    name = "selenium"

    def __init__(self, *, page_load_timeout: int = 20) -> None:
        self.page_load_timeout = page_load_timeout

    @staticmethod
    def _require_selenium():  # pragma: no cover - exercised only when installed
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
        except ImportError as exc:  # noqa: F841
            raise MissingDependencyError(
                backend="selenium", extra="selenium", import_name="selenium"
            ) from exc
        return webdriver, Options

    def fetch(self, source: str) -> FetchResult:
        webdriver, Options = self._require_selenium()

        url = source
        if urlparse(source).scheme not in ("http", "https", "file"):
            url = Path(source).expanduser().resolve().as_uri()

        options = Options()  # pragma: no cover - needs a real webdriver
        options.add_argument("--headless=new")
        driver = webdriver.Chrome(options=options)
        try:  # pragma: no cover - needs a real webdriver
            driver.set_page_load_timeout(self.page_load_timeout)
            driver.get(url)
            html = driver.page_source
        finally:  # pragma: no cover
            driver.quit()
        return FetchResult(source=source, html=html, backend=self.name)
