"""Base fetcher contract shared by every backend adapter.

A *fetcher* turns a source (a local fixture path or a URL) into raw HTML plus
provenance metadata. Keeping this interface tiny is what lets four very
different tools — a pure-Python parser, two browser drivers, and a crawler
framework — be swapped transparently behind the pipeline.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


class MissingDependencyError(RuntimeError):
    """Raised when an optional backend is selected but its library is absent.

    The message always names the extra to install so the failure is actionable.
    """

    def __init__(self, backend: str, extra: str, import_name: str) -> None:
        super().__init__(
            f"The '{backend}' fetcher requires the optional '{import_name}' "
            f"package, which is not installed. Install it with:\n\n"
            f"    pip install 'hyrax-ingestion[{extra}]'\n"
        )
        self.backend = backend
        self.extra = extra
        self.import_name = import_name


@dataclass(frozen=True, slots=True)
class FetchResult:
    """HTML payload plus the canonical source identifier it came from."""

    source: str
    html: str
    backend: str


class Fetcher(ABC):
    """Abstract base for all fetcher backends."""

    #: Stable backend name used by the registry / CLI ``--fetcher`` flag.
    name: str = "base"

    @abstractmethod
    def fetch(self, source: str) -> FetchResult:
        """Fetch a single source (fixture path or URL) and return its HTML."""

    def fetch_many(self, sources: list[str]) -> list[FetchResult]:
        """Fetch many sources sequentially.

        Backends with native concurrency (e.g. Crawlee) may override this; the
        pipeline also provides its own pool-based concurrency on top.
        """

        return [self.fetch(s) for s in sources]
