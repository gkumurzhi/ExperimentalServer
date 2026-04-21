"""Focused tests for request pipeline orchestration and failure handling."""

from __future__ import annotations

from pathlib import Path

from src.http import HTTPRequest, HTTPResponse
from src.request_pipeline import RequestPipeline


def _make_raw_request(
    method: str = "GET",
    path: str = "/",
    headers: dict[str, str] | None = None,
    body: bytes = b"",
) -> bytes:
    """Build raw HTTP request bytes for pipeline tests."""
    header_lines = [f"{method} {path} HTTP/1.1"]
    if headers:
        for key, value in headers.items():
            header_lines.append(f"{key}: {value}")
    if body:
        header_lines.append(f"Content-Length: {len(body)}")
    return "\r\n".join(header_lines).encode("ascii") + b"\r\n\r\n" + body


class _SocketStub:
    """Capture writes performed by the pipeline."""

    def __init__(self, *, fail_on_send: bool = False) -> None:
        self.fail_on_send = fail_on_send
        self.sent: list[bytes] = []

    def sendall(self, data: bytes) -> None:
        if self.fail_on_send:
            raise OSError("send failed")
        self.sent.append(data)


class _PipelineServerStub:
    """Small configurable stand-in for RequestPipelineServer."""

    KEEP_ALIVE_TIMEOUT = 15

    def __init__(self) -> None:
        self.opsec_mode = False
        self.cors_origin: str | None = None
        self._ecdh_manager: object | None = object()
        self.use_keep_alive = False
        self.remaining_requests = 0
        self.auth_error: HTTPResponse | None = None
        self.size_error: HTTPResponse | None = None
        self.dispatch_response = HTTPResponse(200)
        self.send_response_bytes = 0
        self.websocket_attempt = False
        self.websocket_origin_allowed = True
        self.raise_on_dispatch = False
        self.resolve_calls: list[tuple[str, int]] = []
        self.auth_calls: list[tuple[str, tuple[str, int]]] = []
        self.size_calls: list[str] = []
        self.dispatch_calls: list[str] = []
        self.post_process_calls: list[tuple[str, int, str]] = []
        self.send_calls: list[dict[str, object]] = []
        self.record_calls: list[tuple[int, int, bool]] = []
        self.handled_websocket_paths: list[str] = []

    def _resolve_keep_alive(self, request: HTTPRequest, request_num: int) -> tuple[bool, int]:
        self.resolve_calls.append((request.path, request_num))
        return self.use_keep_alive, self.remaining_requests

    def _authenticate_request(
        self,
        request: HTTPRequest,
        client_address: tuple[str, int],
    ) -> HTTPResponse | None:
        self.auth_calls.append((request.path, client_address))
        return self.auth_error

    def _is_websocket_upgrade_attempt(self, request: HTTPRequest) -> bool:
        return self.websocket_attempt

    def _build_error_response(self, status: int, message: str) -> HTTPResponse:
        response = HTTPResponse(status)
        response.set_body(f"{status}:{message}")
        return response

    def _is_websocket_origin_allowed(self, request: HTTPRequest) -> bool:
        return self.websocket_origin_allowed

    def _handle_notepad_ws(self, sock: _SocketStub, request: HTTPRequest) -> None:
        self.handled_websocket_paths.append(request.path)

    def _check_payload_size(self, request: HTTPRequest) -> HTTPResponse | None:
        self.size_calls.append(request.path)
        return self.size_error

    def _dispatch_handler(self, request: HTTPRequest) -> HTTPResponse:
        self.dispatch_calls.append(request.path)
        if self.raise_on_dispatch:
            raise RuntimeError("boom")
        return self.dispatch_response

    def _post_process_response(
        self,
        request: HTTPRequest,
        response: HTTPResponse,
        request_id: str,
    ) -> None:
        self.post_process_calls.append((request.path, response.status_code, request_id))

    def _send_response(
        self,
        response: HTTPResponse,
        client_socket: _SocketStub,
        _bld: dict[str, object],
    ) -> int:
        self.send_calls.append({"status": response.status_code, "build_args": dict(_bld)})
        return self.send_response_bytes

    def _record_metric(
        self,
        status_code: int,
        response_size: int,
        *,
        error: bool = False,
    ) -> None:
        self.record_calls.append((status_code, response_size, error))


class TestRequestPipeline:
    def test_auth_error_short_circuits_and_uses_keep_alive_headers(self) -> None:
        server = _PipelineServerStub()
        server.use_keep_alive = True
        server.remaining_requests = 4
        auth_error = HTTPResponse(401)
        auth_error.set_body("unauthorized")
        server.auth_error = auth_error
        pipeline = RequestPipeline(server)
        sock = _SocketStub()

        result = pipeline.process(
            _make_raw_request("GET", "/", {"Host": "example.test"}),
            sock,
            ("127.0.0.1", 12345),
            1,
        )

        assert result is False
        assert len(sock.sent) == 1
        assert b"HTTP/1.1 401" in sock.sent[0]
        assert b"Connection: keep-alive" in sock.sent[0]
        assert b"Keep-Alive: timeout=15, max=4" in sock.sent[0]
        assert server.dispatch_calls == []
        assert server.record_calls == [(401, len(sock.sent[0]), False)]

    def test_payload_size_error_short_circuits_before_dispatch(self) -> None:
        server = _PipelineServerStub()
        size_error = HTTPResponse(413)
        size_error.set_body("too large")
        server.size_error = size_error
        pipeline = RequestPipeline(server)
        sock = _SocketStub()

        result = pipeline.process(
            _make_raw_request("POST", "/upload", {"Host": "example.test"}, b"x"),
            sock,
            ("127.0.0.1", 12345),
            1,
        )

        assert result is False
        assert len(sock.sent) == 1
        assert b"HTTP/1.1 413" in sock.sent[0]
        assert server.dispatch_calls == []
        assert server.record_calls == [(413, len(sock.sent[0]), False)]

    def test_success_path_records_metric_and_returns_keep_alive(self) -> None:
        server = _PipelineServerStub()
        server.use_keep_alive = True
        server.remaining_requests = 2
        server.dispatch_response = HTTPResponse(204)
        server.send_response_bytes = 321
        pipeline = RequestPipeline(server)
        sock = _SocketStub()

        result = pipeline.process(
            _make_raw_request("PING", "/", {"Host": "example.test"}),
            sock,
            ("127.0.0.1", 12345),
            3,
        )

        assert result is True
        assert server.post_process_calls
        assert server.send_calls == [
            {
                "status": 204,
                "build_args": {
                    "opsec_mode": False,
                    "cors_origin": None,
                    "keep_alive": True,
                    "keep_alive_timeout": 15,
                    "keep_alive_max": 2,
                },
            }
        ]
        assert server.record_calls == [(204, 321, False)]

    def test_streaming_response_forces_connection_close(self, temp_dir: Path) -> None:
        file_path = temp_dir / "payload.bin"
        file_path.write_bytes(b"streamed")
        response = HTTPResponse(200)
        response.set_file(file_path, "application/octet-stream")

        server = _PipelineServerStub()
        server.use_keep_alive = True
        server.dispatch_response = response
        server.send_response_bytes = 123
        pipeline = RequestPipeline(server)

        result = pipeline.process(
            _make_raw_request("GET", "/download", {"Host": "example.test"}),
            _SocketStub(),
            ("127.0.0.1", 12345),
            1,
        )

        assert result is False
        assert server.record_calls == [(200, 123, False)]

    def test_invalid_websocket_upgrade_returns_400(self) -> None:
        server = _PipelineServerStub()
        server.websocket_attempt = True
        pipeline = RequestPipeline(server)
        sock = _SocketStub()

        result = pipeline.process(
            _make_raw_request(
                "GET",
                "/notes/ws",
                {
                    "Host": "example.test",
                    "Upgrade": "websocket",
                    "Connection": "Upgrade",
                    "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",
                },
            ),
            sock,
            ("127.0.0.1", 12345),
            1,
        )

        assert result is False
        assert len(sock.sent) == 1
        assert b"HTTP/1.1 400" in sock.sent[0]
        assert server.handled_websocket_paths == []
        assert server.record_calls == [(400, len(sock.sent[0]), False)]

    def test_forbidden_websocket_origin_returns_403(self) -> None:
        server = _PipelineServerStub()
        server.websocket_attempt = True
        server.websocket_origin_allowed = False
        pipeline = RequestPipeline(server)
        sock = _SocketStub()

        result = pipeline.process(
            _make_raw_request(
                "GET",
                "/notes/ws",
                {
                    "Host": "example.test",
                    "Origin": "https://evil.example",
                    "Upgrade": "websocket",
                    "Connection": "Upgrade",
                    "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",
                    "Sec-WebSocket-Version": "13",
                },
            ),
            sock,
            ("127.0.0.1", 12345),
            1,
        )

        assert result is False
        assert len(sock.sent) == 1
        assert b"HTTP/1.1 403" in sock.sent[0]
        assert server.handled_websocket_paths == []
        assert server.record_calls == [(403, len(sock.sent[0]), False)]

    def test_websocket_upgrade_without_crypto_returns_501(self) -> None:
        server = _PipelineServerStub()
        server.websocket_attempt = True
        server._ecdh_manager = None
        pipeline = RequestPipeline(server)
        sock = _SocketStub()

        result = pipeline.process(
            _make_raw_request(
                "GET",
                "/notes/ws",
                {
                    "Host": "example.test",
                    "Origin": "http://example.test",
                    "Upgrade": "websocket",
                    "Connection": "Upgrade",
                    "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",
                    "Sec-WebSocket-Version": "13",
                },
            ),
            sock,
            ("127.0.0.1", 12345),
            1,
        )

        assert result is False
        assert len(sock.sent) == 1
        assert b"HTTP/1.1 501" in sock.sent[0]
        assert server.handled_websocket_paths == []
        assert server.record_calls == [(501, len(sock.sent[0]), False)]

    def test_valid_websocket_upgrade_dispatches_handler(self) -> None:
        server = _PipelineServerStub()
        server.websocket_attempt = True
        pipeline = RequestPipeline(server)
        sock = _SocketStub()

        result = pipeline.process(
            _make_raw_request(
                "GET",
                "/notes/ws",
                {
                    "Host": "example.test",
                    "Origin": "http://example.test",
                    "Upgrade": "websocket",
                    "Connection": "Upgrade",
                    "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",
                    "Sec-WebSocket-Version": "13",
                },
            ),
            sock,
            ("127.0.0.1", 12345),
            1,
        )

        assert result is False
        assert sock.sent == []
        assert server.handled_websocket_paths == ["/notes/ws"]
        assert server.record_calls == []

    def test_internal_error_records_metric_and_sends_500(self) -> None:
        server = _PipelineServerStub()
        server.raise_on_dispatch = True
        pipeline = RequestPipeline(server)
        sock = _SocketStub()

        result = pipeline.process(
            _make_raw_request("GET", "/explode", {"Host": "example.test"}),
            sock,
            ("127.0.0.1", 12345),
            1,
        )

        assert result is False
        assert len(sock.sent) == 1
        assert b"HTTP/1.1 500" in sock.sent[0]
        assert server.record_calls == [(500, 0, True)]

    def test_internal_error_ignores_secondary_socket_failure(self) -> None:
        server = _PipelineServerStub()
        server.raise_on_dispatch = True
        pipeline = RequestPipeline(server)

        result = pipeline.process(
            _make_raw_request("GET", "/explode", {"Host": "example.test"}),
            _SocketStub(fail_on_send=True),
            ("127.0.0.1", 12345),
            1,
        )

        assert result is False
        assert server.record_calls == [(500, 0, True)]
