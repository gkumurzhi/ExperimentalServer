"""Tests for server method routing and advanced upload routing (B44)."""

import json
import threading
from pathlib import Path

import pytest

from src.handlers import HandlerMixin
from src.http import HTTPRequest, HTTPResponse


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
        self.method_handlers = {
            "GET": self.handle_get,
            "HEAD": self.handle_head,
            "POST": self.handle_post,
            "PUT": self.handle_none,
            "DELETE": self.handle_delete,
            "OPTIONS": self.handle_options,
            "FETCH": self.handle_fetch,
            "INFO": self.handle_info,
            "PING": self.handle_ping,
            "NOTE": self.handle_note,
            "NONE": self.handle_none,
            "SMUGGLE": self.handle_smuggle,
        }

    def get_metrics(self):
        return {
            "uptime_seconds": 0,
            "total_requests": 0,
            "total_errors": 0,
            "bytes_sent": 0,
            "status_counts": {},
        }

    @staticmethod
    def _has_advanced_upload_payload(request: HTTPRequest) -> bool:
        return bool(
            request.body
            or request.headers.get("x-d")
            or request.headers.get("x-d-0")
            or request.query_params.get("d")
        )


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
