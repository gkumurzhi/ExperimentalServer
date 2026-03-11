"""Tests for extracted server methods: _authenticate_request, _dispatch_handler."""

import base64
import json
import threading
from pathlib import Path

import pytest

from src.handlers import HandlerMixin
from src.http import HTTPRequest, HTTPResponse
from src.security.auth import AuthRateLimiter, BasicAuthenticator
from tests.conftest import make_request


class ServerStub(HandlerMixin):
    """Minimal server with auth and dispatch for unit testing."""

    def __init__(
        self, root_dir: Path, upload_dir: Path, *,
        auth: BasicAuthenticator | None = None,
        opsec: bool = False,
    ):
        self.root_dir = root_dir
        self.upload_dir = upload_dir
        self.sandbox_mode = False
        self.opsec_mode = opsec
        self._temp_smuggle_files: set[str] = set()
        self._smuggle_lock = threading.Lock()
        self._notes_lock = threading.Lock()

        self.authenticator = auth
        self._rate_limiter = AuthRateLimiter() if auth else None

        self.method_handlers = {
            "GET": self.handle_get,
            "HEAD": self.handle_head,
            "POST": self.handle_post,
            "PING": self.handle_ping,
            "INFO": self.handle_info,
            "FETCH": self.handle_fetch,
            "OPTIONS": self.handle_options,
            "NONE": self.handle_none,
        }
        self.opsec_methods: dict[str, str] = {}
        if opsec:
            self.opsec_methods = {
                "upload": "XUPLOAD",
                "download": "XDOWNLOAD",
                "info": "XINFO",
                "ping": "XPING",
            }

    def get_metrics(self):
        return {
            "uptime_seconds": 0, "total_requests": 0, "total_errors": 0,
            "bytes_sent": 0, "status_counts": {},
        }

    # Mirror of ExperimentalHTTPServer._authenticate_request
    def _authenticate_request(
        self, request: HTTPRequest, client_address: tuple[str, int],
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

    # Mirror of ExperimentalHTTPServer._dispatch_handler
    def _dispatch_handler(self, request: HTTPRequest) -> HTTPResponse:
        if self.opsec_mode:
            handler = self._get_opsec_handler(request)
        else:
            handler = self.method_handlers.get(request.method)
        if handler:
            return handler(request)
        if self.opsec_mode:
            response = HTTPResponse(404)
            response.set_body(
                json.dumps({"error": "Not Found", "status": 404}),
                "application/json",
            )
            return response
        return self._method_not_allowed(request.method)

    def _get_opsec_handler(self, request):
        method = request.method
        if method in self.method_handlers:
            return self.method_handlers.get(method)
        if method == self.opsec_methods.get("upload"):
            return self.handle_opsec_upload
        if method == self.opsec_methods.get("download"):
            return self.handle_fetch
        if method == self.opsec_methods.get("info"):
            return self.handle_info
        if method == self.opsec_methods.get("ping"):
            return self.handle_ping
        has_data = (
            request.body
            or request.headers.get("x-d")
            or request.headers.get("x-d-0")
            or request.query_params.get("d")
        )
        if has_data:
            return self.handle_opsec_upload
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
def opsec_server(temp_dir, upload_dir):
    (temp_dir / "index.html").write_text("<html>ok</html>")
    return ServerStub(temp_dir, upload_dir, opsec=True)


ADDR = ("127.0.0.1", 12345)


# ── _authenticate_request tests ───────────────────────────────────

class TestAuthenticateRequest:
    def test_no_auth_configured_returns_none(self, server):
        req = make_request("GET", "/")
        assert server._authenticate_request(req, ADDR) is None

    def test_valid_credentials_returns_none(self, auth_server):
        creds = base64.b64encode(b"admin:secret123").decode()
        req = make_request("GET", "/", headers={"Authorization": f"Basic {creds}"})
        result = auth_server._authenticate_request(req, ADDR)
        assert result is None

    def test_missing_header_returns_401(self, auth_server):
        req = make_request("GET", "/")
        result = auth_server._authenticate_request(req, ADDR)
        assert result is not None
        assert result.status_code == 401
        assert "WWW-Authenticate" in result.headers

    def test_wrong_password_returns_401(self, auth_server):
        creds = base64.b64encode(b"admin:wrongpass").decode()
        req = make_request("GET", "/", headers={"Authorization": f"Basic {creds}"})
        result = auth_server._authenticate_request(req, ADDR)
        assert result is not None
        assert result.status_code == 401

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


# ── _dispatch_handler tests ───────────────────────────────────────

class TestDispatchHandler:
    def test_known_method_dispatches(self, server):
        req = make_request("PING", "/")
        resp = server._dispatch_handler(req)
        assert resp.status_code == 200
        data = json.loads(resp.body)
        assert data["status"] == "pong"

    def test_unknown_method_returns_405(self, server):
        req = make_request("CONNECT", "/")
        resp = server._dispatch_handler(req)
        assert resp.status_code == 405
        assert "Allow" in resp.headers

    def test_opsec_unknown_method_returns_404(self, opsec_server):
        req = make_request("CONNECT", "/")
        resp = opsec_server._dispatch_handler(req)
        assert resp.status_code == 404

    def test_opsec_standard_method_works(self, opsec_server):
        req = make_request("PING", "/")
        resp = opsec_server._dispatch_handler(req)
        assert resp.status_code == 200

    def test_get_dispatches_correctly(self, server):
        req = make_request("GET", "/")
        resp = server._dispatch_handler(req)
        assert resp.status_code == 200
