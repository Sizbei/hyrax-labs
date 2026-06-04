"""BeautifulSoup fetcher — the default, fully-functional backend.

This backend reads static HTML directly. For the synthetic supplier fixtures it
simply loads the file off disk; for ``http(s)`` sources it uses ``requests``.
There is no JavaScript execution, which is exactly why it is fast and the right
default for server-rendered supplier catalogs.

Note: BeautifulSoup itself is a *parser*, used in :mod:`hyrax_ingestion.extract`.
This fetcher pairs the requests/file transport with that parser to form the
end-to-end "BeautifulSoup path".
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from hyrax_ingestion.fetchers.base import Fetcher, FetchResult


class SoupFetcher(Fetcher):
    """Static-HTML fetcher backed by the filesystem or ``requests``."""

    name = "soup"

    def __init__(self, *, timeout: float = 10.0, encoding: str = "utf-8") -> None:
        self.timeout = timeout
        self.encoding = encoding

    def fetch(self, source: str) -> FetchResult:
        parsed = urlparse(source)
        if parsed.scheme in ("http", "https"):
            html = self._fetch_http(source)
        else:
            html = self._fetch_file(source)
        return FetchResult(source=source, html=html, backend=self.name)

    def _fetch_file(self, source: str) -> str:
        path = Path(source).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f"fixture not found: {path}")
        return path.read_text(encoding=self.encoding)

    def _fetch_http(self, source: str) -> str:
        # Imported lazily so a missing/old requests build never breaks file mode.
        import requests

        resp = requests.get(source, timeout=self.timeout)
        resp.raise_for_status()
        return resp.text
