"""Pytest fixtures for ExperimentalHTTPServer tests."""

import tempfile
from pathlib import Path

import pytest

from src.http import HTTPRequest


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


def make_request(
    method: str = "GET",
    path: str = "/",
    headers: dict[str, str] | None = None,
    body: bytes = b"",
) -> HTTPRequest:
    """Build a minimal HTTPRequest from parts."""
    header_lines = [f"{method} {path} HTTP/1.1"]
    if headers:
        for k, v in headers.items():
            header_lines.append(f"{k}: {v}")
    if body:
        header_lines.append(f"Content-Length: {len(body)}")
    raw = "\r\n".join(header_lines).encode() + b"\r\n\r\n" + body
    return HTTPRequest(raw)
