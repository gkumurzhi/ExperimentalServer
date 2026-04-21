"""Request orchestration for authenticated HTTP and WebSocket upgrade handling."""

from __future__ import annotations

import logging
import secrets
import socket
import time
from typing import Any, Protocol, TypedDict

from .http import HTTPRequest, HTTPResponse
from .websocket import check_websocket_upgrade

logger = logging.getLogger("httpserver")


class ResponseBuildArgs(TypedDict, total=False):
    """Parameters threaded into :class:`HTTPResponse` header building."""

    opsec_mode: bool
    cors_origin: str | None
    keep_alive: bool
    keep_alive_timeout: int
    keep_alive_max: int


class RequestPipelineServer(Protocol):
    """The subset of server behavior the request pipeline orchestrates."""

    opsec_mode: bool
    cors_origin: str | None
    KEEP_ALIVE_TIMEOUT: int
    _ecdh_manager: Any

    def _resolve_keep_alive(self, request: HTTPRequest, request_num: int) -> tuple[bool, int]: ...

    def _authenticate_request(
        self,
        request: HTTPRequest,
        client_address: tuple[str, int],
    ) -> HTTPResponse | None: ...

    def _is_websocket_upgrade_attempt(self, request: HTTPRequest) -> bool: ...

    def _build_error_response(self, status: int, message: str) -> HTTPResponse: ...

    def _is_websocket_origin_allowed(self, request: HTTPRequest) -> bool: ...

    def _handle_notepad_ws(self, sock: socket.socket, request: HTTPRequest) -> None: ...

    def _check_payload_size(self, request: HTTPRequest) -> HTTPResponse | None: ...

    def _dispatch_handler(self, request: HTTPRequest) -> HTTPResponse: ...

    def _post_process_response(
        self,
        request: HTTPRequest,
        response: HTTPResponse,
        request_id: str,
    ) -> None: ...

    def _send_response(
        self,
        response: HTTPResponse,
        client_socket: socket.socket,
        _bld: ResponseBuildArgs,
    ) -> int: ...

    def _record_metric(
        self,
        status_code: int,
        response_size: int,
        *,
        error: bool = False,
    ) -> None: ...


class RequestPipeline:
    """Coordinate request parsing, auth, dispatch, and response emission."""

    def __init__(self, server: RequestPipelineServer) -> None:
        self._server = server

    def process(
        self,
        data: bytes,
        client_socket: socket.socket,
        client_address: tuple[str, int],
        request_num: int,
    ) -> bool:
        """Process one request and return ``True`` when the connection should stay open."""
        start_time = time.monotonic()
        request_id = secrets.token_hex(4)
        build_args: ResponseBuildArgs = {
            "opsec_mode": self._server.opsec_mode,
            "cors_origin": self._server.cors_origin,
        }

        try:
            request = HTTPRequest(data)
            use_keep_alive, remaining = self._server._resolve_keep_alive(request, request_num)
            build_args["keep_alive"] = use_keep_alive
            if use_keep_alive:
                build_args["keep_alive_timeout"] = self._server.KEEP_ALIVE_TIMEOUT
                build_args["keep_alive_max"] = remaining

            auth_error = self._server._authenticate_request(request, client_address)
            if auth_error is not None:
                self._send_direct_response(auth_error, client_socket, build_args)
                return False

            if self._server._is_websocket_upgrade_attempt(request):
                return self._process_websocket_upgrade(request, client_socket, build_args)

            size_error = self._server._check_payload_size(request)
            if size_error is not None:
                self._send_direct_response(size_error, client_socket, build_args)
                return False

            response = self._server._dispatch_handler(request)
            self._server._post_process_response(request, response, request_id)

            bytes_sent = self._server._send_response(response, client_socket, build_args)
            self._server._record_metric(response.status_code, bytes_sent)

            if response.stream_path is not None:
                use_keep_alive = False

            if not self._server.opsec_mode:
                duration_ms = (time.monotonic() - start_time) * 1000
                logger.info(
                    "[%s] %s - %s %s -> %d (%dms)",
                    request_id,
                    client_address[0],
                    request.method,
                    request.path,
                    response.status_code,
                    duration_ms,
                )

            return use_keep_alive

        except Exception:
            logger.exception(
                "[%s] Request handling error from %s",
                request_id,
                client_address[0],
            )
            self._server._record_metric(500, 0, error=True)
            message = "Error" if self._server.opsec_mode else "Internal Server Error"
            error_response = self._server._build_error_response(500, message)
            try:
                client_socket.sendall(error_response.build(**build_args))
            except Exception:
                pass
            return False

    def _send_direct_response(
        self,
        response: HTTPResponse,
        client_socket: socket.socket,
        build_args: ResponseBuildArgs,
    ) -> None:
        """Send a direct response outside the normal response pipeline and record metrics."""
        payload = response.build(**build_args)
        client_socket.sendall(payload)
        self._server._record_metric(response.status_code, len(payload))

    def _process_websocket_upgrade(
        self,
        request: HTTPRequest,
        client_socket: socket.socket,
        build_args: ResponseBuildArgs,
    ) -> bool:
        """Validate and dispatch the Secure Notepad WebSocket upgrade path."""
        if not check_websocket_upgrade(request):
            response = self._server._build_error_response(
                400,
                "Invalid WebSocket upgrade request",
            )
            self._send_direct_response(response, client_socket, build_args)
            return False

        if not self._server._is_websocket_origin_allowed(request):
            response = self._server._build_error_response(403, "Forbidden WebSocket origin")
            self._send_direct_response(response, client_socket, build_args)
            return False

        if self._server._ecdh_manager is None:
            response = self._server._build_error_response(
                501,
                "Secure Notepad requires the cryptography package; install exphttp[crypto]",
            )
            self._send_direct_response(response, client_socket, build_args)
            return False

        self._server._handle_notepad_ws(client_socket, request)
        return False


__all__ = ["RequestPipeline", "RequestPipelineServer", "ResponseBuildArgs"]
