"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path
import pytest


@pytest.fixture
def tmp_db_path(tmp_path: Path) -> Path:
    """Provide a temporary database path for tests."""
    return tmp_path / "test.db"


@pytest.fixture
def tmp_download_dir(tmp_path: Path) -> Path:
    """Provide a temporary download directory for tests."""
    download_dir = tmp_path / "downloads"
    download_dir.mkdir(parents=True, exist_ok=True)
    return download_dir


@pytest.fixture
def app_config_overrides() -> dict[str, str]:
    """Temporary config overrides for tests."""
    return {}
