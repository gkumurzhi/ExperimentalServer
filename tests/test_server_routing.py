"""Tests for server method routing and OPSEC routing (B44)."""

import json
import threading
from pathlib import Path

import pytest

from src.handlers import HandlerMixin
from src.http import HTTPRequest, HTTPResponse


class StubServer(HandlerMixin):
    """Minimal server stub for routing tests."""

    def __init__(self, root_dir: Path, upload_dir: Path, opsec: bool = False):
        self.root_dir = root_dir
        self.upload_dir = upload_dir
        self.sandbox_mode = False
        self.opsec_mode = opsec
        self._temp_smuggle_files: set[str] = set()
        self._smuggle_lock = threading.Lock()
        self.method_handlers = {
            "GET": self.handle_get,
            "POST": self.handle_post,
            "PUT": self.handle_none,
            "OPTIONS": self.handle_options,
            "FETCH": self.handle_fetch,
            "INFO": self.handle_info,
            "PING": self.handle_ping,
            "NONE": self.handle_none,
            "SMUGGLE": self.handle_smuggle,
        }
        self.opsec_methods = {
            "upload": "XUPLOAD",
            "download": "XDOWNLOAD",
            "info": "XINFO",
            "ping": "XPING",
        }


def _make_request(method: str, path: str = "/", body: bytes = b"",
                  headers: dict[str, str] | None = None) -> HTTPRequest:
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


@pytest.fixture
def opsec_server(temp_dir, upload_dir):
    return StubServer(temp_dir, upload_dir, opsec=True)


class TestMethodRouting:
    """Test that standard method_handlers dispatch is correct."""

    def test_all_standard_methods_registered(self, server):
        expected = {"GET", "POST", "PUT", "OPTIONS", "FETCH", "INFO", "PING", "NONE", "SMUGGLE"}
        assert set(server.method_handlers.keys()) == expected

    def test_get_handler_callable(self, server):
        handler = server.method_handlers["GET"]
        req = _make_request("GET", "/")
        resp = handler(req)
        assert isinstance(resp, HTTPResponse)
        assert resp.status_code == 200

    def test_ping_handler_returns_pong(self, server):
        handler = server.method_handlers["PING"]
        req = _make_request("PING", "/")
        resp = handler(req)
        data = json.loads(resp.body)
        assert data["status"] == "pong"

    def test_info_handler_for_root(self, server, temp_dir):
        handler = server.method_handlers["INFO"]
        req = _make_request("INFO", "/")
        resp = handler(req)
        assert resp.status_code == 200
        data = json.loads(resp.body)
        assert data["is_directory"] is True

    def test_unknown_method_not_in_handlers(self, server):
        assert server.method_handlers.get("DELETE") is None

    def test_post_delegates_to_none(self, server):
        """POST should delegate to handle_none (upload)."""
        assert server.method_handlers["POST"] == server.handle_post
        req = _make_request("POST", "/", body=b"data",
                            headers={"X-File-Name": "test.bin"})
        resp = server.handle_post(req)
        assert resp.status_code == 201

    def test_put_is_none(self, server):
        """PUT should be handle_none."""
        assert server.method_handlers["PUT"] == server.handle_none


class TestOpsecMethods:
    """Test OPSEC method name mapping."""

    def test_opsec_methods_set(self, opsec_server):
        assert opsec_server.opsec_methods["upload"] == "XUPLOAD"
        assert opsec_server.opsec_methods["download"] == "XDOWNLOAD"
        assert opsec_server.opsec_methods["info"] == "XINFO"
        assert opsec_server.opsec_methods["ping"] == "XPING"

    def test_standard_get_still_works_in_opsec(self, opsec_server):
        req = _make_request("GET", "/")
        resp = opsec_server.handle_get(req)
        assert resp.status_code == 200

    def test_ping_hides_server_in_opsec(self, opsec_server):
        req = _make_request("PING", "/")
        resp = opsec_server.handle_ping(req)
        data = json.loads(resp.body)
        assert "server" not in data
        assert data["status"] == "pong"


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

    def test_cors_headers_in_response(self, server):
        req = _make_request("GET", "/")
        resp = server.handle_get(req)
        built = resp.build()
        assert b"Access-Control-Allow-Origin: *" in built

    def test_opsec_hides_cors_expose(self, opsec_server):
        req = _make_request("GET", "/")
        resp = opsec_server.handle_get(req)
        built = resp.build(opsec_mode=True)
        assert b"Server: nginx" in built
        assert b"Access-Control-Expose-Headers" not in built

    def test_csp_on_html(self, server):
        req = _make_request("GET", "/")
        resp = server.handle_get(req)
        assert "Content-Security-Policy" in resp.headers
