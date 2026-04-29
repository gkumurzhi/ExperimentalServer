"""Integration tests for handler mixins (B27).

Tests use a concrete handler class that composes all mixins,
exercising handlers in-process without network I/O.
"""

import json
import threading
from pathlib import Path

import pytest

from src.handlers import HandlerMixin
from src.http import HTTPRequest
from tests.conftest import make_request


def _has_cryptography() -> bool:
    try:
        from src.security.crypto import HAS_CRYPTOGRAPHY

        return HAS_CRYPTOGRAPHY
    except ImportError:
        return False


class StubServer(HandlerMixin):
    """Minimal concrete class combining all handler mixins for testing."""

    def __init__(self, root_dir: Path, upload_dir: Path, **kwargs):
        self.root_dir = root_dir
        self.upload_dir = upload_dir
        self.notes_dir = root_dir / "notes"
        self.notes_dir.mkdir(exist_ok=True)
        self.cors_origin = kwargs.get("cors_origin")
        self.sandbox_mode = kwargs.get("sandbox", False)
        self.opsec_mode = kwargs.get("opsec", False)
        self.advanced_upload_enabled = kwargs.get("advanced_upload", False)
        self.method_handlers = self.build_method_handlers()
        self._temp_smuggle_files: set[str] = set()
        self._smuggle_lock = threading.Lock()
        self._notes_lock = threading.Lock()
        self._ecdh_manager = None

    def get_metrics(self):
        return {
            "uptime_seconds": 42.0,
            "total_requests": 10,
            "total_errors": 1,
            "bytes_sent": 5000,
            "status_counts": {200: 9, 500: 1},
        }


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
        # The bundled web UI is served outside uploads so the browser can load.
        content = resp.body or (resp.stream_path.read_bytes() if resp.stream_path else b"")
        assert b"Experimental HTTP Server" in content

    def test_get_existing_file(self, server, upload_dir):
        (upload_dir / "readme.txt").write_text("content here")
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

    def test_get_hidden_upload_file(self, server, upload_dir):
        (upload_dir / ".secret").write_text("SECRET=x")
        req = make_request("GET", "/uploads/.secret")
        resp = server.handle_get(req)
        assert resp.status_code == 404

    def test_get_uploaded_html_forces_download(self, server, upload_dir):
        (upload_dir / "evil.html").write_text("<script>alert(1)</script>")
        req = make_request("GET", "/uploads/evil.html")
        resp = server.handle_get(req)

        assert resp.status_code == 200
        assert resp.headers["Content-Type"] == "application/octet-stream"
        assert resp.headers["Content-Disposition"] == 'attachment; filename="evil.html"'
        assert "Content-Security-Policy" not in resp.headers

    def test_get_upload_in_sandbox(self, sandbox_server, upload_dir):
        (upload_dir / "data.bin").write_bytes(b"\xde\xad")
        req = make_request("GET", "/uploads/data.bin")
        resp = sandbox_server.handle_get(req)
        assert resp.status_code == 200
        assert resp.stream_path is not None
        assert resp.stream_path.read_bytes() == b"\xde\xad"

    def test_get_directory_serves_index(self, server, upload_dir):
        sub = upload_dir / "sub"
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
            "NONE",
            "/",
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
            "NONE",
            "/",
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
            "NONE",
            "/",
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
            "POST",
            "/",
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
    def test_info_existing_file(self, server, upload_dir):
        (upload_dir / "info_target.txt").write_text("data")
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

    def test_info_directory_listing(self, server, upload_dir):
        sub = upload_dir / "mydir"
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

    def test_info_hidden_file_returns_404(self, server, temp_dir):
        (temp_dir / ".env").write_text("SECRET=x")
        req = make_request("INFO", "/.env")
        resp = server.handle_info(req)
        assert resp.status_code == 404

    def test_info_traversal_blocked(self, server):
        req = make_request("INFO", "/../../etc/passwd")
        resp = server.handle_info(req)
        # Should get 400 (invalid path) from traversal block
        assert resp.status_code == 400

    def test_info_directory_pagination(self, server, upload_dir):
        sub = upload_dir / "pagedir"
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

    def test_ping_reports_uploads_only_and_advanced_upload(self, temp_dir, upload_dir):
        srv = StubServer(temp_dir, upload_dir)
        req = make_request("PING", "/")
        resp = srv.handle_ping(req)
        data = json.loads(resp.body)
        assert data["access_scope"] == "uploads"
        assert data["advanced_upload"] is False


# ── OPTIONS tests ──────────────────────────────────────────────────


class TestHandleOptions:
    def test_options_returns_204(self, server):
        req = make_request(
            "OPTIONS",
            "/",
            headers={"Access-Control-Request-Method": "FETCH"},
        )
        resp = server.handle_options(req)
        assert resp.status_code == 204
        assert "Access-Control-Allow-Methods" not in resp.headers

    def test_options_with_explicit_cors_origin_includes_custom_methods(self, temp_dir, upload_dir):
        srv = StubServer(temp_dir, upload_dir, cors_origin="https://app.example")
        req = make_request(
            "OPTIONS",
            "/",
            headers={"Access-Control-Request-Method": "POST"},
        )
        resp = srv.handle_options(req)
        assert resp.status_code == 204
        allowed = resp.headers.get("Access-Control-Allow-Methods", "")
        assert "FETCH" in allowed

    def test_options_with_explicit_cors_origin_sets_allow_methods(self, temp_dir, upload_dir):
        srv = StubServer(temp_dir, upload_dir, cors_origin="https://app.example")
        req = make_request(
            "OPTIONS",
            "/",
            headers={"Access-Control-Request-Method": "NOTE"},
        )
        resp = srv.handle_options(req)
        assert resp.status_code == 204
        allowed = resp.headers.get("Access-Control-Allow-Methods", "")
        assert "NOTE" in allowed


# ── OPSEC upload tests ─────────────────────────────────────────────


class TestHandleOpsecUpload:
    def test_malformed_request_cannot_use_advanced_upload_fallback(self, temp_dir, upload_dir):
        import base64

        srv = StubServer(temp_dir, upload_dir, advanced_upload=True)
        payload = base64.b64encode(b"blocked malformed upload").decode()
        req = HTTPRequest(
            (
                "XUPLOAD\r\n"
                f"X-D: {payload}\r\n"
                "X-N: malformed.txt\r\n"
                "\r\n"
            ).encode("ascii")
        )

        resp = srv._dispatch_handler(req)

        assert resp.status_code == 400
        assert not (upload_dir / "malformed.txt").exists()
        assert list(upload_dir.iterdir()) == []

    def test_invalid_request_target_cannot_use_advanced_upload_fallback(self, temp_dir, upload_dir):
        import base64

        srv = StubServer(temp_dir, upload_dir, advanced_upload=True)
        payload = base64.b64encode(b"blocked target upload").decode()
        req = HTTPRequest(
            (
                "XUPLOAD /\t HTTP/1.1\r\n"
                f"X-D: {payload}\r\n"
                "X-N: target.txt\r\n"
                "\r\n"
            ).encode("ascii")
        )

        resp = srv._dispatch_handler(req)

        assert resp.status_code == 400
        assert not (upload_dir / "target.txt").exists()
        assert list(upload_dir.iterdir()) == []

    def test_valid_unknown_method_still_uses_advanced_upload_fallback(self, temp_dir, upload_dir):
        import base64

        srv = StubServer(temp_dir, upload_dir, advanced_upload=True)
        payload = base64.b64encode(b"valid fallback upload").decode()
        req = make_request("XUPLOAD", "/", headers={"X-D": payload, "X-N": "fallback.txt"})

        resp = srv._dispatch_handler(req)

        assert resp.status_code == 200
        assert (upload_dir / "fallback.txt").read_bytes() == b"valid fallback upload"

    def test_opsec_json_upload(self, temp_dir, upload_dir):
        import base64

        srv = StubServer(temp_dir, upload_dir, opsec=True)
        payload = json.dumps(
            {
                "n": "secret.bin",
                "d": base64.b64encode(b"secret data").decode(),
            }
        ).encode()
        req = make_request("OPSEC", "/", body=payload)
        resp = srv.handle_advanced_upload(req)
        assert resp.status_code == 200
        data = json.loads(resp.body)
        assert data["ok"] is True

    def test_opsec_empty_body_returns_400(self, temp_dir, upload_dir):
        srv = StubServer(temp_dir, upload_dir, opsec=True)
        req = make_request("OPSEC", "/")
        resp = srv.handle_advanced_upload(req)
        assert resp.status_code == 400

    def test_opsec_json_array_returns_400_without_writing(self, temp_dir, upload_dir):
        srv = StubServer(temp_dir, upload_dir, opsec=True)
        req = make_request("OPSEC", "/", body=b"[]")
        resp = srv.handle_advanced_upload(req)
        assert resp.status_code == 400
        assert list(upload_dir.iterdir()) == []

    def test_opsec_json_object_missing_data_returns_400_without_writing(self, temp_dir, upload_dir):
        srv = StubServer(temp_dir, upload_dir, opsec=True)
        payload = json.dumps({"n": "missing.bin"}).encode()
        req = make_request("OPSEC", "/", body=payload)
        resp = srv.handle_advanced_upload(req)
        assert resp.status_code == 400
        assert list(upload_dir.iterdir()) == []

    def test_opsec_invalid_base64_returns_400_without_writing(self, temp_dir, upload_dir):
        srv = StubServer(temp_dir, upload_dir, opsec=True)
        req = make_request("XUPLOAD", "/", headers={"X-D": "not!!!base64"})
        resp = srv.handle_advanced_upload(req)
        assert resp.status_code == 400
        assert list(upload_dir.iterdir()) == []

    def test_opsec_invalid_url_base64_returns_400_without_writing(self, temp_dir, upload_dir):
        srv = StubServer(temp_dir, upload_dir, opsec=True)
        req = make_request("XUPLOAD", "/?d=not!!!base64")
        resp = srv.handle_advanced_upload(req)
        assert resp.status_code == 400
        assert list(upload_dir.iterdir()) == []

    def test_opsec_invalid_kb64_returns_400_without_writing(self, temp_dir, upload_dir):
        import base64

        srv = StubServer(temp_dir, upload_dir, opsec=True)
        raw = base64.b64encode(b"ciphertext").decode()
        req = make_request(
            "XUPLOAD",
            "/",
            headers={
                "X-D": raw,
                "X-E": "xor",
                "X-K": "%%%invalid%%%",
                "X-Kb64": "true",
            },
        )
        resp = srv.handle_advanced_upload(req)
        assert resp.status_code == 400
        assert list(upload_dir.iterdir()) == []

    def test_opsec_headers_transport(self, temp_dir, upload_dir):
        """X-D header with no body → 200, file saved correctly."""
        import base64

        srv = StubServer(temp_dir, upload_dir, opsec=True)
        raw_data = b"headers transport data"
        b64 = base64.b64encode(raw_data).decode()
        req = make_request("XUPLOAD", "/", headers={"X-D": b64})
        resp = srv.handle_advanced_upload(req)
        assert resp.status_code == 200
        result = json.loads(resp.body)
        assert result["ok"] is True
        assert result["transport"] == "headers"
        # Verify file content on disk
        saved = list(upload_dir.iterdir())
        assert len(saved) >= 1
        assert any(f.read_bytes() == raw_data for f in saved)

    def test_opsec_url_transport(self, temp_dir, upload_dir):
        """?d=<url-safe-b64> with no body → 200, file saved correctly."""
        import base64

        srv = StubServer(temp_dir, upload_dir, opsec=True)
        raw_data = b"url transport data"
        # URL-safe base64
        b64 = base64.urlsafe_b64encode(raw_data).decode().rstrip("=")
        req = make_request("XUPLOAD", f"/?d={b64}")
        resp = srv.handle_advanced_upload(req)
        assert resp.status_code == 200
        result = json.loads(resp.body)
        assert result["ok"] is True
        assert result["transport"] == "url"
        saved = list(upload_dir.iterdir())
        assert any(f.read_bytes() == raw_data for f in saved)

    def test_opsec_headers_xor_decrypt(self, temp_dir, upload_dir):
        """X-D + X-E: xor + X-K → decrypted content on disk."""
        import base64

        from src.security.crypto import xor_bytes

        srv = StubServer(temp_dir, upload_dir, opsec=True)
        original = b"secret plaintext"
        key = "mykey"
        encrypted = xor_bytes(original, key)
        b64 = base64.b64encode(encrypted).decode()
        req = make_request(
            "XUPLOAD",
            "/",
            headers={
                "X-D": b64,
                "X-E": "xor",
                "X-K": key,
            },
        )
        resp = srv.handle_advanced_upload(req)
        assert resp.status_code == 200
        saved = list(upload_dir.iterdir())
        assert any(f.read_bytes() == original for f in saved)

    def test_opsec_url_xor_decrypt(self, temp_dir, upload_dir):
        """?d=...&e=xor&k=... → decrypted content on disk."""
        import base64

        from src.security.crypto import xor_bytes

        srv = StubServer(temp_dir, upload_dir, opsec=True)
        original = b"url secret"
        key = "urlkey"
        encrypted = xor_bytes(original, key)
        b64 = base64.urlsafe_b64encode(encrypted).decode().rstrip("=")
        req = make_request("XUPLOAD", f"/?d={b64}&e=xor&k={key}")
        resp = srv.handle_advanced_upload(req)
        assert resp.status_code == 200
        saved = list(upload_dir.iterdir())
        assert any(f.read_bytes() == original for f in saved)

    def test_opsec_headers_hmac_valid(self, temp_dir, upload_dir):
        """X-H with correct HMAC → 200."""
        import base64

        from src.security.crypto import compute_hmac

        srv = StubServer(temp_dir, upload_dir, opsec=True)
        raw_data = b"hmac data"
        key = "hmackey"
        b64 = base64.b64encode(raw_data).decode()
        hmac_val = compute_hmac(raw_data, key)
        req = make_request(
            "XUPLOAD",
            "/",
            headers={
                "X-D": b64,
                "X-E": "xor",
                "X-K": key,
                "X-H": hmac_val,
            },
        )
        resp = srv.handle_advanced_upload(req)
        assert resp.status_code == 200
        assert json.loads(resp.body)["ok"] is True

    def test_opsec_headers_hmac_invalid(self, temp_dir, upload_dir):
        """X-H with wrong HMAC → 400, err=hmac."""
        import base64

        srv = StubServer(temp_dir, upload_dir, opsec=True)
        raw_data = b"hmac data"
        b64 = base64.b64encode(raw_data).decode()
        req = make_request(
            "XUPLOAD",
            "/",
            headers={
                "X-D": b64,
                "X-E": "xor",
                "X-K": "somekey",
                "X-H": "deadbeef",
            },
        )
        resp = srv.handle_advanced_upload(req)
        assert resp.status_code == 400
        assert json.loads(resp.body)["err"] == "hmac"

    def test_opsec_body_priority_over_headers(self, temp_dir, upload_dir):
        """JSON body + X-D header → body wins, transport=body."""
        import base64

        srv = StubServer(temp_dir, upload_dir, opsec=True)
        body_data = b"body wins"
        header_data = b"header loses"
        payload = json.dumps(
            {
                "d": base64.b64encode(body_data).decode(),
            }
        ).encode()
        req = make_request(
            "XUPLOAD",
            "/",
            headers={
                "X-D": base64.b64encode(header_data).decode(),
            },
            body=payload,
        )
        resp = srv.handle_advanced_upload(req)
        assert resp.status_code == 200
        result = json.loads(resp.body)
        assert result["transport"] == "body"
        saved = list(upload_dir.iterdir())
        assert any(f.read_bytes() == body_data for f in saved)

    def test_opsec_headers_priority_over_url(self, temp_dir, upload_dir):
        """X-D header + ?d= param → headers win, transport=headers."""
        import base64

        srv = StubServer(temp_dir, upload_dir, opsec=True)
        header_data = b"header wins"
        url_data = b"url loses"
        h_b64 = base64.b64encode(header_data).decode()
        u_b64 = base64.urlsafe_b64encode(url_data).decode().rstrip("=")
        req = make_request(
            "XUPLOAD",
            f"/?d={u_b64}",
            headers={
                "X-D": h_b64,
            },
        )
        resp = srv.handle_advanced_upload(req)
        assert resp.status_code == 200
        result = json.loads(resp.body)
        assert result["transport"] == "headers"
        saved = list(upload_dir.iterdir())
        assert any(f.read_bytes() == header_data for f in saved)

    def test_opsec_empty_all_returns_400(self, temp_dir, upload_dir):
        """No body, no X-D, no ?d= → 400."""
        srv = StubServer(temp_dir, upload_dir, opsec=True)
        req = make_request("XUPLOAD", "/")
        resp = srv.handle_advanced_upload(req)
        assert resp.status_code == 400

    def test_opsec_transport_in_response(self, temp_dir, upload_dir):
        """Verify transport field in response for each mode."""
        import base64

        srv = StubServer(temp_dir, upload_dir, opsec=True)
        raw = b"transport test"
        b64_std = base64.b64encode(raw).decode()
        b64_url = base64.urlsafe_b64encode(raw).decode().rstrip("=")

        # Body
        body_payload = json.dumps({"d": b64_std}).encode()
        resp = srv.handle_advanced_upload(make_request("X", "/", body=body_payload))
        assert json.loads(resp.body)["transport"] == "body"

        # Headers
        resp = srv.handle_advanced_upload(make_request("X", "/", headers={"X-D": b64_std}))
        assert json.loads(resp.body)["transport"] == "headers"

        # URL
        resp = srv.handle_advanced_upload(make_request("X", f"/?d={b64_url}"))
        assert json.loads(resp.body)["transport"] == "url"

    def test_urlsafe_b64decode(self, temp_dir, upload_dir):
        """URL-safe base64 (-, _, no padding) decodes correctly."""
        import base64

        srv = StubServer(temp_dir, upload_dir, opsec=True)
        # Data that produces + and / in standard base64
        raw = bytes(range(256))
        url_b64 = base64.urlsafe_b64encode(raw).decode().rstrip("=")
        decoded = srv._urlsafe_b64decode(url_b64)
        assert decoded == raw

    def test_opsec_headers_with_filename(self, temp_dir, upload_dir):
        """X-N header → file saved with that name."""
        import base64

        srv = StubServer(temp_dir, upload_dir, opsec=True)
        raw = b"named file"
        b64 = base64.b64encode(raw).decode()
        req = make_request(
            "XUPLOAD",
            "/",
            headers={
                "X-D": b64,
                "X-N": "custom_name.txt",
            },
        )
        resp = srv.handle_advanced_upload(req)
        assert resp.status_code == 200
        assert (upload_dir / "custom_name.txt").exists()
        assert (upload_dir / "custom_name.txt").read_bytes() == raw

    def test_opsec_kb64_header(self, temp_dir, upload_dir):
        """X-Kb64: true → key decoded from base64."""
        import base64

        from src.security.crypto import xor_bytes

        srv = StubServer(temp_dir, upload_dir, opsec=True)
        original = b"kb64 test"
        key = "mypassword"
        encrypted = xor_bytes(original, key)
        b64_data = base64.b64encode(encrypted).decode()
        b64_key = base64.b64encode(key.encode()).decode()
        req = make_request(
            "XUPLOAD",
            "/",
            headers={
                "X-D": b64_data,
                "X-E": "xor",
                "X-K": b64_key,
                "X-Kb64": "true",
            },
        )
        resp = srv.handle_advanced_upload(req)
        assert resp.status_code == 200
        saved = list(upload_dir.iterdir())
        assert any(f.read_bytes() == original for f in saved)

    def test_opsec_chunked_headers(self, temp_dir, upload_dir):
        """X-D-0 + X-D-1 + X-D-2 → reassembled correctly."""
        import base64

        srv = StubServer(temp_dir, upload_dir, opsec=True)
        raw = b"chunked header data that spans multiple headers"
        b64 = base64.b64encode(raw).decode()
        # Split into 3 chunks
        chunk_size = len(b64) // 3 + 1
        chunks = {}
        for i in range(0, len(b64), chunk_size):
            chunks[f"X-D-{i // chunk_size}"] = b64[i : i + chunk_size]
        req = make_request("XUPLOAD", "/", headers=chunks)
        resp = srv.handle_advanced_upload(req)
        assert resp.status_code == 200
        result = json.loads(resp.body)
        assert result["ok"] is True
        assert result["transport"] == "headers"
        saved = list(upload_dir.iterdir())
        assert any(f.read_bytes() == raw for f in saved)

    def test_opsec_chunked_single_chunk(self, temp_dir, upload_dir):
        """Only X-D-0 → works."""
        import base64

        srv = StubServer(temp_dir, upload_dir, opsec=True)
        raw = b"single chunk"
        b64 = base64.b64encode(raw).decode()
        req = make_request("XUPLOAD", "/", headers={"X-D-0": b64})
        resp = srv.handle_advanced_upload(req)
        assert resp.status_code == 200
        result = json.loads(resp.body)
        assert result["ok"] is True
        assert result["transport"] == "headers"
        saved = list(upload_dir.iterdir())
        assert any(f.read_bytes() == raw for f in saved)


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


# ── HEAD tests ────────────────────────────────────────────────────


class TestHandleHead:
    def test_head_200(self, server):
        req = make_request("HEAD", "/")
        resp = server.handle_head(req)
        assert resp.status_code == 200
        assert resp.body == b""
        assert resp.stream_path is None

    def test_head_empty_body(self, server, upload_dir):
        (upload_dir / "data.txt").write_text("some data")
        req = make_request("HEAD", "/data.txt")
        resp = server.handle_head(req)
        assert resp.status_code == 200
        assert resp.body == b""
        assert resp.stream_path is None

    def test_head_content_length_matches_get(self, server, upload_dir):
        content = "hello world content"
        (upload_dir / "match.txt").write_text(content)
        get_req = make_request("GET", "/match.txt")
        get_resp = server.handle_get(get_req)
        head_req = make_request("HEAD", "/match.txt")
        head_resp = server.handle_head(head_req)
        assert head_resp.headers.get("Content-Length") == get_resp.headers.get("Content-Length")

    def test_head_404_for_missing(self, server):
        req = make_request("HEAD", "/nonexistent.xyz")
        resp = server.handle_head(req)
        assert resp.status_code == 404


# ── DELETE tests ──────────────────────────────────────────────────


class TestHandleDelete:
    def test_delete_existing_file(self, server, upload_dir):
        (upload_dir / "to_delete.txt").write_text("bye")
        req = make_request("DELETE", "/uploads/to_delete.txt")
        resp = server.handle_delete(req)
        assert resp.status_code == 200
        data = json.loads(resp.body)
        assert data["success"] is True
        assert data["deleted"] == "to_delete.txt"
        assert not (upload_dir / "to_delete.txt").exists()

    def test_delete_missing_file(self, server):
        req = make_request("DELETE", "/uploads/ghost.txt")
        resp = server.handle_delete(req)
        assert resp.status_code == 404

    def test_delete_outside_uploads(self, server, temp_dir):
        (temp_dir / "root_file.txt").write_text("root")
        req = make_request("DELETE", "/root_file.txt")
        resp = server.handle_delete(req)
        # sandbox restriction: file resolves inside upload_dir or 404
        assert resp.status_code in (403, 404)

    def test_delete_directory_rejected(self, server, upload_dir):
        sub = upload_dir / "subdir"
        sub.mkdir()
        req = make_request("DELETE", "/uploads/subdir")
        resp = server.handle_delete(req)
        assert resp.status_code == 400

    def test_delete_uploads_root_requires_clear_flag(self, server, upload_dir):
        (upload_dir / "keep.txt").write_text("keep")
        req = make_request("DELETE", "/uploads")
        resp = server.handle_delete(req)
        assert resp.status_code == 400
        assert (upload_dir / "keep.txt").exists()

    def test_delete_uploads_clear_removes_visible_contents(self, server, upload_dir):
        (upload_dir / ".gitkeep").write_text("")
        (upload_dir / "file.txt").write_text("data")
        subdir = upload_dir / "nested"
        subdir.mkdir()
        (subdir / "child.txt").write_text("child")
        notes_dir = upload_dir / "notes"
        notes_dir.mkdir()
        (notes_dir / "regular-upload.txt").write_text("remove")

        req = make_request("DELETE", "/uploads?clear=1")
        resp = server.handle_delete(req)

        assert resp.status_code == 200
        data = json.loads(resp.body)
        assert data["success"] is True
        assert data["cleared"] is True
        assert data["deleted_files"] == 1
        assert data["deleted_dirs"] == 2
        assert data["preserved"] == [".gitkeep"]
        assert (upload_dir / ".gitkeep").exists()
        assert not notes_dir.exists()
        assert not (upload_dir / "file.txt").exists()
        assert not subdir.exists()

    def test_delete_path_traversal_blocked(self, server):
        req = make_request("DELETE", "/uploads/../../etc/passwd")
        resp = server.handle_delete(req)
        assert resp.status_code in (403, 404)


# ── Cache headers tests ──────────────────────────────────────────


class TestCacheHeaders:
    def test_get_returns_etag_and_last_modified(self, server, upload_dir):
        (upload_dir / "cached.txt").write_text("cache me")
        req = make_request("GET", "/cached.txt")
        resp = server.handle_get(req)
        assert resp.status_code == 200
        assert "ETag" in resp.headers
        assert "Last-Modified" in resp.headers
        assert "Cache-Control" in resp.headers

    def test_conditional_304_with_if_none_match(self, server, upload_dir):
        (upload_dir / "etag_test.txt").write_text("etag content")
        # First request to get ETag
        req1 = make_request("GET", "/etag_test.txt")
        resp1 = server.handle_get(req1)
        etag = resp1.headers["ETag"]
        # Second request with If-None-Match
        req2 = make_request("GET", "/etag_test.txt", headers={"If-None-Match": etag})
        resp2 = server.handle_get(req2)
        assert resp2.status_code == 304
        assert resp2.body == b""

    def test_head_has_cache_headers(self, server, upload_dir):
        (upload_dir / "head_cache.txt").write_text("head cache")
        req = make_request("HEAD", "/head_cache.txt")
        resp = server.handle_head(req)
        assert resp.status_code == 200
        assert "ETag" in resp.headers
        assert "Last-Modified" in resp.headers


# ── Metrics tests ─────────────────────────────────────────────────


class TestMetrics:
    def test_get_metrics_returns_json(self, server):
        req = make_request("GET", "/metrics")
        resp = server.handle_get(req)
        assert resp.status_code == 200
        data = json.loads(resp.body)
        assert "uptime_seconds" in data
        assert "total_requests" in data
        assert "total_errors" in data
        assert "bytes_sent" in data
        assert "status_counts" in data

    def test_metrics_available(self, temp_dir, upload_dir):
        srv = StubServer(temp_dir, upload_dir)
        req = make_request("GET", "/metrics")
        resp = srv.handle_get(req)
        assert resp.status_code == 200


# ── OPSEC AES decryption path tests ──────────────────────────────


class TestOpsecAESDecryption:
    """Test OPSEC upload with AES-256-GCM encrypted payload."""

    @pytest.mark.skipif(
        not _has_cryptography(),
        reason="cryptography package not installed",
    )
    def test_opsec_headers_aes_decrypt(self, temp_dir, upload_dir):
        """X-D + X-E: aes + X-K → AES-decrypted content on disk."""
        import base64

        from src.security.crypto import aes_encrypt

        srv = StubServer(temp_dir, upload_dir, opsec=True)
        original = b"aes encrypted secret"
        key = "strongpassword"
        encrypted = aes_encrypt(original, key)
        b64 = base64.b64encode(encrypted).decode()
        req = make_request(
            "XUPLOAD",
            "/",
            headers={
                "X-D": b64,
                "X-E": "aes",
                "X-K": key,
            },
        )
        resp = srv.handle_advanced_upload(req)
        assert resp.status_code == 200
        saved = list(upload_dir.iterdir())
        assert any(f.read_bytes() == original for f in saved)

    @pytest.mark.skipif(
        not _has_cryptography(),
        reason="cryptography package not installed",
    )
    def test_opsec_url_aes_decrypt(self, temp_dir, upload_dir):
        """?d=...&e=aes&k=... → AES-decrypted content on disk."""
        import base64

        from src.security.crypto import aes_encrypt

        srv = StubServer(temp_dir, upload_dir, opsec=True)
        original = b"url aes secret"
        key = "urlkey"
        encrypted = aes_encrypt(original, key)
        b64 = base64.urlsafe_b64encode(encrypted).decode().rstrip("=")
        req = make_request("XUPLOAD", f"/?d={b64}&e=aes&k={key}")
        resp = srv.handle_advanced_upload(req)
        assert resp.status_code == 200
        saved = list(upload_dir.iterdir())
        assert any(f.read_bytes() == original for f in saved)

    @pytest.mark.skipif(
        not _has_cryptography(),
        reason="cryptography package not installed",
    )
    def test_opsec_aes_wrong_key_returns_400_without_writing(self, temp_dir, upload_dir):
        """AES with wrong key fails closed without writing ciphertext."""
        import base64

        from src.security.crypto import aes_encrypt

        srv = StubServer(temp_dir, upload_dir, opsec=True)
        original = b"aes wrong key test"
        encrypted = aes_encrypt(original, "correct_key")
        b64 = base64.b64encode(encrypted).decode()
        req = make_request(
            "XUPLOAD",
            "/",
            headers={
                "X-D": b64,
                "X-E": "aes",
                "X-K": "wrong_key",
            },
        )
        resp = srv.handle_advanced_upload(req)
        assert resp.status_code == 400
        assert list(upload_dir.iterdir()) == []

    @pytest.mark.skipif(
        not _has_cryptography(),
        reason="cryptography package not installed",
    )
    def test_opsec_aes_tampered_headers_return_400_without_writing(self, temp_dir, upload_dir):
        """Tampered AES-GCM header payload fails closed without writing ciphertext."""
        import base64

        from src.security.crypto import aes_encrypt

        srv = StubServer(temp_dir, upload_dir, opsec=True)
        encrypted = bytearray(aes_encrypt(b"tamper me", "correct_key"))
        encrypted[-1] ^= 0x01
        b64 = base64.b64encode(bytes(encrypted)).decode()
        req = make_request(
            "XUPLOAD",
            "/",
            headers={
                "X-D": b64,
                "X-E": "aes",
                "X-K": "correct_key",
            },
        )
        resp = srv.handle_advanced_upload(req)
        assert resp.status_code == 400
        assert list(upload_dir.iterdir()) == []

    @pytest.mark.skipif(
        not _has_cryptography(),
        reason="cryptography package not installed",
    )
    def test_opsec_aes_tampered_url_returns_400_without_writing(self, temp_dir, upload_dir):
        """Tampered AES-GCM URL payload fails closed without writing ciphertext."""
        import base64

        from src.security.crypto import aes_encrypt

        srv = StubServer(temp_dir, upload_dir, opsec=True)
        encrypted = bytearray(aes_encrypt(b"url tamper me", "correct_key"))
        encrypted[-1] ^= 0x01
        b64 = base64.urlsafe_b64encode(bytes(encrypted)).decode().rstrip("=")
        req = make_request("XUPLOAD", f"/?d={b64}&e=aes&k=correct_key")
        resp = srv.handle_advanced_upload(req)
        assert resp.status_code == 400
        assert list(upload_dir.iterdir()) == []

    def test_opsec_aes_without_crypto_returns_400_without_writing(
        self,
        temp_dir,
        upload_dir,
        monkeypatch,
    ):
        """Requested AES fails clearly when cryptography support is unavailable."""
        import base64

        import src.security.crypto as crypto

        monkeypatch.setattr(crypto, "HAS_CRYPTOGRAPHY", False)
        srv = StubServer(temp_dir, upload_dir, opsec=True)
        aes_like_payload = bytes([1]) + b"x" * 44
        b64 = base64.b64encode(aes_like_payload).decode()
        req = make_request(
            "XUPLOAD",
            "/",
            headers={
                "X-D": b64,
                "X-E": "aes",
                "X-K": "correct_key",
            },
        )
        resp = srv.handle_advanced_upload(req)
        assert resp.status_code == 400
        assert json.loads(resp.body)["error"] == "AES decryption unavailable"
        assert list(upload_dir.iterdir()) == []

    @pytest.mark.skipif(
        not _has_cryptography(),
        reason="cryptography package not installed",
    )
    def test_opsec_aes_with_hmac(self, temp_dir, upload_dir):
        """AES + HMAC verification → decrypted content on disk."""
        import base64

        from src.security.crypto import aes_encrypt, compute_hmac

        srv = StubServer(temp_dir, upload_dir, opsec=True)
        original = b"aes hmac verified"
        key = "hmacaeskey"
        encrypted = aes_encrypt(original, key)
        b64 = base64.b64encode(encrypted).decode()
        hmac_val = compute_hmac(encrypted, key)
        req = make_request(
            "XUPLOAD",
            "/",
            headers={
                "X-D": b64,
                "X-E": "aes",
                "X-K": key,
                "X-H": hmac_val,
            },
        )
        resp = srv.handle_advanced_upload(req)
        assert resp.status_code == 200
        assert json.loads(resp.body)["ok"] is True
        saved = list(upload_dir.iterdir())
        assert any(f.read_bytes() == original for f in saved)
