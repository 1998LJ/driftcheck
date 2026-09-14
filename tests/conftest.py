"""Pytest fixtures for driftcheck tests."""

import pytest
from pathlib import Path


@pytest.fixture
def temp_empty_repo(tmp_path: Path) -> Path:
    """Return a path to a fresh empty directory for testing detectors.

    Usage: def test_xxx(temp_empty_repo): ...
    """
    return tmp_path
