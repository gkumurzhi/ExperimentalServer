"""Tests for extracted server methods: auth and handler dispatch."""

import base64
import gzip
import json
import ssl
import struct
import threading
from pathlib import Path

import pytest

from src.handlers import HandlerMixin
from src.http import HTTPRequest, HTTPResponse
from src.security.auth import AuthRateLimiter, BasicAuthenticator
from src.server import ExperimentalHTTPServer
from src.websocket import WS_CLOSE, WS_PING, WS_PONG, WS_TEXT, parse_ws_frame
from tests.conftest import make_request


class ServerStub(HandlerMixin):
    """Minimal server with auth and dispatch for unit testing."""

    def __init__(
        self,
        root_dir: Path,
        upload_dir: Path,
        *,
        auth: BasicAuthenticator | None = None,
        opsec: bool = False,
        advanced_upload: bool = False,
    ):
        self.root_dir = root_dir
        self.upload_dir = upload_dir
        self.notes_dir = root_dir / "notes"
        self.notes_dir.mkdir(exist_ok=True)
        self._temp_smuggle_files: set[str] = set()
        self._smuggle_lock = threading.Lock()
        self._notes_lock = threading.Lock()
        self._ecdh_manager = None
        self.advanced_upload_enabled = advanced_upload

        self.authenticator = auth
        self._rate_limiter = AuthRateLimiter() if auth else None

        self.method_handlers = self.build_method_handlers()

    def get_metrics(self):
        return {
            "uptime_seconds": 0,
            "total_requests": 0,
            "total_errors": 0,
            "bytes_sent": 0,
            "status_counts": {},
        }

    # Mirror of ExperimentalHTTPServer._authenticate_request
    def _authenticate_request(
        self,
        request: HTTPRequest,
        client_address: tuple[str, int],
    ) -> HTTPResponse | None:
        if not self.authenticator:
            return None
        ip = client_address[0]
        if self._rate_limiter and self._rate_limiter.is_blocked(ip):
            response = HTTPResponse(429)
            response.set_body(
                json.dumps({"error": "Too Many Requests", "status": 429}),
                "application/json",
            )
            return response
        auth_header = request.headers.get("authorization")
        if not self.authenticator.authenticate(auth_header):
            if self._rate_limiter:
                self._rate_limiter.record_failure(ip)
            response = HTTPResponse(401)
            response.set_header(
                "WWW-Authenticate",
                self.authenticator.get_www_authenticate_header(),
            )
            response.set_body(
                json.dumps({"error": "Unauthorized", "status": 401}),
                "application/json",
            )
            return response
        if self._rate_limiter:
            self._rate_limiter.reset(ip)
        return None


@pytest.fixture
def server(temp_dir, upload_dir):
    (temp_dir / "index.html").write_text("<html>ok</html>")
    return ServerStub(temp_dir, upload_dir)


@pytest.fixture
def auth_server(temp_dir, upload_dir):
    (temp_dir / "index.html").write_text("<html>ok</html>")
    auth = BasicAuthenticator({"admin": "secret123"})
    return ServerStub(temp_dir, upload_dir, auth=auth)


@pytest.fixture
def advanced_upload_server(temp_dir, upload_dir):
    (temp_dir / "index.html").write_text("<html>ok</html>")
    return ServerStub(temp_dir, upload_dir, advanced_upload=True)


ADDR = ("127.0.0.1", 12345)


# ── _authenticate_request tests ───────────────────────────────────


class TestAuthenticateRequest:
    def test_no_auth_configured_returns_none(self, server):
        req = make_request("GET", "/")
        assert server._authenticate_request(req, ADDR) is None

    def test_rate_limited_returns_429(self, auth_server):
        # Trigger rate limit by failing multiple times
        for _ in range(10):
            req = make_request("GET", "/")
            auth_server._authenticate_request(req, ADDR)

        req = make_request("GET", "/")
        result = auth_server._authenticate_request(req, ADDR)
        assert result is not None
        assert result.status_code == 429

    def test_successful_auth_resets_rate_limiter(self, auth_server):
        # Fail a few times
        for _ in range(3):
            req = make_request("GET", "/")
            auth_server._authenticate_request(req, ADDR)

        # Succeed
        creds = base64.b64encode(b"admin:secret123").decode()
        req = make_request("GET", "/", headers={"Authorization": f"Basic {creds}"})
        auth_server._authenticate_request(req, ADDR)

        # Should not be blocked
        assert not auth_server._rate_limiter.is_blocked(ADDR[0])

    def test_real_server_rate_limited_returns_429(self, temp_dir, monkeypatch):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True, auth="admin:secret123")
        assert server._rate_limiter is not None
        monkeypatch.setattr(server._rate_limiter, "is_blocked", lambda _ip: True)

        response = server._authenticate_request(make_request("GET", "/"), ADDR)

        assert response is not None
        assert response.status_code == 429
        assert json.loads(response.body) == {"error": "Too Many Requests", "status": 429}


# ── _dispatch_handler tests ───────────────────────────────────────


class TestDispatchHandler:
    def test_unknown_method_returns_405(self, server):
        req = make_request("CONNECT", "/")
        resp = server._dispatch_handler(req)
        assert resp.status_code == 405
        assert "Allow" in resp.headers

    def test_unknown_method_without_advanced_payload_returns_405(self, advanced_upload_server):
        req = make_request("CONNECT", "/")
        resp = advanced_upload_server._dispatch_handler(req)
        assert resp.status_code == 405

    def test_real_server_unknown_method_with_advanced_payload_is_rejected_by_default(
        self,
        temp_dir,
    ):
        import base64

        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)

        payload = base64.b64encode(b"advanced upload").decode("ascii")
        resp = server._dispatch_handler(
            make_request("CONNECT", "/", headers={"X-D": payload, "X-N": "advanced.txt"})
        )

        assert resp.status_code == 405
        assert not (server.upload_dir / "advanced.txt").exists()

    def test_real_server_unknown_method_with_advanced_payload_uploads_when_enabled(
        self,
        temp_dir,
    ):
        import base64

        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(
            root_dir=str(temp_dir),
            quiet=True,
            advanced_upload=True,
        )

        payload = base64.b64encode(b"advanced upload").decode("ascii")
        resp = server._dispatch_handler(
            make_request("CONNECT", "/", headers={"X-D": payload, "X-N": "advanced.txt"})
        )

        assert resp.status_code == 200
        assert json.loads(resp.body)["ok"] is True
        assert (server.upload_dir / "advanced.txt").read_bytes() == b"advanced upload"


class TestWebSocketOriginValidation:
    def test_missing_origin_allowed(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)
        req = make_request(
            "GET",
            "/notes/ws",
            headers={
                "Host": "127.0.0.1:8080",
                "Upgrade": "websocket",
                "Connection": "Upgrade",
                "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",
                "Sec-WebSocket-Version": "13",
            },
        )
        assert server._is_websocket_origin_allowed(req) is True

    def test_same_origin_allowed_by_default(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)
        req = make_request(
            "GET",
            "/notes/ws",
            headers={
                "Host": "127.0.0.1:8080",
                "Origin": "http://127.0.0.1:8080",
                "Upgrade": "websocket",
                "Connection": "Upgrade",
                "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",
                "Sec-WebSocket-Version": "13",
            },
        )
        assert server._is_websocket_origin_allowed(req) is True

    def test_cross_origin_rejected_by_default(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)
        req = make_request(
            "GET",
            "/notes/ws",
            headers={
                "Host": "127.0.0.1:8080",
                "Origin": "https://evil.example",
                "Upgrade": "websocket",
                "Connection": "Upgrade",
                "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",
                "Sec-WebSocket-Version": "13",
            },
        )
        assert server._is_websocket_origin_allowed(req) is False

    def test_configured_origin_allowlist(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(
            root_dir=str(temp_dir),
            quiet=True,
            cors_origin="https://app.example, https://admin.example",
        )
        req = make_request(
            "GET",
            "/notes/ws",
            headers={
                "Host": "127.0.0.1:8080",
                "Origin": "https://admin.example",
                "Upgrade": "websocket",
                "Connection": "Upgrade",
                "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",
                "Sec-WebSocket-Version": "13",
            },
        )
        assert server._is_websocket_origin_allowed(req) is True

    def test_wildcard_origin_allows_cross_origin_upgrade(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True, cors_origin="*")
        req = make_request(
            "GET",
            "/notes/ws",
            headers={
                "Host": "127.0.0.1:8080",
                "Origin": "https://evil.example",
                "Upgrade": "websocket",
                "Connection": "Upgrade",
                "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",
                "Sec-WebSocket-Version": "13",
            },
        )
        assert server._is_websocket_origin_allowed(req) is True

    def test_origin_with_missing_host_is_rejected(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)
        req = make_request(
            "GET",
            "/notes/ws",
            headers={
                "Origin": "http://127.0.0.1:8080",
                "Upgrade": "websocket",
                "Connection": "Upgrade",
                "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",
                "Sec-WebSocket-Version": "13",
            },
        )
        assert server._is_websocket_origin_allowed(req) is False


class TestCorsContract:
    def test_multi_origin_http_cors_reflects_only_matching_request_origin(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(
            root_dir=str(temp_dir),
            quiet=True,
            cors_origin="https://app.example, https://admin.example",
        )
        req = make_request("GET", "/", headers={"Origin": "https://admin.example"})
        response = HTTPResponse(200)
        response.set_body("OK", "text/plain")

        built = response.build(cors_origin=server._resolve_cors_origin(req))

        assert b"Access-Control-Allow-Origin: https://admin.example\r\n" in built
        invalid_acao = b"Access-Control-Allow-Origin: https://app.example, https://admin.example"
        assert invalid_acao not in built
        assert b"Vary: Origin\r\n" in built

    def test_multi_origin_http_cors_omits_unlisted_request_origin(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(
            root_dir=str(temp_dir),
            quiet=True,
            cors_origin="https://app.example, https://admin.example",
        )
        req = make_request("GET", "/", headers={"Origin": "https://evil.example"})
        response = HTTPResponse(200)
        response.set_body("OK", "text/plain")

        built = response.build(cors_origin=server._resolve_cors_origin(req))

        assert b"Access-Control-Allow-Origin:" not in built

    def test_http_cors_omits_header_without_request_origin(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(
            root_dir=str(temp_dir),
            quiet=True,
            cors_origin="https://app.example",
        )
        req = make_request("GET", "/")
        response = HTTPResponse(200)
        response.set_body("OK", "text/plain")

        built = response.build(cors_origin=server._resolve_cors_origin(req))

        assert b"Access-Control-Allow-Origin:" not in built

    def test_wildcard_http_cors_keeps_wildcard_origin(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True, cors_origin="*")
        req = make_request("GET", "/", headers={"Origin": "https://evil.example"})
        response = HTTPResponse(200)
        response.set_body("OK", "text/plain")

        built = response.build(cors_origin=server._resolve_cors_origin(req))

        assert b"Access-Control-Allow-Origin: *\r\n" in built
        assert b"Vary: Origin\r\n" not in built

    def test_mixed_wildcard_origin_config_is_rejected(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")

        with pytest.raises(ValueError, match="wildcard"):
            ExperimentalHTTPServer(
                root_dir=str(temp_dir),
                quiet=True,
                cors_origin="*, https://app.example",
            )

    def test_options_does_not_allow_unknown_method_without_advanced_upload(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(
            root_dir=str(temp_dir),
            quiet=True,
            cors_origin="https://app.example",
            advanced_upload=False,
        )
        req = make_request(
            "OPTIONS",
            "/",
            headers={"Access-Control-Request-Method": "XUPLOAD"},
        )

        response = server.handle_options(req)

        allowed = response.headers["Access-Control-Allow-Methods"]
        assert "XUPLOAD" not in allowed
        assert "SMUGGLE" in allowed

    def test_options_allows_unknown_method_when_advanced_upload_enabled(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(
            root_dir=str(temp_dir),
            quiet=True,
            cors_origin="https://app.example",
            advanced_upload=True,
        )
        req = make_request(
            "OPTIONS",
            "/",
            headers={
                "Access-Control-Request-Method": "XUPLOAD",
                "Access-Control-Request-Headers": "X-D-10, X-N, X-Unknown",
            },
        )

        response = server.handle_options(req)

        assert "XUPLOAD" in response.headers["Access-Control-Allow-Methods"]
        allowed_headers = response.headers["Access-Control-Allow-Headers"]
        assert "X-D-10" in allowed_headers
        assert "X-N" in allowed_headers
        assert "X-Unknown" not in allowed_headers

    def test_options_allows_auth_and_conditional_request_headers(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(
            root_dir=str(temp_dir),
            quiet=True,
            cors_origin="https://app.example",
        )
        req = make_request(
            "OPTIONS",
            "/",
            headers={
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization, If-None-Match, X-Unknown",
            },
        )

        response = server.handle_options(req)

        allowed_headers = response.headers["Access-Control-Allow-Headers"]
        assert "Authorization" in allowed_headers
        assert "If-None-Match" in allowed_headers
        assert "X-Unknown" not in allowed_headers


class _SendSocketStub:
    def __init__(self) -> None:
        self.sent: list[bytes] = []
        self.closed = False
        self.timeouts: list[float] = []

    def sendall(self, data: bytes) -> None:
        self.sent.append(data)

    def close(self) -> None:
        self.closed = True

    def settimeout(self, value: float) -> None:
        self.timeouts.append(value)


class _WebSocketSocketStub(_SendSocketStub):
    def __init__(self, recv_items: list[bytes | BaseException]) -> None:
        super().__init__()
        self._recv_items = list(recv_items)

    def recv(self, _size: int) -> bytes:
        if not self._recv_items:
            return b""
        item = self._recv_items.pop(0)
        if isinstance(item, BaseException):
            raise item
        return item


class _ListeningSocketStub:
    def __init__(self) -> None:
        self.options: list[tuple[int, int, int]] = []
        self.bound: tuple[str, int] | None = None
        self.backlog: int | None = None
        self.timeouts: list[float] = []
        self.closed = False

    def setsockopt(self, level: int, optname: int, value: int) -> None:
        self.options.append((level, optname, value))

    def bind(self, addr: tuple[str, int]) -> None:
        self.bound = addr

    def listen(self, backlog: int) -> None:
        self.backlog = backlog

    def settimeout(self, value: float) -> None:
        self.timeouts.append(value)

    def accept(self) -> tuple[object, tuple[str, int]]:
        raise KeyboardInterrupt

    def close(self) -> None:
        self.closed = True


class TestServerHelpers:
    @staticmethod
    def _make_masked_ws_frame(
        opcode: int,
        payload: bytes,
        *,
        fin: bool = True,
        rsv: int = 0,
    ) -> bytes:
        mask_key = b"\x37\x38\x39\x30"
        masked = bytearray(len(payload))
        for index, value in enumerate(payload):
            masked[index] = value ^ mask_key[index % 4]

        header = bytearray(((0x80 if fin else 0x00) | rsv | opcode,))
        length = len(payload)
        if length < 126:
            header.append(0x80 | length)
        elif length < 65536:
            header.extend((0x80 | 126,))
            header.extend(struct.pack("!H", length))
        else:
            header.extend((0x80 | 127,))
            header.extend(struct.pack("!Q", length))
        header.extend(mask_key)
        return bytes(header) + bytes(masked)

    @staticmethod
    def _ws_close_code(frame_bytes: bytes) -> int:
        frame = parse_ws_frame(frame_bytes)
        assert frame is not None
        assert frame[0] == WS_CLOSE
        return struct.unpack("!H", frame[1][:2])[0]

    def test_cleanup_old_smuggle_files_removes_stale_html(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)
        stale = server.upload_dir / "smuggle_old.html"
        keep = server.upload_dir / "notes.txt"
        stale.write_text("stale", encoding="utf-8")
        keep.write_text("keep", encoding="utf-8")

        server._cleanup_old_smuggle_files()

        assert not stale.exists()
        assert keep.exists()

    def test_server_leaves_upload_notes_as_regular_upload_content(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        upload_notes = temp_dir / "uploads" / "notes"
        upload_notes.mkdir(parents=True)
        (upload_notes / "abc.enc").write_bytes(b"ciphertext")
        (upload_notes / "abc.meta.json").write_text("{}", encoding="utf-8")

        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)

        assert not (server.notes_dir / "abc.enc").exists()
        assert (upload_notes / "abc.enc").read_bytes() == b"ciphertext"
        assert (upload_notes / "abc.meta.json").read_text(encoding="utf-8") == "{}"

    def test_server_does_not_generate_method_config_file(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)

        assert not (temp_dir / ".opsec_config.json").exists()

    def test_should_keep_alive_respects_http_version(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)

        http11 = make_request("GET", "/")
        http11_close = make_request("GET", "/", headers={"Connection": "close"})
        http10 = HTTPRequest(b"GET / HTTP/1.0\r\n\r\n")
        http10_keep = HTTPRequest(b"GET / HTTP/1.0\r\nConnection: keep-alive\r\n\r\n")

        assert server._should_keep_alive(http11) is True
        assert server._should_keep_alive(http11_close) is False
        assert server._should_keep_alive(http10) is False
        assert server._should_keep_alive(http10_keep) is True

    def test_resolve_keep_alive_disables_when_request_budget_is_exhausted(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)
        request = make_request("GET", "/")

        use_keep_alive, remaining = server._resolve_keep_alive(request, 1)
        assert use_keep_alive is True
        assert remaining == server.KEEP_ALIVE_MAX - 1

        use_keep_alive, remaining = server._resolve_keep_alive(request, server.KEEP_ALIVE_MAX)
        assert use_keep_alive is False
        assert remaining == 0

    def test_check_payload_size_handles_invalid_and_oversized_lengths(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(
            root_dir=str(temp_dir),
            quiet=True,
            max_upload_size=2 * 1024 * 1024,
        )

        invalid = make_request("POST", "/", headers={"Content-Length": "nope"})
        oversized = make_request("POST", "/", headers={"Content-Length": str(3 * 1024 * 1024)})

        assert server._check_payload_size(invalid) is None

        response = server._check_payload_size(oversized)
        assert response is not None
        assert response.status_code == 413
        assert "Max size: 2 MB" in json.loads(response.body)["error"]

    def test_smuggle_rejects_over_source_limit_without_temp_artifact(self, server, upload_dir):
        server.smuggle_source_size_limit = 4
        source_path = upload_dir / "large.bin"
        source_path.write_bytes(b"12345")

        response = server.handle_smuggle(make_request("SMUGGLE", "/uploads/large.bin"))

        assert response.status_code == 413
        body = json.loads(response.body)
        assert body["status"] == 413
        assert body["file_size"] == 5
        assert body["max_size"] == 4
        assert body["error"] == "SMUGGLE source too large. Max size: 4.0 B"
        assert "X-Smuggle-URL" not in response.headers
        assert server._temp_smuggle_files == set()
        assert list(upload_dir.glob("smuggle_*.html")) == []

    def test_smuggle_rejects_encrypted_over_source_limit_before_artifact(
        self,
        server,
        upload_dir,
    ):
        server.smuggle_source_size_limit = 4
        source_path = upload_dir / "large.bin"
        source_path.write_bytes(b"12345")

        response = server.handle_smuggle(make_request("SMUGGLE", "/uploads/large.bin?encrypt=1"))

        assert response.status_code == 413
        assert "X-Smuggle-URL" not in response.headers
        assert server._temp_smuggle_files == set()
        assert list(upload_dir.glob("smuggle_*.html")) == []

    def test_smuggle_source_limit_boundary(self, server, upload_dir):
        server.smuggle_source_size_limit = 4
        source_path = upload_dir / "edge.bin"
        source_path.write_bytes(b"1234")

        response = server.handle_smuggle(make_request("SMUGGLE", "/uploads/edge.bin"))

        assert response.status_code == 200

    def test_smuggle_small_file_generates_registered_temp_html(self, server, upload_dir):
        server.smuggle_source_size_limit = 64
        source_path = upload_dir / "small.txt"
        source_path.write_bytes(b"small payload")

        response = server.handle_smuggle(make_request("SMUGGLE", "/uploads/small.txt"))

        assert response.status_code == 200
        body = json.loads(response.body)
        assert body["url"].startswith("/uploads/smuggle_")
        assert body["file"] == "small.txt"
        assert body["encrypted"] is False

        temp_path = upload_dir / body["url"].removeprefix("/uploads/")
        assert temp_path.exists()
        assert str(temp_path) in server._temp_smuggle_files
        assert "small.txt" in temp_path.read_text(encoding="utf-8")

    def test_smuggle_temp_get_streams_and_cleans_up_without_full_read(
        self,
        temp_dir,
        monkeypatch,
    ):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)
        source_path = server.upload_dir / "small.txt"
        source_path.write_bytes(b"small payload")
        smuggle_response = server.handle_smuggle(make_request("SMUGGLE", "/uploads/small.txt"))
        smuggle_body = json.loads(smuggle_response.body)
        temp_path = server.upload_dir / smuggle_body["url"].removeprefix("/uploads/")

        def fail_read_bytes(_path):
            raise AssertionError("smuggle temp response must stream instead of full-read")

        monkeypatch.setattr(Path, "read_bytes", fail_read_bytes)

        get_response = server.handle_get(make_request("GET", smuggle_body["url"]))
        assert get_response.status_code == 200
        assert get_response.stream_path == temp_path
        assert get_response.body == b""

        sock = _SendSocketStub()
        server._send_response(
            get_response,
            sock,
            {
                "cors_origin": None,
                "keep_alive": True,
                "keep_alive_timeout": 15,
                "keep_alive_max": 3,
            },
        )

        assert len(sock.sent) >= 2
        assert not temp_path.exists()
        assert server._temp_smuggle_files == set()

    def test_smuggle_temp_head_cleans_up_one_shot_artifact(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)
        source_path = server.upload_dir / "small.txt"
        source_path.write_bytes(b"small payload")
        smuggle_response = server.handle_smuggle(make_request("SMUGGLE", "/uploads/small.txt"))
        smuggle_body = json.loads(smuggle_response.body)
        temp_path = server.upload_dir / smuggle_body["url"].removeprefix("/uploads/")

        head_response = server.handle_head(make_request("HEAD", smuggle_body["url"]))
        assert head_response.status_code == 200
        assert head_response.stream_path is None
        assert head_response.stream_cleanup is not None
        assert head_response.body == b""

        sock = _SendSocketStub()
        server._send_response(
            head_response,
            sock,
            {
                "cors_origin": None,
                "keep_alive": True,
                "keep_alive_timeout": 15,
                "keep_alive_max": 3,
            },
        )

        assert len(sock.sent) == 1
        assert b"HTTP/1.1 200 OK" in sock.sent[0]
        assert not temp_path.exists()
        assert server._temp_smuggle_files == set()
        assert head_response.stream_cleanup is None

    def test_smuggle_temp_conditional_get_cleans_up_one_shot_artifact(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)
        source_path = server.upload_dir / "small.txt"
        source_path.write_bytes(b"small payload")
        smuggle_response = server.handle_smuggle(make_request("SMUGGLE", "/uploads/small.txt"))
        smuggle_body = json.loads(smuggle_response.body)
        temp_path = server.upload_dir / smuggle_body["url"].removeprefix("/uploads/")
        etag = server._compute_etag(temp_path)

        response = server.handle_get(
            make_request("GET", smuggle_body["url"], headers={"If-None-Match": etag})
        )

        assert response.status_code == 304
        assert response.stream_cleanup is not None

        sock = _SendSocketStub()
        server._send_response(
            response,
            sock,
            {
                "cors_origin": None,
                "keep_alive": True,
                "keep_alive_timeout": 15,
                "keep_alive_max": 3,
            },
        )

        assert len(sock.sent) == 1
        assert b"HTTP/1.1 304 Not Modified" in sock.sent[0]
        assert not temp_path.exists()
        assert server._temp_smuggle_files == set()
        assert response.stream_cleanup is None

    def test_maybe_gzip_response_compresses_large_buffered_body(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)
        response = HTTPResponse(200)
        payload = ("x" * 2000).encode("utf-8")
        response.set_body(payload, "application/json")

        server._maybe_gzip_response(response)

        assert response.headers["Content-Encoding"] == "gzip"
        assert response.headers["Vary"] == "Accept-Encoding"
        assert gzip.decompress(response.body) == payload
        assert response.headers["Content-Length"] == str(len(response.body))

    def test_maybe_gzip_response_preserves_large_streamed_file_without_buffering(
        self,
        temp_dir,
        monkeypatch,
    ):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)
        payload = ("stream-data-" * 200).encode("utf-8")
        payload_path = temp_dir / "payload.txt"
        payload_path.write_bytes(payload)
        response = HTTPResponse(200)
        response.set_file(payload_path, "text/plain")

        def fail_read_bytes(_path):
            raise AssertionError("streaming gzip must not buffer files")

        monkeypatch.setattr(Path, "read_bytes", fail_read_bytes)

        server._maybe_gzip_response(response)

        assert response.stream_path == payload_path
        assert response.body == b""
        assert response.headers["Content-Length"] == str(len(payload))
        assert "Content-Encoding" not in response.headers

    def test_maybe_gzip_response_leaves_small_body_unchanged(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)
        response = HTTPResponse(200)
        response.set_body(b"small", "application/json")
        original_body = response.body

        server._maybe_gzip_response(response)

        assert response.body == original_body
        assert "Content-Encoding" not in response.headers

    def test_build_error_response_returns_json_error_payload(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)

        response = server._build_error_response(418, "teapot")

        assert response.status_code == 418
        assert json.loads(response.body) == {"error": "teapot", "status": 418}
        assert response.headers["Content-Type"] == "application/json"

    def test_is_websocket_upgrade_attempt_detects_handshake_headers(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)

        upgrade_request = make_request(
            "GET",
            "/notes/ws",
            headers={
                "Upgrade": "websocket",
                "Connection": "Upgrade",
                "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",
            },
        )
        plain_request = make_request("GET", "/")

        assert server._is_websocket_upgrade_attempt(upgrade_request) is True
        assert server._is_websocket_upgrade_attempt(plain_request) is False

    def test_post_process_response_adds_request_id_and_gzip_when_requested(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)
        request = make_request("GET", "/", headers={"Accept-Encoding": "br, gzip"})
        response = HTTPResponse(200)
        payload = ("compress-me-" * 300).encode("utf-8")
        response.set_body(payload, "application/json")

        server._post_process_response(request, response, "req-123")

        assert response.headers["X-Request-Id"] == "req-123"
        assert response.headers["Content-Encoding"] == "gzip"
        assert gzip.decompress(response.body) == payload

    def test_post_process_response_skips_gzip_when_ui_requests_identity_body(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)
        request = make_request(
            "GET",
            "/",
            headers={"Accept-Encoding": "br, gzip", "X-Exphttp-No-Gzip": "1"},
        )
        response = HTTPResponse(200)
        payload = ("compress-me-" * 300).encode("utf-8")
        response.set_body(payload, "application/json")

        server._post_process_response(request, response, "req-123")

        assert response.headers["X-Request-Id"] == "req-123"
        assert "Content-Encoding" not in response.headers
        assert response.body == payload

    def test_advanced_upload_payload_detection(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)

        assert server._has_advanced_upload_payload(make_request("STEALTH", "/")) is False
        assert server._has_advanced_upload_payload(make_request("STEALTH", "/?d=abc")) is True
        assert (
            server._has_advanced_upload_payload(
                make_request("STEALTH", "/", headers={"X-D": "abc"})
            )
            is True
        )

    def test_send_response_streams_file_with_close_connection(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        payload_path = temp_dir / "payload.txt"
        payload_path.write_text("stream payload", encoding="utf-8")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)
        response = HTTPResponse(200)
        response.set_file(payload_path, "text/plain")
        sock = _SendSocketStub()

        bytes_sent = server._send_response(
            response,
            sock,
            {
                "cors_origin": None,
                "keep_alive": True,
                "keep_alive_timeout": 15,
                "keep_alive_max": 3,
            },
        )

        assert len(sock.sent) == 2
        assert b"HTTP/1.1 200 OK" in sock.sent[0]
        assert b"Connection: close" in sock.sent[0]
        assert sock.sent[1] == b"stream payload"
        assert bytes_sent == len(sock.sent[0]) + len(sock.sent[1])

    def test_handle_client_closes_socket_when_tls_handshake_fails(self, temp_dir, monkeypatch):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True, tls=True)
        sock = _SendSocketStub()

        class _FailingSSLContext:
            def wrap_socket(self, _client_socket, server_side):
                assert server_side is True
                raise ssl.SSLError("bad handshake")

        server.running = True
        server._tls.enabled = True
        server._tls.ssl_context = _FailingSSLContext()  # type: ignore[assignment]

        def fail_receive(*_args, **_kwargs):
            raise AssertionError("_receive_request should not be called after handshake failure")

        monkeypatch.setattr(server, "_receive_request", fail_receive)

        server._handle_client(sock, ("127.0.0.1", 43210))

        assert sock.timeouts == [5.0]
        assert sock.closed is True

    def test_handle_client_processes_keep_alive_requests_until_handler_stops(
        self,
        temp_dir,
        monkeypatch,
    ):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)
        sock = _SendSocketStub()
        idle_timeouts: list[float | None] = []
        processed: list[tuple[bytes, int]] = []
        payloads = iter([b"first", b"second"])

        def fake_receive(_sock, idle_timeout=None):
            idle_timeouts.append(idle_timeout)
            return next(payloads, b"")

        def fake_process(data, _sock, _addr, request_num):
            processed.append((data, request_num))
            return request_num == 1

        monkeypatch.setattr(server, "_receive_request", fake_receive)
        monkeypatch.setattr(server, "_process_request", fake_process)
        server.running = True

        server._handle_client(sock, ("127.0.0.1", 43210))

        assert idle_timeouts == [None, server.KEEP_ALIVE_TIMEOUT]
        assert processed == [(b"first", 1), (b"second", 2)]
        assert sock.closed is True

    def test_handle_notepad_ws_sends_ping_on_timeout_then_closes(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)
        server.running = True
        sock = _WebSocketSocketStub([TimeoutError(), b""])
        request = make_request(
            "GET",
            "/notes/ws",
            headers={"Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ=="},
        )

        server._handle_notepad_ws(sock, request)

        assert b"HTTP/1.1 101 Switching Protocols" in sock.sent[0]
        ping_frame = parse_ws_frame(sock.sent[1])
        close_frame = parse_ws_frame(sock.sent[-1])
        assert ping_frame is not None
        assert ping_frame[0] == WS_PING
        assert close_frame is not None
        assert close_frame[0] == WS_CLOSE
        assert sock.timeouts == [60.0]

    def test_handle_notepad_ws_handles_ping_pong_and_text_frames(self, temp_dir, monkeypatch):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)
        handled_payloads: list[bytes] = []
        monkeypatch.setattr(
            server,
            "_handle_ws_message",
            lambda _sock, payload: handled_payloads.append(payload),
        )
        server.running = True
        sock = _WebSocketSocketStub(
            [
                self._make_masked_ws_frame(WS_PING, b"keepalive")
                + self._make_masked_ws_frame(WS_PONG, b"ack")
                + self._make_masked_ws_frame(WS_TEXT, b'{"type":"list"}'),
                b"",
            ]
        )
        request = make_request(
            "GET",
            "/notes/ws",
            headers={"Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ=="},
        )

        server._handle_notepad_ws(sock, request)

        assert handled_payloads == [b'{"type":"list"}']
        pong_frame = parse_ws_frame(sock.sent[1])
        close_frame = parse_ws_frame(sock.sent[-1])
        assert pong_frame is not None
        assert pong_frame[0] == WS_PONG
        assert pong_frame[1] == b"keepalive"
        assert close_frame is not None
        assert close_frame[0] == WS_CLOSE

    def test_handle_notepad_ws_rejects_malformed_frames_before_dispatch(
        self,
        temp_dir,
        monkeypatch,
    ):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        malformed_cases = [
            (
                "fragmented text",
                self._make_masked_ws_frame(WS_TEXT, b'{"type":"list"}', fin=False),
                1002,
            ),
            (
                "reserved bit",
                self._make_masked_ws_frame(WS_TEXT, b'{"type":"list"}', rsv=0x40),
                1002,
            ),
            ("unknown opcode", self._make_masked_ws_frame(0x03, b"payload"), 1002),
            ("oversized control", self._make_masked_ws_frame(WS_PING, b"x" * 126), 1002),
            ("invalid close payload", self._make_masked_ws_frame(WS_CLOSE, b"\x03"), 1002),
            (
                "invalid close reason",
                self._make_masked_ws_frame(WS_CLOSE, struct.pack("!H", 1000) + b"\xff"),
                1007,
            ),
        ]

        for case_name, frame, expected_close_code in malformed_cases:
            server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)
            handled_payloads: list[bytes] = []

            def record_payload(
                _sock: object,
                payload: bytes,
                sink: list[bytes] = handled_payloads,
            ) -> None:
                sink.append(payload)

            monkeypatch.setattr(
                server,
                "_handle_ws_message",
                record_payload,
            )
            server.running = True
            sock = _WebSocketSocketStub([frame])
            request = make_request(
                "GET",
                "/notes/ws",
                headers={"Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ=="},
            )

            server._handle_notepad_ws(sock, request)

            assert handled_payloads == [], case_name
            assert len(sock.sent) == 2, case_name
            assert self._ws_close_code(sock.sent[1]) == expected_close_code, case_name

    def test_handle_notepad_ws_rejects_oversized_frames(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)
        server.running = True
        oversized_header = struct.pack("!BBQ", 0x80 | WS_TEXT, 0x80 | 127, (10 * 1024 * 1024) + 1)
        sock = _WebSocketSocketStub([oversized_header])
        request = make_request(
            "GET",
            "/notes/ws",
            headers={"Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ=="},
        )

        server._handle_notepad_ws(sock, request)

        too_big_close = parse_ws_frame(sock.sent[1])
        assert too_big_close is not None
        assert too_big_close[0] == WS_CLOSE
        assert struct.unpack("!H", too_big_close[1][:2])[0] == 1009
        assert too_big_close[1][2:] == b"Message too big"
        assert len(sock.sent) == 2

    def test_start_opens_browser_and_cleans_up_resources(self, temp_dir, monkeypatch, capsys):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(
            root_dir=str(temp_dir),
            quiet=True,
            auth="admin:secret",
            open_browser=True,
            tls=True,
        )
        listening_socket = _ListeningSocketStub()
        opened_urls: list[str] = []
        shutdown_calls: list[tuple[bool, bool]] = []
        stale_temp = temp_dir / "stale-smuggle.html"
        stale_temp.write_text("temp", encoding="utf-8")
        server._temp_smuggle_files.add(str(stale_temp))
        server._tls.enabled = True
        server._tls._used_self_signed = True

        class _ExecutorStub:
            def __init__(self, max_workers: int) -> None:
                assert max_workers == server.max_workers

            def submit(self, *_args, **_kwargs) -> None:
                raise AssertionError("submit() should not run when accept() interrupts immediately")

            def shutdown(self, wait: bool, cancel_futures: bool) -> None:
                shutdown_calls.append((wait, cancel_futures))

        monkeypatch.setattr(server, "_setup_tls", lambda: None)
        monkeypatch.setattr(server, "_cleanup_temp_files", lambda: opened_urls.append("cleanup"))
        monkeypatch.setattr("src.server.socket.socket", lambda *_args, **_kwargs: listening_socket)
        monkeypatch.setattr("src.server.ThreadPoolExecutor", _ExecutorStub)
        monkeypatch.setattr("webbrowser.open", lambda url: opened_urls.append(url))

        server.start()

        output = capsys.readouterr().out
        assert "https://127.0.0.1:8080" in output
        assert "[TLS]     certificate: self-signed" in output
        assert "[AUTH]    Basic Auth enabled" in output
        assert "File access: uploads/ only" in output
        assert "Advanced upload: disabled" in output
        assert "Shutting down..." in output
        assert "Server stopped" in output
        assert listening_socket.bound == ("127.0.0.1", 8080)
        assert listening_socket.backlog == 128
        assert listening_socket.timeouts == [1.0]
        assert listening_socket.closed is True
        assert shutdown_calls == [(True, True)]
        assert opened_urls[0] == "https://127.0.0.1:8080"
        assert "cleanup" in opened_urls
        assert not stale_temp.exists()
        assert server._temp_smuggle_files == set()
