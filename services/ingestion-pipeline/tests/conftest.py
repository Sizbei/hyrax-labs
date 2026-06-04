"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    assert FIXTURES_DIR.is_dir(), f"missing fixtures dir: {FIXTURES_DIR}"
    return FIXTURES_DIR


@pytest.fixture(scope="session")
def fixture_files(fixtures_dir: Path) -> list[str]:
    files = [str(p) for p in sorted(fixtures_dir.glob("*.html"))]
    assert files, "no HTML fixtures found"
    return files


@pytest.fixture
def aurora_fixture(fixtures_dir: Path) -> str:
    return str(fixtures_dir / "aurora-surfaces.html")
