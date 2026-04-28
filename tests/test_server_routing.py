"""Tests for server method routing and advanced upload routing (B44)."""

import fnmatch
import json
import subprocess
import threading
from html.parser import HTMLParser
from pathlib import Path

import pytest

from src.handlers import HandlerMixin
from src.handlers.base import get_package_resource
from src.http import HTTPRequest, HTTPResponse

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
    import tomli as tomllib


class ScriptSrcParser(HTMLParser):
    """Collect script src attributes from bundled HTML."""

    def __init__(self):
        super().__init__()
        self.script_srcs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "script":
            return

        attr_map = dict(attrs)
        src = attr_map.get("src")
        if src:
            self.script_srcs.append(src)


class StubServer(HandlerMixin):
    """Minimal server stub for routing tests."""

    def __init__(self, root_dir: Path, upload_dir: Path):
        self.root_dir = root_dir
        self.upload_dir = upload_dir
        self.notes_dir = root_dir / "notes"
        self.notes_dir.mkdir(exist_ok=True)
        self.cors_origin = None
        self._temp_smuggle_files: set[str] = set()
        self._smuggle_lock = threading.Lock()
        self._notes_lock = threading.Lock()
        self._ecdh_manager = None
        self.advanced_upload_enabled = False
        self.method_handlers = self.build_method_handlers()

    def get_metrics(self):
        return {
            "uptime_seconds": 0,
            "total_requests": 0,
            "total_errors": 0,
            "bytes_sent": 0,
            "status_counts": {},
        }


def _make_request(
    method: str, path: str = "/", body: bytes = b"", headers: dict[str, str] | None = None
) -> HTTPRequest:
    lines = [f"{method} {path} HTTP/1.1"]
    if headers:
        for k, v in headers.items():
            lines.append(f"{k}: {v}")
    if body:
        lines.append(f"Content-Length: {len(body)}")
    raw = "\r\n".join(lines).encode() + b"\r\n\r\n" + body
    return HTTPRequest(raw)


def _index_local_script_resource_paths() -> list[str]:
    index_path = get_package_resource("index.html")
    assert index_path is not None

    parser = ScriptSrcParser()
    parser.feed(index_path.read_text(encoding="utf-8"))
    return [
        src.lstrip("/")
        for src in parser.script_srcs
        if src.startswith("/") and not src.startswith("//")
    ]


def _src_package_data_patterns() -> list[str]:
    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    with pyproject_path.open("rb") as pyproject_file:
        pyproject = tomllib.load(pyproject_file)

    patterns = pyproject["tool"]["setuptools"]["package-data"]["src"]
    assert isinstance(patterns, list)
    return [str(pattern) for pattern in patterns]


@pytest.fixture
def temp_dir():
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        (p / "index.html").write_text("<html>test</html>")
        yield p


@pytest.fixture
def upload_dir(temp_dir):
    u = temp_dir / "uploads"
    u.mkdir()
    return u


@pytest.fixture
def server(temp_dir, upload_dir):
    return StubServer(temp_dir, upload_dir)


class TestMethodRouting:
    """Test that standard method_handlers dispatch is correct."""

    def test_all_standard_methods_registered(self, server):
        expected = {
            "GET",
            "HEAD",
            "POST",
            "PUT",
            "PATCH",
            "DELETE",
            "OPTIONS",
            "FETCH",
            "INFO",
            "PING",
            "NOTE",
            "NONE",
            "SMUGGLE",
        }
        assert set(server.method_handlers.keys()) == expected

    def test_get_handler_callable(self, server):
        handler = server.method_handlers["GET"]
        req = _make_request("GET", "/")
        resp = handler(req)
        assert isinstance(resp, HTTPResponse)
        assert resp.status_code == 200

    def test_info_handler_for_root(self, server, temp_dir):
        handler = server.method_handlers["INFO"]
        req = _make_request("INFO", "/")
        resp = handler(req)
        assert resp.status_code == 200
        data = json.loads(resp.body)
        assert data["is_directory"] is True

    def test_unknown_method_not_in_handlers(self, server):
        assert server.method_handlers.get("CONNECT") is None

    def test_post_delegates_to_none(self, server):
        """POST should delegate to handle_none (upload)."""
        assert server.method_handlers["POST"] == server.handle_post
        req = _make_request("POST", "/", body=b"data", headers={"X-File-Name": "test.bin"})
        resp = server.handle_post(req)
        assert resp.status_code == 201

    def test_put_is_none(self, server):
        """PUT should be handle_none."""
        assert server.method_handlers["PUT"] == server.handle_none


class TestStaticResourceRouting:
    """Test bundled static asset routing."""

    def test_valid_static_asset_serves(self, server):
        req = _make_request("GET", "/static/ui/app.js")
        resp = server.handle_get(req)

        assert resp.status_code == 200
        assert resp.stream_path is not None
        assert resp.stream_path.name == "app.js"

    def test_inspector_static_asset_serves(self, server):
        req = _make_request("GET", "/static/ui/inspector.js")
        resp = server.handle_get(req)

        assert resp.status_code == 200
        assert resp.stream_path is not None
        assert resp.stream_path.name == "inspector.js"

    def test_index_local_script_references_resolve(self):
        missing = [
            resource_path
            for resource_path in _index_local_script_resource_paths()
            if get_package_resource(resource_path) is None
        ]

        assert missing == []

    def test_index_local_script_references_match_package_data(self):
        patterns = _src_package_data_patterns()
        missing = [
            f"data/{resource_path}"
            for resource_path in _index_local_script_resource_paths()
            if not any(
                fnmatch.fnmatchcase(f"data/{resource_path}", pattern)
                for pattern in patterns
            )
        ]

        assert missing == []

    def test_index_local_script_references_are_tracked(self):
        repo_root = Path(__file__).resolve().parents[1]
        if not (repo_root / ".git").exists():
            pytest.skip("Git tracking check requires a repository checkout")

        missing = []
        for resource_path in _index_local_script_resource_paths():
            source_path = Path("src/data") / resource_path
            result = subprocess.run(
                ["git", "ls-files", "--error-unmatch", "--", str(source_path)],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                missing.append(str(source_path))

        assert missing == []

    def test_static_raw_traversal_returns_not_found(self, server):
        req = _make_request("GET", "/static/../../server.py")
        resp = server.handle_get(req)

        assert resp.status_code == 404
        assert resp.stream_path is None

    def test_static_encoded_traversal_returns_not_found(self, server):
        req = _make_request("GET", "/static/%2e%2e/%2e%2e/server.py")
        resp = server.handle_get(req)

        assert resp.status_code == 404
        assert resp.stream_path is None


class TestAdvancedUploadRouting:
    """Test advanced upload payload detection."""

    def test_standard_get_still_works(self, server):
        req = _make_request("GET", "/")
        resp = server.handle_get(req)
        assert resp.status_code == 200

    def test_unknown_method_with_d_param_has_advanced_payload(self, server):
        import base64

        b64 = base64.urlsafe_b64encode(b"test").decode().rstrip("=")
        req = _make_request("RANDOMMETHOD", f"/?d={b64}")
        assert server._has_advanced_upload_payload(req) is True

    def test_unknown_method_no_data_has_no_advanced_payload(self, server):
        req = _make_request("RANDOMMETHOD", "/")
        assert server._has_advanced_upload_payload(req) is False


class TestSmuggleHandler:
    """Test SMUGGLE handler (creates temp HTML files)."""

    def test_smuggle_missing_file(self, server):
        req = _make_request("SMUGGLE", "/uploads/nonexistent.bin")
        resp = server.handle_smuggle(req)
        assert resp.status_code == 404

    def test_smuggle_creates_temp_html(self, server, upload_dir):
        (upload_dir / "secret.txt").write_bytes(b"secret data")
        req = _make_request("SMUGGLE", "/uploads/secret.txt")
        resp = server.handle_smuggle(req)
        assert resp.status_code == 200
        data = json.loads(resp.body)
        assert "url" in data
        assert data["url"].startswith("/uploads/smuggle_")
        assert data["file"] == "secret.txt"
        # Temp file should be registered
        assert len(server._temp_smuggle_files) == 1

    def test_smuggle_with_encryption(self, server, upload_dir):
        (upload_dir / "enc.bin").write_bytes(b"\x01\x02\x03")
        req = _make_request("SMUGGLE", "/uploads/enc.bin?encrypt=1")
        resp = server.handle_smuggle(req)
        assert resp.status_code == 200
        data = json.loads(resp.body)
        assert data["encrypted"] is True


class TestResponseHeaders:
    """Test response header correctness."""

    def test_cors_headers_disabled_by_default(self, server):
        req = _make_request("GET", "/")
        resp = server.handle_get(req)
        built = resp.build()
        assert b"Access-Control-Allow-Origin" not in built

    def test_cors_headers_when_enabled(self, server):
        req = _make_request("GET", "/")
        resp = server.handle_get(req)
        built = resp.build(cors_origin="https://app.example")
        assert b"Access-Control-Allow-Origin: https://app.example" in built

    def test_cors_exposes_file_headers(self, server):
        req = _make_request("GET", "/")
        resp = server.handle_get(req)
        built = resp.build(cors_origin="https://app.example")
        assert b"Server: ExperimentalHTTPServer/" in built
        assert b"Access-Control-Expose-Headers" in built

    def test_csp_on_html(self, server):
        req = _make_request("GET", "/")
        resp = server.handle_get(req)
        assert "Content-Security-Policy" in resp.headers
