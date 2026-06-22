"""Tests for extracted server methods: auth and handler dispatch."""

import base64
import gzip
import json
import logging
import os
import ssl
import struct
import threading
from pathlib import Path

import pytest

from src.features import resolve_feature_profile
from src.handlers import HandlerMixin
from src.handlers.smuggle import SmuggleTempPolicy
from src.http import HTTPRequest, HTTPResponse
from src.http.io import RequestReceiveResult
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
    ):
        self.root_dir = root_dir
        self.upload_dir = upload_dir
        self.notes_dir = root_dir / "notes"
        self.notes_dir.mkdir(exist_ok=True)
        self._temp_smuggle_files: set[str] = set()
        self._smuggle_lock = threading.Lock()
        self._notes_lock = threading.Lock()
        self._ecdh_manager = None
        self.features = resolve_feature_profile("lab")
        self.advanced_upload_enabled = True

        self.authenticator = auth
        self._rate_limiter = AuthRateLimiter() if auth else None

        self.method_handlers = self.build_method_handlers()

    def get_metrics(self):
        return {
            "uptime_seconds": 0,
            "total_requests": 0,
            "total_errors": 0,
            "client_errors": 0,
            "server_errors": 0,
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
    return ServerStub(temp_dir, upload_dir)


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

    def test_real_server_unknown_method_with_advanced_payload_uploads_with_lab_profile(
        self,
        temp_dir,
    ):
        import base64

        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(
            root_dir=str(temp_dir),
            quiet=True,
            profile="lab",
        )

        payload = base64.b64encode(b"advanced upload").decode("ascii")
        resp = server._dispatch_handler(
            make_request("CONNECT", "/", headers={"X-D": payload, "X-N": "advanced.txt"})
        )

        assert resp.status_code == 200
        assert json.loads(resp.body)["ok"] is True
        assert (server.upload_dir / "advanced.txt").read_bytes() == b"advanced upload"


class TestFeatureProfiles:
    def test_default_profile_uses_workspace_policy(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)

        ping_data = json.loads(server._dispatch_handler(make_request("PING", "/")).body)

        assert server.profile == "workspace"
        assert ping_data["profile"] == "workspace"
        assert ping_data["advanced_upload"] is False
        assert ping_data["capabilities"] == resolve_feature_profile("workspace").capabilities()

    @pytest.mark.parametrize("profile", ["serve", "workspace", "lab"])
    def test_profile_policy_flows_through_public_surfaces(self, temp_dir, profile):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(
            root_dir=str(temp_dir),
            quiet=True,
            cors_origin="https://app.example",
            profile=profile,
        )
        features = server.features

        ping_data = json.loads(server._dispatch_handler(make_request("PING", "/")).body)
        assert ping_data["profile"] == features.profile
        assert ping_data["capabilities"] == features.capabilities()
        assert ping_data["supported_methods"] == list(features.registry_methods())
        assert list(server.method_handlers.keys()) == list(features.registry_methods())

        options = server.handle_options(
            make_request(
                "OPTIONS",
                "/",
                headers={"Access-Control-Request-Method": "XUPLOAD"},
            )
        )
        expected_cors_methods = list(features.cors_methods())
        if (
            features.allows_unknown_cors_method("XUPLOAD")
            and "XUPLOAD" not in expected_cors_methods
        ):
            expected_cors_methods.append("XUPLOAD")
        assert server._cors_allow_methods_header().split(", ") == list(features.cors_methods())
        assert options.headers["Access-Control-Allow-Methods"].split(", ") == expected_cors_methods

        mutation_headers = {
            "Host": "127.0.0.1:8080",
            "Origin": "https://evil.example",
        }
        upload_request = make_request(
            "POST",
            "/policy-upload.txt",
            headers=mutation_headers,
            body=b"x",
        )
        upload_guarded = features.requires_browser_mutation_guard(
            "POST",
            method_registered="POST" in server.method_handlers,
            has_advanced_upload_payload=False,
        )
        assert server._is_browser_protected_mutation(upload_request) is upload_guarded
        assert server._is_browser_mutation_allowed(upload_request) is (not upload_guarded)

        advanced_request = make_request(
            "XUPLOAD",
            "/",
            headers={**mutation_headers, "X-D": base64.b64encode(b"x").decode("ascii")},
        )
        advanced_guarded = features.requires_browser_mutation_guard(
            "XUPLOAD",
            method_registered=False,
            has_advanced_upload_payload=True,
        )
        assert server._is_browser_protected_mutation(advanced_request) is advanced_guarded
        assert server._is_browser_mutation_allowed(advanced_request) is (not advanced_guarded)

        websocket_request = make_request(
            "GET",
            "/notes/ws",
            headers={
                "Upgrade": "websocket",
                "Connection": "Upgrade",
                "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",
                "Sec-WebSocket-Version": "13",
            },
        )
        assert server._is_websocket_upgrade_attempt(websocket_request) is (
            features.websocket_route_enabled("/notes/ws")
        )

    def test_serve_profile_exposes_read_only_capabilities(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(
            root_dir=str(temp_dir),
            quiet=True,
            cors_origin="https://app.example",
            profile="serve",
        )

        assert list(server.method_handlers.keys()) == [
            "GET",
            "HEAD",
            "OPTIONS",
            "FETCH",
            "INFO",
            "PING",
        ]

        ping = server._dispatch_handler(make_request("PING", "/"))
        ping_data = json.loads(ping.body)
        assert ping_data["profile"] == "serve"
        assert ping_data["advanced_upload"] is False
        assert ping_data["capabilities"] == {
            "ordinary_upload": False,
            "file_delete": False,
            "clear_uploads": False,
            "advanced_upload": False,
            "smuggle": False,
            "note_http": False,
            "note_delete": False,
            "note_clear": False,
            "websocket_notes": False,
        }

        upload = server._dispatch_handler(make_request("POST", "/blocked.txt", body=b"x"))
        advanced = server._dispatch_handler(
            make_request("XUPLOAD", "/", headers={"X-D": base64.b64encode(b"x").decode()})
        )
        note = server._dispatch_handler(make_request("NOTE", "/notes/key"))
        smuggle = server._dispatch_handler(make_request("SMUGGLE", "/uploads/file.txt"))
        clear = server._dispatch_handler(make_request("DELETE", "/uploads?clear=1"))
        assert [upload.status_code, advanced.status_code, note.status_code] == [405, 405, 405]
        assert [smuggle.status_code, clear.status_code] == [405, 405]
        assert not (server.upload_dir / "blocked.txt").exists()

        options = server.handle_options(
            make_request(
                "OPTIONS",
                "/",
                headers={"Access-Control-Request-Method": "XUPLOAD"},
            )
        )
        allowed = options.headers["Access-Control-Allow-Methods"]
        assert "GET" in allowed
        assert "POST" not in allowed
        assert "NOTE" not in allowed
        assert "SMUGGLE" not in allowed
        assert "XUPLOAD" not in allowed
        assert (
            server._is_websocket_upgrade_attempt(
                make_request(
                    "GET",
                    "/notes/ws",
                    headers={
                        "Upgrade": "websocket",
                        "Connection": "Upgrade",
                        "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",
                        "Sec-WebSocket-Version": "13",
                    },
                )
            )
            is False
        )

    def test_workspace_profile_allows_upload_delete_but_not_lab_features(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(
            root_dir=str(temp_dir),
            quiet=True,
            cors_origin="https://app.example",
            profile="workspace",
        )

        assert list(server.method_handlers.keys()) == [
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
            "NONE",
        ]

        upload = server._dispatch_handler(make_request("POST", "/workspace.txt", body=b"x"))
        assert upload.status_code == 201
        assert (server.upload_dir / "workspace.txt").read_bytes() == b"x"

        delete = server._dispatch_handler(make_request("DELETE", "/uploads/workspace.txt"))
        assert delete.status_code == 200
        assert not (server.upload_dir / "workspace.txt").exists()

        (server.upload_dir / "keep.txt").write_text("keep", encoding="utf-8")
        clear = server._dispatch_handler(make_request("DELETE", "/uploads?clear=1"))
        assert clear.status_code == 403
        assert (server.upload_dir / "keep.txt").exists()

        advanced = server._dispatch_handler(
            make_request("XUPLOAD", "/", headers={"X-D": base64.b64encode(b"x").decode()})
        )
        note = server._dispatch_handler(make_request("NOTE", "/notes/key"))
        smuggle = server._dispatch_handler(make_request("SMUGGLE", "/uploads/keep.txt"))
        assert [advanced.status_code, note.status_code, smuggle.status_code] == [405, 405, 405]

        ping_data = json.loads(server._dispatch_handler(make_request("PING", "/")).body)
        assert ping_data["profile"] == "workspace"
        assert ping_data["capabilities"]["ordinary_upload"] is True
        assert ping_data["capabilities"]["file_delete"] is True
        assert ping_data["capabilities"]["clear_uploads"] is False
        assert ping_data["capabilities"]["advanced_upload"] is False
        assert ping_data["capabilities"]["note_http"] is False
        assert ping_data["capabilities"]["websocket_notes"] is False
        assert (
            server._is_websocket_upgrade_attempt(
                make_request(
                    "GET",
                    "/notes/ws",
                    headers={
                        "Upgrade": "websocket",
                        "Connection": "Upgrade",
                        "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",
                        "Sec-WebSocket-Version": "13",
                    },
                )
            )
            is False
        )

        options = server.handle_options(
            make_request(
                "OPTIONS",
                "/",
                headers={"Access-Control-Request-Method": "XUPLOAD"},
            )
        )
        allowed = options.headers["Access-Control-Allow-Methods"]
        assert "POST" in allowed
        assert "DELETE" in allowed
        assert "NOTE" not in allowed
        assert "SMUGGLE" not in allowed
        assert "XUPLOAD" not in allowed

    def test_lab_profile_preserves_experimental_surface(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(
            root_dir=str(temp_dir),
            quiet=True,
            cors_origin="https://app.example",
            profile="lab",
        )

        assert "NOTE" in server.method_handlers
        assert "SMUGGLE" in server.method_handlers
        assert server.features.advanced_upload is True
        assert (
            server._is_websocket_upgrade_attempt(
                make_request(
                    "GET",
                    "/notes/ws",
                    headers={
                        "Upgrade": "websocket",
                        "Connection": "Upgrade",
                        "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",
                        "Sec-WebSocket-Version": "13",
                    },
                )
            )
            is True
        )

        options = server.handle_options(
            make_request(
                "OPTIONS",
                "/",
                headers={"Access-Control-Request-Method": "XUPLOAD"},
            )
        )
        allowed = options.headers["Access-Control-Allow-Methods"]
        assert "NOTE" in allowed
        assert "SMUGGLE" in allowed
        assert "XUPLOAD" in allowed

    def test_lab_profile_preserves_clear_operations(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(
            root_dir=str(temp_dir),
            quiet=True,
            profile="lab",
        )
        upload_file = server.upload_dir / "clear-me.txt"
        upload_file.write_text("clear", encoding="utf-8")
        note_file = server.notes_dir / "clear-me.enc"
        note_file.write_bytes(b"opaque note")

        upload_clear = server._dispatch_handler(make_request("DELETE", "/uploads?clear=1"))
        note_clear = server._dispatch_handler(make_request("NOTE", "/notes?clear=1"))

        assert upload_clear.status_code == 200
        upload_data = json.loads(upload_clear.body)
        assert upload_data["success"] is True
        assert upload_data["cleared"] is True
        assert not upload_file.exists()

        assert note_clear.status_code == 200
        note_data = json.loads(note_clear.body)
        assert note_data["success"] is True
        assert note_data["cleared"] is True
        assert not note_file.exists()


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

    def test_wildcard_origin_rejects_cross_origin_upgrade(self, temp_dir):
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
        assert server._is_websocket_origin_allowed(req) is False

    def test_literal_wildcard_origin_rejects_websocket_upgrade(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True, cors_origin="*")
        req = make_request(
            "GET",
            "/notes/ws",
            headers={
                "Host": "127.0.0.1:8080",
                "Origin": "*",
                "Upgrade": "websocket",
                "Connection": "Upgrade",
                "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",
                "Sec-WebSocket-Version": "13",
            },
        )
        assert server._is_websocket_origin_allowed(req) is False

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

        built = response.build(
            cors_origin=server._resolve_cors_origin(req),
            cors_allow_methods=server._cors_allow_methods_header(),
        )

        assert b"Access-Control-Allow-Origin: *\r\n" in built
        assert b"Vary: Origin\r\n" not in built
        methods_header = next(
            line
            for line in built.split(b"\r\n")
            if line.startswith(b"Access-Control-Allow-Methods:")
        )
        assert b"GET" in methods_header
        assert b"FETCH" in methods_header
        assert b"POST" not in methods_header
        assert b"DELETE" not in methods_header
        assert b"SMUGGLE" not in methods_header

    def test_mixed_wildcard_origin_config_is_rejected(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")

        with pytest.raises(ValueError, match="wildcard"):
            ExperimentalHTTPServer(
                root_dir=str(temp_dir),
                quiet=True,
                cors_origin="*, https://app.example",
            )

    def test_options_rejects_unknown_advanced_method_by_default(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(
            root_dir=str(temp_dir),
            quiet=True,
            cors_origin="https://app.example",
        )
        req = make_request(
            "OPTIONS",
            "/",
            headers={"Access-Control-Request-Method": "XUPLOAD"},
        )

        response = server.handle_options(req)

        allowed = response.headers["Access-Control-Allow-Methods"]
        assert "POST" in allowed
        assert "DELETE" in allowed
        assert "XUPLOAD" not in allowed
        assert "SMUGGLE" not in allowed

    def test_options_allows_unknown_method_with_lab_profile(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(
            root_dir=str(temp_dir),
            quiet=True,
            cors_origin="https://app.example",
            profile="lab",
        )
        req = make_request(
            "OPTIONS",
            "/",
            headers={"Access-Control-Request-Method": "XUPLOAD"},
        )

        response = server.handle_options(req)

        allowed = response.headers["Access-Control-Allow-Methods"]
        assert "XUPLOAD" in allowed
        assert "SMUGGLE" in allowed

    def test_wildcard_options_advertises_only_read_methods(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(
            root_dir=str(temp_dir),
            quiet=True,
            cors_origin="*",
        )
        req = make_request(
            "OPTIONS",
            "/",
            headers={"Access-Control-Request-Method": "XUPLOAD"},
        )

        response = server.handle_options(req)

        allowed = response.headers["Access-Control-Allow-Methods"]
        assert "GET" in allowed
        assert "FETCH" in allowed
        assert "POST" not in allowed
        assert "DELETE" not in allowed
        assert "SMUGGLE" not in allowed
        assert "XUPLOAD" not in allowed

    def test_options_allows_advanced_upload_headers(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(
            root_dir=str(temp_dir),
            quiet=True,
            cors_origin="https://app.example",
            profile="lab",
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


class TestBrowserMutationGuard:
    @staticmethod
    def _raw_request(
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        body: bytes = b"",
    ) -> bytes:
        header_lines = [f"{method} {path} HTTP/1.1"]
        for key, value in (headers or {}).items():
            header_lines.append(f"{key}: {value}")
        if body:
            header_lines.append(f"Content-Length: {len(body)}")
        return "\r\n".join(header_lines).encode("ascii") + b"\r\n\r\n" + body

    def test_cross_origin_mutation_rejected_by_default(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)
        req = make_request(
            "POST",
            "/upload",
            headers={
                "Host": "127.0.0.1:8080",
                "Origin": "https://evil.example",
            },
            body=b"x",
        )

        assert server._is_browser_mutation_allowed(req) is False

    def test_same_origin_mutation_allowed_by_default(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)
        req = make_request(
            "POST",
            "/upload",
            headers={
                "Host": "127.0.0.1:8080",
                "Origin": "http://127.0.0.1:8080",
            },
            body=b"x",
        )

        assert server._is_browser_mutation_allowed(req) is True

    def test_cross_origin_mutation_with_wildcard_cors_is_rejected(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True, cors_origin="*")
        req = make_request(
            "POST",
            "/upload",
            headers={
                "Host": "127.0.0.1:8080",
                "Origin": "https://app.example",
            },
            body=b"x",
        )

        assert server._resolve_cors_origin(req) == "*"
        assert server._is_browser_mutation_allowed(req) is False

    def test_cross_site_fetch_metadata_with_wildcard_cors_is_rejected(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True, cors_origin="*")
        req = make_request(
            "POST",
            "/upload",
            headers={
                "Host": "127.0.0.1:8080",
                "Origin": "https://app.example",
                "Sec-Fetch-Site": "cross-site",
            },
            body=b"x",
        )

        assert server._resolve_cors_origin(req) == "*"
        assert server._is_browser_mutation_allowed(req) is False

    def test_literal_wildcard_origin_with_wildcard_cors_is_rejected(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True, cors_origin="*")
        req = make_request(
            "POST",
            "/upload",
            headers={
                "Host": "127.0.0.1:8080",
                "Origin": "*",
            },
            body=b"x",
        )

        assert server._resolve_cors_origin(req) == "*"
        assert server._is_browser_mutation_allowed(req) is False

    def test_configured_cors_origin_allows_browser_mutation(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(
            root_dir=str(temp_dir),
            quiet=True,
            cors_origin="https://app.example",
        )
        req = make_request(
            "DELETE",
            "/uploads/file.txt",
            headers={
                "Host": "127.0.0.1:8080",
                "Origin": "https://app.example",
            },
        )

        assert server._resolve_cors_origin(req) == "https://app.example"
        assert server._is_browser_mutation_allowed(req) is True

    def test_non_browser_mutation_without_browser_headers_allowed(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)
        req = make_request(
            "POST",
            "/upload",
            headers={"Host": "127.0.0.1:8080"},
            body=b"x",
        )

        assert server._is_browser_mutation_allowed(req) is True

    def test_fetch_metadata_cross_site_mutation_without_origin_rejected(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)
        req = make_request(
            "POST",
            "/upload",
            headers={
                "Host": "127.0.0.1:8080",
                "Sec-Fetch-Site": "cross-site",
            },
            body=b"x",
        )

        assert server._is_browser_mutation_allowed(req) is False

    def test_fetch_metadata_same_site_mutation_without_origin_rejected(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)
        req = make_request(
            "POST",
            "/upload",
            headers={
                "Host": "127.0.0.1:8080",
                "Sec-Fetch-Site": "same-site",
            },
            body=b"x",
        )

        assert server._is_browser_mutation_allowed(req) is False

    def test_fetch_metadata_same_origin_mutation_without_origin_allowed(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)
        req = make_request(
            "POST",
            "/upload",
            headers={
                "Host": "127.0.0.1:8080",
                "Sec-Fetch-Site": "same-origin",
            },
            body=b"x",
        )

        assert server._is_browser_mutation_allowed(req) is True

    def test_conflicting_cross_site_fetch_metadata_rejects_default_same_origin(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)
        req = make_request(
            "POST",
            "/upload",
            headers={
                "Host": "127.0.0.1:8080",
                "Origin": "http://127.0.0.1:8080",
                "Sec-Fetch-Site": "cross-site",
            },
            body=b"x",
        )

        assert server._is_browser_mutation_allowed(req) is False

    def test_cross_site_fetch_metadata_allows_configured_cors_origin(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(
            root_dir=str(temp_dir),
            quiet=True,
            cors_origin="https://app.example",
        )
        req = make_request(
            "POST",
            "/upload",
            headers={
                "Host": "127.0.0.1:8080",
                "Origin": "https://app.example",
                "Sec-Fetch-Site": "cross-site",
            },
            body=b"x",
        )

        assert server._is_browser_mutation_allowed(req) is True

    def test_null_origin_mutation_rejected_by_default(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)
        req = make_request(
            "POST",
            "/upload",
            headers={
                "Host": "127.0.0.1:8080",
                "Origin": "null",
            },
            body=b"x",
        )

        assert server._is_browser_mutation_allowed(req) is False

    def test_origin_with_missing_host_is_rejected_for_mutation(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)
        req = make_request(
            "POST",
            "/upload",
            headers={"Origin": "http://127.0.0.1:8080"},
            body=b"x",
        )

        assert server._is_browser_mutation_allowed(req) is False

    def test_cross_origin_read_only_request_not_guarded(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)
        req = make_request(
            "GET",
            "/",
            headers={
                "Host": "127.0.0.1:8080",
                "Origin": "https://evil.example",
            },
        )

        assert server._is_browser_mutation_allowed(req) is True

    def test_unknown_advanced_upload_payload_is_guarded(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True, profile="lab")
        req = make_request(
            "XUPLOAD",
            "/",
            headers={
                "Host": "127.0.0.1:8080",
                "Origin": "https://evil.example",
                "X-D": "eA==",
            },
        )

        assert server._is_browser_mutation_allowed(req) is False

    def test_real_pipeline_rejects_cross_origin_mutation_without_write(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)
        sock = _SendSocketStub()

        keep_alive = server._process_request(
            self._raw_request(
                "POST",
                "/blocked.txt",
                headers={
                    "Host": "127.0.0.1:8080",
                    "Origin": "https://evil.example",
                },
                body=b"blocked",
            ),
            sock,
            ADDR,
            1,
        )

        assert keep_alive is False
        assert len(sock.sent) == 1
        assert b"HTTP/1.1 403 Forbidden" in sock.sent[0]
        assert not (server.upload_dir / "blocked.txt").exists()

    def test_real_pipeline_allows_same_origin_mutation(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)
        sock = _SendSocketStub()

        keep_alive = server._process_request(
            self._raw_request(
                "POST",
                "/same-origin.txt",
                headers={
                    "Host": "127.0.0.1:8080",
                    "Origin": "http://127.0.0.1:8080",
                },
                body=b"same-origin",
            ),
            sock,
            ADDR,
            1,
        )

        assert keep_alive is True
        assert len(sock.sent) == 1
        assert b"HTTP/1.1 201 Created" in sock.sent[0]
        assert (server.upload_dir / "same-origin.txt").read_bytes() == b"same-origin"

    def test_real_pipeline_allows_non_browser_mutation(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)
        sock = _SendSocketStub()

        keep_alive = server._process_request(
            self._raw_request(
                "POST",
                "/api-client.txt",
                headers={"Host": "127.0.0.1:8080"},
                body=b"api-client",
            ),
            sock,
            ADDR,
            1,
        )

        assert keep_alive is True
        assert len(sock.sent) == 1
        assert b"HTTP/1.1 201 Created" in sock.sent[0]
        assert (server.upload_dir / "api-client.txt").read_bytes() == b"api-client"


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
    def __init__(self, accepted: list[tuple[object, tuple[str, int]]] | None = None) -> None:
        self.options: list[tuple[int, int, int]] = []
        self.bound: tuple[str, int] | None = None
        self.backlog: int | None = None
        self.timeouts: list[float] = []
        self.closed = False
        self.accepted = list(accepted or [])

    def setsockopt(self, level: int, optname: int, value: int) -> None:
        self.options.append((level, optname, value))

    def bind(self, addr: tuple[str, int]) -> None:
        self.bound = addr

    def listen(self, backlog: int) -> None:
        self.backlog = backlog

    def settimeout(self, value: float) -> None:
        self.timeouts.append(value)

    def accept(self) -> tuple[object, tuple[str, int]]:
        if self.accepted:
            return self.accepted.pop(0)
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

    def test_single_worker_default_websocket_budget_preserves_worker_pool(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True, max_workers=1)

        assert server.max_websocket_connections == 0
        assert server._try_acquire_websocket_slot() is False
        ws_metrics = server.get_metrics()["websocket"]
        assert ws_metrics["active"] == 0
        assert ws_metrics["rejected_admissions"] == 1

    def test_explicit_single_websocket_budget_can_admit_connection(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(
            root_dir=str(temp_dir),
            quiet=True,
            max_workers=1,
            max_websocket_connections=1,
        )

        assert server._try_acquire_websocket_slot() is True
        ws_metrics = server.get_metrics()["websocket"]
        assert ws_metrics["active"] == 1
        assert ws_metrics["rejected_admissions"] == 0
        server._release_websocket_slot()
        ws_metrics = server.get_metrics()["websocket"]
        assert ws_metrics["active"] == 0
        assert ws_metrics["rejected_admissions"] == 0
        assert ws_metrics["closed"] == 1

    def test_request_admission_rejects_when_worker_budget_is_full(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True, max_workers=1)

        assert server._try_acquire_request_admission() is True
        assert server._try_acquire_request_admission() is False

        assert server.get_metrics()["request_admission"] == {
            "active": 1,
            "accepted": 1,
            "rejected": 1,
        }
        server._release_request_admission()
        assert server.get_metrics()["request_admission"] == {
            "active": 0,
            "accepted": 1,
            "rejected": 1,
        }

    def test_admitted_client_releases_admission_after_normal_close(
        self,
        temp_dir,
        monkeypatch,
    ):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)
        sock = _SendSocketStub()
        calls: list[tuple[object, tuple[str, int]]] = []

        assert server._try_acquire_request_admission() is True
        monkeypatch.setattr(server, "_handle_client", lambda *args: calls.append(args))

        server._handle_admitted_client(sock, ("127.0.0.1", 43210))

        assert calls == [(sock, ("127.0.0.1", 43210))]
        assert server.get_metrics()["request_admission"] == {
            "active": 0,
            "accepted": 1,
            "rejected": 0,
        }
        assert server.get_metrics()["connections"] == {
            "active": 0,
            "accepted": 1,
            "closed": 1,
        }

    def test_admitted_client_releases_admission_after_handler_exception(
        self,
        temp_dir,
        monkeypatch,
    ):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)
        sock = _SendSocketStub()

        def fail_handle(*_args):
            raise RuntimeError("boom")

        assert server._try_acquire_request_admission() is True
        monkeypatch.setattr(server, "_handle_client", fail_handle)

        with pytest.raises(RuntimeError, match="boom"):
            server._handle_admitted_client(sock, ("127.0.0.1", 43210))

        assert server.get_metrics()["request_admission"] == {
            "active": 0,
            "accepted": 1,
            "rejected": 0,
        }
        assert server.get_metrics()["connections"] == {
            "active": 0,
            "accepted": 1,
            "closed": 1,
        }

    def test_handle_client_records_unexpected_worker_exception(
        self,
        temp_dir,
        monkeypatch,
        caplog,
    ):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)
        sock = _SendSocketStub()

        def fail_receive(*_args, **_kwargs):
            raise RuntimeError("receive failed")

        caplog.set_level(logging.ERROR, logger="httpserver")
        monkeypatch.setattr(server, "_receive_request_result", fail_receive)
        server.running = True

        server._handle_client(sock, ("127.0.0.1", 43210))

        assert sock.closed is True
        assert server.get_metrics()["worker"] == {
            "exceptions": 1,
            "exception_sources": {"handle_client": 1},
            "last_exception_type": "RuntimeError",
        }
        assert "Client worker failed for 127.0.0.1:43210" in caplog.text

    def test_admitted_client_releases_admission_when_tls_handshake_fails(
        self,
        temp_dir,
        monkeypatch,
    ):
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
        assert server._try_acquire_request_admission() is True
        monkeypatch.setattr(
            server,
            "_receive_request",
            lambda *_args, **_kwargs: pytest.fail("handshake failure should return first"),
        )

        server._handle_admitted_client(sock, ("127.0.0.1", 43210))

        assert sock.closed is True
        assert server.get_metrics()["request_admission"] == {
            "active": 0,
            "accepted": 1,
            "rejected": 0,
        }

    def test_cancelled_worker_future_releases_admission(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)
        sock = _SendSocketStub()

        class _CancelledFuture:
            def cancelled(self) -> bool:
                return True

        assert server._try_acquire_request_admission() is True

        server._release_cancelled_admission(_CancelledFuture(), sock)

        assert sock.closed is True
        assert server.get_metrics()["request_admission"] == {
            "active": 0,
            "accepted": 1,
            "rejected": 0,
        }

    def test_worker_future_exception_is_logged_and_metriced(
        self,
        temp_dir,
        caplog,
    ):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)
        sock = _SendSocketStub()

        class _FailedFuture:
            def cancelled(self) -> bool:
                return False

            def exception(self):
                return RuntimeError("worker exploded")

        caplog.set_level(logging.ERROR, logger="httpserver")

        server._finalize_worker_future(_FailedFuture(), sock, ("127.0.0.1", 43210))

        assert sock.closed is False
        assert server.get_metrics()["worker"] == {
            "exceptions": 1,
            "exception_sources": {"worker_future": 1},
            "last_exception_type": "RuntimeError",
        }
        assert "Worker future failed while handling 127.0.0.1:43210" in caplog.text

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

    def test_receive_request_records_rejection_metrics(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(
            root_dir=str(temp_dir),
            quiet=True,
            max_header_size=16,
        )
        sock = _WebSocketSocketStub([b"GET / HTTP/1.1\r\nX-Pad: oversized"])

        result = server._receive_request(sock)

        assert result == b""
        assert server.get_metrics()["receive_rejections"] == {"header_too_large": 1}

    def test_receive_request_legacy_wrapper_releases_body_reservation(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(
            root_dir=str(temp_dir),
            quiet=True,
            body_memory_budget=8,
        )
        request = b"POST / HTTP/1.1\r\nContent-Length: 5\r\n\r\nhello"
        sock = _WebSocketSocketStub([request])

        result = server._receive_request(sock)

        assert result == request
        body_memory = server.get_metrics()["body_memory"]
        assert body_memory["current_bytes"] == 0
        assert body_memory["peak_bytes"] == 5

    def test_handle_client_releases_body_reservation_when_processing_raises(
        self,
        temp_dir,
        monkeypatch,
    ):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)
        sock = _SendSocketStub()
        reservation = server._body_memory_budget.try_reserve(4)
        assert reservation is not None

        def fake_receive(_sock, idle_timeout=None):
            return RequestReceiveResult(b"body", reservation)

        def fail_process(*_args, **_kwargs):
            raise RuntimeError("process failed")

        monkeypatch.setattr(server, "_receive_request_result", fake_receive)
        monkeypatch.setattr(server, "_process_request", fail_process)
        server.running = True

        server._handle_client(sock, ("127.0.0.1", 43210))

        assert server.get_metrics()["body_memory"]["current_bytes"] == 0
        assert server.get_metrics()["worker"]["last_exception_type"] == "RuntimeError"
        assert sock.closed is True

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

    def test_smuggle_temp_html_uses_artifact_csp_without_weakening_ui_csp(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>", encoding="utf-8")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True, profile="lab")
        source_path = server.upload_dir / "small.txt"
        source_path.write_bytes(b"small payload")

        smuggle_response = server.handle_smuggle(make_request("SMUGGLE", "/uploads/small.txt"))
        smuggle_body = json.loads(smuggle_response.body)
        artifact_response = server.handle_get(make_request("GET", smuggle_body["url"]))

        assert artifact_response.status_code == 200
        assert artifact_response.headers["Content-Type"].startswith("text/html")
        artifact_csp = artifact_response.headers["Content-Security-Policy"]
        assert "script-src 'self' 'unsafe-inline'" in artifact_csp
        assert "frame-ancestors 'none'" in artifact_csp
        assert artifact_response.stream_cleanup is not None

        ui_response = server.handle_get(make_request("GET", "/"))
        ui_csp = ui_response.headers["Content-Security-Policy"]
        assert "script-src 'self';" in ui_csp
        assert "script-src 'self' 'unsafe-inline'" not in ui_csp

        ordinary_html = server.upload_dir / "ordinary.html"
        ordinary_html.write_text("<script>window.executed=true</script>", encoding="utf-8")
        ordinary_response = server.handle_get(make_request("GET", "/uploads/ordinary.html"))

        assert ordinary_response.headers["Content-Type"] == "application/octet-stream"
        assert "Content-Security-Policy" not in ordinary_response.headers

    def test_smuggle_encrypted_response_exposes_verification_password(
        self,
        server,
        upload_dir,
        monkeypatch,
    ):
        monkeypatch.setattr("src.handlers.smuggle.secrets.choice", lambda _alphabet: "A")
        source_path = upload_dir / "secret.txt"
        source_path.write_bytes(b"secret payload")

        response = server.handle_smuggle(make_request("SMUGGLE", "/uploads/secret.txt?encrypt=1"))

        assert response.status_code == 200
        body = json.loads(response.body)
        assert body["url"].startswith("/uploads/smuggle_")
        assert body["file"] == "secret.txt"
        assert body["encrypted"] is True
        assert body["password"] == "AAAAAAA"

        temp_path = upload_dir / body["url"].removeprefix("/uploads/")
        html = temp_path.read_text(encoding="utf-8")
        assert "Protected File" in html
        assert "secret payload" not in html

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
        assert "password" not in body

        temp_path = upload_dir / body["url"].removeprefix("/uploads/")
        assert temp_path.exists()
        assert str(temp_path) in server._temp_smuggle_files
        assert "small.txt" in temp_path.read_text(encoding="utf-8")

    def test_smuggle_builder_rejects_non_allowlisted_extension(self, server, upload_dir):
        (upload_dir / "small.txt").write_bytes(b"small payload")

        response = server.handle_smuggle(
            make_request(
                "SMUGGLE",
                "/uploads/small.txt?download_name=Quarterly-Report&download_ext=exe&preset=card_manual",
            )
        )

        assert response.status_code == 400
        body = json.loads(response.body)
        assert body["status"] == 400
        assert body["error"] == "Invalid SMUGGLE builder extension"

    def test_smuggle_builder_rejects_invalid_preset(self, server, upload_dir):
        (upload_dir / "small.txt").write_bytes(b"small payload")

        response = server.handle_smuggle(
            make_request(
                "SMUGGLE",
                "/uploads/small.txt?download_name=Quarterly-Report&download_ext=pdf&preset=viewer",
            )
        )

        assert response.status_code == 400
        body = json.loads(response.body)
        assert body["status"] == 400
        assert body["error"] == "Invalid SMUGGLE builder preset"

    def test_smuggle_builder_rejects_invalid_delay(self, server, upload_dir):
        (upload_dir / "small.txt").write_bytes(b"small payload")

        response = server.handle_smuggle(
            make_request(
                "SMUGGLE",
                "/uploads/small.txt?download_name=Quarterly-Report&download_ext=pdf"
                "&preset=card_auto&delay_ms=12001",
            )
        )

        assert response.status_code == 400
        body = json.loads(response.body)
        assert body["status"] == 400
        assert body["error"] == "Invalid SMUGGLE builder delay"

    def test_smuggle_builder_rejects_invalid_show_notice(self, server, upload_dir):
        (upload_dir / "small.txt").write_bytes(b"small payload")

        response = server.handle_smuggle(
            make_request(
                "SMUGGLE",
                "/uploads/small.txt?download_name=Quarterly-Report&download_ext=pdf"
                "&preset=card_manual&show_notice=banana",
            )
        )

        assert response.status_code == 400
        body = json.loads(response.body)
        assert body["status"] == 400
        assert body["error"] == "Invalid SMUGGLE builder show_notice"

    def test_smuggle_builder_rejects_oversized_title(self, server, upload_dir):
        (upload_dir / "small.txt").write_bytes(b"small payload")
        oversized_title = "A" * 121

        response = server.handle_smuggle(
            make_request(
                "SMUGGLE",
                "/uploads/small.txt?download_name=Quarterly-Report&download_ext=pdf"
                f"&preset=card_manual&title={oversized_title}",
            )
        )

        assert response.status_code == 400
        body = json.loads(response.body)
        assert body["status"] == 400
        assert body["error"] == "SMUGGLE builder title is too long"

    def test_smuggle_builder_card_auto_renders_selected_download_name(self, server, upload_dir):
        (upload_dir / "small.txt").write_bytes(b"small payload")

        response = server.handle_smuggle(
            make_request(
                "SMUGGLE",
                "/uploads/small.txt?download_name=Quarterly-Report&download_ext=pdf"
                "&preset=card_auto&title=Quarterly%20Report"
                "&message=Internal%20lab%20test%20artifact"
                "&cta_label=Download%20test%20artifact&delay_ms=1200&show_notice=1",
            )
        )

        assert response.status_code == 200
        body = json.loads(response.body)
        temp_path = upload_dir / body["url"].removeprefix("/uploads/")
        html = temp_path.read_text(encoding="utf-8")
        assert "Quarterly-Report.pdf" in html
        assert "Internal lab test artifact" in html
        assert "Test artifact notice: internal lab-only page." in html
        assert 'id="smuggleCountdown"' in html

    def test_smuggle_builder_encrypted_response_uses_resolved_filename(
        self,
        server,
        upload_dir,
        monkeypatch,
    ):
        monkeypatch.setattr("src.handlers.smuggle.secrets.choice", lambda _alphabet: "A")
        (upload_dir / "secret.txt").write_bytes(b"secret payload")

        response = server.handle_smuggle(
            make_request(
                "SMUGGLE",
                "/uploads/secret.txt?encrypt=1&download_name=Quarterly-Report"
                "&download_ext=pdf&preset=direct",
            )
        )

        assert response.status_code == 200
        body = json.loads(response.body)
        assert body["encrypted"] is True
        assert body["password"] == "AAAAAAA"
        temp_path = upload_dir / body["url"].removeprefix("/uploads/")
        html = temp_path.read_text(encoding="utf-8")
        assert "Quarterly-Report.pdf" in html
        assert "CryptoJS.SHA256" in html

    def test_smuggle_temp_cleanup_removes_artifacts_over_max_age(
        self,
        temp_dir,
        monkeypatch,
    ):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)
        server.smuggle_temp_policy = SmuggleTempPolicy(
            max_age_seconds=10,
            max_file_count=None,
            max_total_bytes=None,
        )
        old_temp = server.upload_dir / "smuggle_old.html"
        fresh_temp = server.upload_dir / "smuggle_fresh.html"
        old_temp.write_text("old", encoding="utf-8")
        fresh_temp.write_text("fresh", encoding="utf-8")
        os.utime(old_temp, (80, 80))
        os.utime(fresh_temp, (95, 95))
        server._temp_smuggle_files.update({str(old_temp), str(fresh_temp)})
        monkeypatch.setattr("src.handlers.smuggle.time.time", lambda: 100.0)

        removed = server.cleanup_smuggle_temp_artifacts()

        assert removed == 1
        assert not old_temp.exists()
        assert fresh_temp.exists()
        assert str(old_temp) not in server._temp_smuggle_files
        assert str(fresh_temp) in server._temp_smuggle_files

    def test_smuggle_temp_cleanup_prunes_oldest_over_file_limit(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)
        server.smuggle_temp_policy = SmuggleTempPolicy(
            max_age_seconds=None,
            max_file_count=1,
            max_total_bytes=None,
        )
        old_temp = server.upload_dir / "smuggle_old.html"
        new_temp = server.upload_dir / "smuggle_new.html"
        old_temp.write_text("old", encoding="utf-8")
        new_temp.write_text("new", encoding="utf-8")
        os.utime(old_temp, (80, 80))
        os.utime(new_temp, (90, 90))
        server._temp_smuggle_files.update({str(old_temp), str(new_temp)})

        removed = server.cleanup_smuggle_temp_artifacts()

        assert removed == 1
        assert not old_temp.exists()
        assert new_temp.exists()
        assert str(old_temp) not in server._temp_smuggle_files
        assert str(new_temp) in server._temp_smuggle_files

    def test_smuggle_temp_cleanup_prunes_oldest_over_byte_limit(self, temp_dir):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)
        server.smuggle_temp_policy = SmuggleTempPolicy(
            max_age_seconds=None,
            max_file_count=None,
            max_total_bytes=5,
        )
        old_temp = server.upload_dir / "smuggle_old.html"
        new_temp = server.upload_dir / "smuggle_new.html"
        old_temp.write_bytes(b"1234")
        new_temp.write_bytes(b"5678")
        os.utime(old_temp, (80, 80))
        os.utime(new_temp, (90, 90))
        server._temp_smuggle_files.update({str(old_temp), str(new_temp)})

        removed = server.cleanup_smuggle_temp_artifacts()

        assert removed == 1
        assert not old_temp.exists()
        assert new_temp.exists()
        assert str(old_temp) not in server._temp_smuggle_files
        assert str(new_temp) in server._temp_smuggle_files

    def test_smuggle_rejects_temp_artifact_over_byte_limit_without_partial_file(
        self,
        server,
        upload_dir,
    ):
        server.smuggle_source_size_limit = 64
        server.smuggle_temp_policy = SmuggleTempPolicy(
            max_age_seconds=None,
            max_file_count=10,
            max_total_bytes=1,
        )
        source_path = upload_dir / "small.txt"
        source_path.write_bytes(b"small payload")

        response = server.handle_smuggle(make_request("SMUGGLE", "/uploads/small.txt"))

        assert response.status_code == 507
        body = json.loads(response.body)
        assert body["status"] == 507
        assert "SMUGGLE temp storage quota exceeded" in body["error"]
        assert "X-Smuggle-URL" not in response.headers
        assert server._temp_smuggle_files == set()
        assert list(upload_dir.glob("smuggle_*.html")) == []

    def test_smuggle_generation_prunes_existing_temp_artifact_for_file_limit(
        self,
        server,
        upload_dir,
    ):
        server.smuggle_source_size_limit = 64
        server.smuggle_temp_policy = SmuggleTempPolicy(
            max_age_seconds=None,
            max_file_count=1,
            max_total_bytes=None,
        )
        old_temp = upload_dir / "smuggle_old.html"
        old_temp.write_text("old", encoding="utf-8")
        os.utime(old_temp, (80, 80))
        server._temp_smuggle_files.add(str(old_temp))
        source_path = upload_dir / "small.txt"
        source_path.write_bytes(b"small payload")

        response = server.handle_smuggle(make_request("SMUGGLE", "/uploads/small.txt"))

        assert response.status_code == 200
        body = json.loads(response.body)
        temp_path = upload_dir / body["url"].removeprefix("/uploads/")
        assert not old_temp.exists()
        assert temp_path.exists()
        assert str(old_temp) not in server._temp_smuggle_files
        assert server._temp_smuggle_files == {str(temp_path)}

    def test_smuggle_temp_get_streams_and_cleans_up_without_full_read(
        self,
        temp_dir,
        monkeypatch,
    ):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True, profile="lab")
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
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True, profile="lab")
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
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True, profile="lab")
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
        lab_server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True, profile="lab")

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

        assert server._is_websocket_upgrade_attempt(upgrade_request) is False
        assert lab_server._is_websocket_upgrade_attempt(upgrade_request) is True
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
            return RequestReceiveResult(next(payloads, b""))

        def fake_process(data, _sock, _addr, request_num):
            processed.append((data, request_num))
            return request_num == 1

        monkeypatch.setattr(server, "_receive_request_result", fake_receive)
        monkeypatch.setattr(server, "_process_request", fake_process)
        server.running = True

        server._handle_client(sock, ("127.0.0.1", 43210))

        assert idle_timeouts == [None, server.KEEP_ALIVE_TIMEOUT]
        assert processed == [(b"first", 1), (b"second", 2)]
        assert server.get_metrics()["bytes_received"] == len(b"first") + len(b"second")
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
        assert server.get_metrics()["websocket"]["idle_pings"] == 1

    def test_handle_notepad_ws_records_incomplete_frame_timeout(
        self,
        temp_dir,
        monkeypatch,
    ):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(
            root_dir=str(temp_dir),
            quiet=True,
            websocket_frame_idle_timeout=0.5,
        )
        server.running = True
        times = iter([100.0, 101.0])
        monkeypatch.setattr("src.server.time.monotonic", lambda: next(times, 101.0))
        sock = _WebSocketSocketStub([b"\x81\x85", TimeoutError()])
        request = make_request(
            "GET",
            "/notes/ws",
            headers={"Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ=="},
        )

        server._handle_notepad_ws(sock, request)

        close_frame = parse_ws_frame(sock.sent[-1])
        assert close_frame is not None
        assert close_frame[0] == WS_CLOSE
        assert struct.unpack("!H", close_frame[1][:2])[0] == 1002
        metrics = server.get_metrics()
        assert metrics["websocket"]["incomplete_frame_timeouts"] == 1
        assert metrics["timeouts"] == {"websocket_incomplete_frame": 1}

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
        assert server.get_metrics()["websocket"]["message_too_big"] == 1

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
        assert "Max headers: 64 KiB" in output
        assert "Profile: workspace" in output
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

    def test_start_acquires_admission_before_worker_submission(
        self,
        temp_dir,
        monkeypatch,
        capsys,
    ):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True, max_workers=1)
        client = _SendSocketStub()
        listening_socket = _ListeningSocketStub([(client, ("127.0.0.1", 43210))])
        submitted: list[tuple[object, tuple[str, int]]] = []

        class _DoneFuture:
            def add_done_callback(self, callback) -> None:
                callback(self)

            def cancelled(self) -> bool:
                return False

        class _ExecutorStub:
            def __init__(self, max_workers: int) -> None:
                assert max_workers == 1

            def submit(self, fn, client_socket, client_address):
                assert server.get_metrics()["request_admission"] == {
                    "active": 1,
                    "accepted": 1,
                    "rejected": 0,
                }
                submitted.append((client_socket, client_address))
                fn(client_socket, client_address)
                return _DoneFuture()

            def shutdown(self, wait: bool, cancel_futures: bool) -> None:
                assert wait is True
                assert cancel_futures is True

        monkeypatch.setattr(server, "_setup_tls", lambda: None)
        monkeypatch.setattr(server, "_handle_client", lambda *_args: None)
        monkeypatch.setattr("src.server.socket.socket", lambda *_args, **_kwargs: listening_socket)
        monkeypatch.setattr("src.server.ThreadPoolExecutor", _ExecutorStub)

        server.start()

        capsys.readouterr()
        assert submitted == [(client, ("127.0.0.1", 43210))]
        assert server.get_metrics()["request_admission"] == {
            "active": 0,
            "accepted": 1,
            "rejected": 0,
        }

    def test_start_rejects_connection_when_admission_budget_is_full(
        self,
        temp_dir,
        monkeypatch,
        capsys,
    ):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True, max_workers=1)
        client = _SendSocketStub()
        listening_socket = _ListeningSocketStub([(client, ("127.0.0.1", 43210))])

        class _ExecutorStub:
            def __init__(self, max_workers: int) -> None:
                assert max_workers == 1

            def submit(self, *_args, **_kwargs) -> None:
                raise AssertionError("overloaded connection must not be submitted")

            def shutdown(self, wait: bool, cancel_futures: bool) -> None:
                assert wait is True
                assert cancel_futures is True

        assert server._try_acquire_request_admission() is True
        monkeypatch.setattr(server, "_setup_tls", lambda: None)
        monkeypatch.setattr("src.server.socket.socket", lambda *_args, **_kwargs: listening_socket)
        monkeypatch.setattr("src.server.ThreadPoolExecutor", _ExecutorStub)

        server.start()

        capsys.readouterr()
        response_bytes = b"".join(client.sent)
        assert response_bytes.startswith(b"HTTP/1.1 503 ")
        assert json.loads(response_bytes.split(b"\r\n\r\n", 1)[1]) == {
            "error": "Server busy",
            "status": 503,
        }
        assert client.closed is True
        assert server.get_metrics()["request_admission"] == {
            "active": 1,
            "accepted": 1,
            "rejected": 1,
        }
        server._release_request_admission()

    def test_start_releases_admission_when_submit_fails(
        self,
        temp_dir,
        monkeypatch,
        capsys,
    ):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True, max_workers=1)
        client = _SendSocketStub()
        listening_socket = _ListeningSocketStub([(client, ("127.0.0.1", 43210))])

        class _ExecutorStub:
            def __init__(self, max_workers: int) -> None:
                assert max_workers == 1

            def submit(self, *_args, **_kwargs) -> None:
                raise RuntimeError("executor unavailable")

            def shutdown(self, wait: bool, cancel_futures: bool) -> None:
                assert wait is True
                assert cancel_futures is True

        monkeypatch.setattr(server, "_setup_tls", lambda: None)
        monkeypatch.setattr("src.server.socket.socket", lambda *_args, **_kwargs: listening_socket)
        monkeypatch.setattr("src.server.ThreadPoolExecutor", _ExecutorStub)

        server.start()

        capsys.readouterr()
        assert client.closed is True
        assert server.get_metrics()["request_admission"] == {
            "active": 0,
            "accepted": 1,
            "rejected": 0,
        }

    def test_start_releases_admission_when_submitted_future_is_cancelled(
        self,
        temp_dir,
        monkeypatch,
        capsys,
    ):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True, max_workers=1)
        client = _SendSocketStub()
        listening_socket = _ListeningSocketStub([(client, ("127.0.0.1", 43210))])

        class _CancelledFuture:
            def add_done_callback(self, callback) -> None:
                callback(self)

            def cancelled(self) -> bool:
                return True

        class _ExecutorStub:
            def __init__(self, max_workers: int) -> None:
                assert max_workers == 1

            def submit(self, *_args, **_kwargs):
                return _CancelledFuture()

            def shutdown(self, wait: bool, cancel_futures: bool) -> None:
                assert wait is True
                assert cancel_futures is True

        monkeypatch.setattr(server, "_setup_tls", lambda: None)
        monkeypatch.setattr("src.server.socket.socket", lambda *_args, **_kwargs: listening_socket)
        monkeypatch.setattr("src.server.ThreadPoolExecutor", _ExecutorStub)

        server.start()

        capsys.readouterr()
        assert client.closed is True
        assert server.get_metrics()["request_admission"] == {
            "active": 0,
            "accepted": 1,
            "rejected": 0,
        }
