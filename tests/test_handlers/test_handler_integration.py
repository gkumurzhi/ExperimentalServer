"""Integration tests for handler mixins (B27).

Tests use a concrete handler class that composes all mixins,
exercising handlers in-process without network I/O.
"""

import json
import threading
from pathlib import Path

import pytest

from src.handlers import HandlerMixin
from tests.conftest import make_request


class StubServer(HandlerMixin):
    """Minimal concrete class combining all handler mixins for testing."""

    def __init__(self, root_dir: Path, upload_dir: Path, **kwargs):
        self.root_dir = root_dir
        self.upload_dir = upload_dir
        self.sandbox_mode = kwargs.get("sandbox", False)
        self.opsec_mode = kwargs.get("opsec", False)
        self.method_handlers = {
            "GET": self.handle_get,
            "POST": self.handle_post,
            "FETCH": self.handle_fetch,
            "INFO": self.handle_info,
            "PING": self.handle_ping,
            "NONE": self.handle_none,
            "OPTIONS": self.handle_options,
        }
        self._temp_smuggle_files: set[str] = set()
        self._smuggle_lock = threading.Lock()


@pytest.fixture
def server(temp_dir, upload_dir):
    # Create a minimal index.html so GET / works
    (temp_dir / "index.html").write_text("<html>hello</html>")
    return StubServer(temp_dir, upload_dir)


@pytest.fixture
def sandbox_server(temp_dir, upload_dir):
    (temp_dir / "index.html").write_text("<html>hello</html>")
    return StubServer(temp_dir, upload_dir, sandbox=True)


# ── GET tests ──────────────────────────────────────────────────────

class TestHandleGet:
    def test_get_index(self, server):
        req = make_request("GET", "/")
        resp = server.handle_get(req)
        assert resp.status_code == 200
        # index.html is text/html — may be full-read (OPSEC) or streamed
        content = resp.body or (resp.stream_path.read_bytes() if resp.stream_path else b"")
        assert b"hello" in content

    def test_get_existing_file(self, server, temp_dir):
        (temp_dir / "readme.txt").write_text("content here")
        req = make_request("GET", "/readme.txt")
        resp = server.handle_get(req)
        assert resp.status_code == 200
        # Non-HTML files are streamed
        assert resp.stream_path is not None
        assert resp.stream_path.read_bytes() == b"content here"

    def test_get_missing_file(self, server):
        req = make_request("GET", "/no_such_file.xyz")
        resp = server.handle_get(req)
        assert resp.status_code == 404

    def test_get_hidden_file(self, server, temp_dir):
        (temp_dir / ".env").write_text("SECRET=x")
        req = make_request("GET", "/.env")
        resp = server.handle_get(req)
        assert resp.status_code == 404

    def test_get_upload_in_sandbox(self, sandbox_server, upload_dir):
        (upload_dir / "data.bin").write_bytes(b"\xDE\xAD")
        req = make_request("GET", "/uploads/data.bin")
        resp = sandbox_server.handle_get(req)
        assert resp.status_code == 200
        assert resp.stream_path is not None
        assert resp.stream_path.read_bytes() == b"\xDE\xAD"

    def test_get_directory_serves_index(self, server, temp_dir):
        sub = temp_dir / "sub"
        sub.mkdir()
        (sub / "index.html").write_text("<p>sub</p>")
        req = make_request("GET", "/sub")
        resp = server.handle_get(req)
        assert resp.status_code == 200


# ── NONE (upload) tests ────────────────────────────────────────────

class TestHandleNone:
    def test_upload_file(self, server, upload_dir):
        body = b"file content 123"
        req = make_request(
            "NONE", "/",
            headers={"X-File-Name": "test.txt"},
            body=body,
        )
        resp = server.handle_none(req)
        assert resp.status_code == 201
        data = json.loads(resp.body)
        assert data["success"] is True
        assert data["size"] == len(body)
        # File should exist on disk
        uploaded = upload_dir / data["filename"]
        assert uploaded.exists()
        assert uploaded.read_bytes() == body

    def test_upload_empty_body(self, server):
        req = make_request("NONE", "/", headers={"X-File-Name": "empty.txt"})
        resp = server.handle_none(req)
        assert resp.status_code == 400

    def test_upload_generates_safe_filename(self, server, upload_dir):
        req = make_request(
            "NONE", "/",
            headers={"X-File-Name": "../../evil.sh"},
            body=b"pwned",
        )
        resp = server.handle_none(req)
        assert resp.status_code == 201
        data = json.loads(resp.body)
        # Filename should be sanitized — no path separators
        assert "/" not in data["filename"]
        assert ".." not in data["filename"]

    def test_upload_unique_name_on_collision(self, server, upload_dir):
        (upload_dir / "dup.txt").write_text("old")
        req = make_request(
            "NONE", "/",
            headers={"X-File-Name": "dup.txt"},
            body=b"new",
        )
        resp = server.handle_none(req)
        assert resp.status_code == 201
        data = json.loads(resp.body)
        assert data["filename"] != "dup.txt"  # should get _1 suffix


# ── POST tests (delegates to NONE) ────────────────────────────────

class TestHandlePost:
    def test_post_uploads_like_none(self, server, upload_dir):
        req = make_request(
            "POST", "/",
            headers={"X-File-Name": "post_file.bin"},
            body=b"post data",
        )
        resp = server.handle_post(req)
        assert resp.status_code == 201


# ── FETCH tests ────────────────────────────────────────────────────

class TestHandleFetch:
    def test_fetch_existing_file(self, server, upload_dir):
        (upload_dir / "dl.zip").write_bytes(b"PK\x03\x04")
        req = make_request("FETCH", "/uploads/dl.zip")
        resp = server.handle_fetch(req)
        assert resp.status_code == 200
        assert resp.stream_path is not None
        assert b"PK" in resp.stream_path.read_bytes()
        assert "content-disposition" in {k.lower() for k in resp.headers}

    def test_fetch_missing_file(self, server):
        req = make_request("FETCH", "/uploads/ghost.txt")
        resp = server.handle_fetch(req)
        assert resp.status_code == 404


# ── INFO tests ─────────────────────────────────────────────────────

class TestHandleInfo:
    def test_info_existing_file(self, server, temp_dir):
        (temp_dir / "info_target.txt").write_text("data")
        req = make_request("INFO", "/info_target.txt")
        resp = server.handle_info(req)
        assert resp.status_code == 200
        data = json.loads(resp.body)
        assert data["exists"] is True
        assert data["name"] == "info_target.txt"
        assert data["is_file"] is True

    def test_info_missing_file(self, server):
        req = make_request("INFO", "/nonexistent")
        resp = server.handle_info(req)
        assert resp.status_code == 404
        data = json.loads(resp.body)
        assert data["exists"] is False

    def test_info_directory_listing(self, server, temp_dir):
        sub = temp_dir / "mydir"
        sub.mkdir()
        (sub / "a.txt").write_text("a")
        (sub / "b.txt").write_text("b")
        req = make_request("INFO", "/mydir")
        resp = server.handle_info(req)
        assert resp.status_code == 200
        data = json.loads(resp.body)
        assert data["is_directory"] is True
        names = [c["name"] for c in data["contents"]]
        assert "a.txt" in names
        assert "b.txt" in names

    def test_info_sandbox_restricts_to_uploads(self, sandbox_server, upload_dir):
        (upload_dir / "s.txt").write_text("sandbox")
        req = make_request("INFO", "/uploads/s.txt")
        resp = sandbox_server.handle_info(req)
        assert resp.status_code == 200

    def test_info_traversal_blocked(self, server):
        req = make_request("INFO", "/../../etc/passwd")
        resp = server.handle_info(req)
        # Should get 400 (invalid path) from traversal block
        assert resp.status_code == 400

    def test_info_directory_pagination(self, server, temp_dir):
        sub = temp_dir / "pagedir"
        sub.mkdir()
        for i in range(5):
            (sub / f"file{i}.txt").write_text(str(i))
        req = make_request("INFO", "/pagedir?offset=2&limit=2")
        resp = server.handle_info(req)
        assert resp.status_code == 200
        data = json.loads(resp.body)
        assert data["total_items"] == 5
        assert len(data["contents"]) == 2
        assert data["offset"] == 2
        assert data["limit"] == 2


# ── PING tests ─────────────────────────────────────────────────────

class TestHandlePing:
    def test_ping_returns_pong(self, server):
        req = make_request("PING", "/")
        resp = server.handle_ping(req)
        assert resp.status_code == 200
        data = json.loads(resp.body)
        assert data["status"] == "pong"
        assert "server" in data
        assert "timestamp" in data

    def test_ping_opsec_hides_server(self, temp_dir, upload_dir):
        srv = StubServer(temp_dir, upload_dir, opsec=True)
        req = make_request("PING", "/")
        resp = srv.handle_ping(req)
        data = json.loads(resp.body)
        assert "server" not in data  # OPSEC hides server info


# ── OPTIONS tests ──────────────────────────────────────────────────

class TestHandleOptions:
    def test_options_returns_204(self, server):
        req = make_request(
            "OPTIONS", "/",
            headers={"Access-Control-Request-Method": "FETCH"},
        )
        resp = server.handle_options(req)
        assert resp.status_code == 204

    def test_options_opsec_hides_custom_methods(self, temp_dir, upload_dir):
        srv = StubServer(temp_dir, upload_dir, opsec=True)
        req = make_request(
            "OPTIONS", "/",
            headers={"Access-Control-Request-Method": "POST"},
        )
        resp = srv.handle_options(req)
        assert resp.status_code == 204
        allowed = resp.headers.get("Access-Control-Allow-Methods", "")
        assert "FETCH" not in allowed  # custom methods hidden in OPSEC


# ── OPSEC upload tests ─────────────────────────────────────────────

class TestHandleOpsecUpload:
    def test_opsec_json_upload(self, temp_dir, upload_dir):
        import base64
        srv = StubServer(temp_dir, upload_dir, opsec=True)
        payload = json.dumps({
            "n": "secret.bin",
            "d": base64.b64encode(b"secret data").decode(),
        }).encode()
        req = make_request("OPSEC", "/", body=payload)
        resp = srv.handle_opsec_upload(req)
        assert resp.status_code == 200
        data = json.loads(resp.body)
        assert data["ok"] is True

    def test_opsec_empty_body_returns_400(self, temp_dir, upload_dir):
        srv = StubServer(temp_dir, upload_dir, opsec=True)
        req = make_request("OPSEC", "/")
        resp = srv.handle_opsec_upload(req)
        assert resp.status_code == 400


# ── Auth rate limiter tests ────────────────────────────────────────

class TestAuthRateLimiter:
    def test_not_blocked_initially(self):
        from src.security.auth import AuthRateLimiter
        rl = AuthRateLimiter(max_attempts=3, cooldown=10.0)
        assert rl.is_blocked("1.2.3.4") is False

    def test_blocked_after_max_failures(self):
        from src.security.auth import AuthRateLimiter
        rl = AuthRateLimiter(max_attempts=3, cooldown=10.0)
        for _ in range(3):
            rl.record_failure("1.2.3.4")
        assert rl.is_blocked("1.2.3.4") is True

    def test_reset_unblocks(self):
        from src.security.auth import AuthRateLimiter
        rl = AuthRateLimiter(max_attempts=2, cooldown=10.0)
        rl.record_failure("1.2.3.4")
        rl.record_failure("1.2.3.4")
        assert rl.is_blocked("1.2.3.4") is True
        rl.reset("1.2.3.4")
        assert rl.is_blocked("1.2.3.4") is False

    def test_different_ips_independent(self):
        from src.security.auth import AuthRateLimiter
        rl = AuthRateLimiter(max_attempts=2, cooldown=10.0)
        rl.record_failure("1.1.1.1")
        rl.record_failure("1.1.1.1")
        assert rl.is_blocked("1.1.1.1") is True
        assert rl.is_blocked("2.2.2.2") is False
