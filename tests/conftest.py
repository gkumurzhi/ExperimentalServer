"""Pytest fixtures for ExperimentalHTTPServer tests."""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_file(temp_dir: Path) -> Path:
    """Create a sample file for testing."""
    file_path = temp_dir / "test_file.txt"
    file_path.write_text("Hello, World!")
    return file_path


@pytest.fixture
def upload_dir(temp_dir: Path) -> Path:
    """Create an uploads directory for testing."""
    uploads = temp_dir / "uploads"
    uploads.mkdir(exist_ok=True)
    return uploads
