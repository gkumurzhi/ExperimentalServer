"""Live server tests for WebSocket upgrade validation."""

from __future__ import annotations

import socket
import threading
import time

from src.server import ExperimentalHTTPServer
from tests.conftest import find_free_port


def _start_server(port: int, disable_ecdh: bool = False) -> ExperimentalHTTPServer:
    server = ExperimentalHTTPServer(
        host="127.0.0.1",
        port=port,
        root_dir="/tmp",
        quiet=True,
    )
    if disable_ecdh:
        server._ecdh_manager = None
    thread = threading.Thread(target=server.start, daemon=True)
    thread.start()
    for _ in range(50):
        time.sleep(0.05)
        if server.running:
            break
    return server


def _send_raw(port: int, raw: bytes, timeout: float = 2.0) -> bytes:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect(("127.0.0.1", port))
        sock.sendall(raw)
        chunks: list[bytes] = []
        while True:
            try:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                chunks.append(chunk)
            except TimeoutError:
                break
        return b"".join(chunks)
    finally:
        sock.close()


class TestWebSocketUpgradeSecurity:
    def test_cross_origin_upgrade_rejected_by_default(self) -> None:
        port = find_free_port()
        server = _start_server(port)
        try:
            raw = (
                f"GET /notes/ws HTTP/1.1\r\n"
                f"Host: 127.0.0.1:{port}\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n"
                "Sec-WebSocket-Version: 13\r\n"
                "Origin: https://evil.example\r\n"
                "\r\n"
            ).encode("ascii")
            response = _send_raw(port, raw)
            assert b"HTTP/1.1 403 Forbidden" in response
        finally:
            server.stop()

    def test_invalid_websocket_version_rejected(self) -> None:
        port = find_free_port()
        server = _start_server(port)
        try:
            raw = (
                f"GET /notes/ws HTTP/1.1\r\n"
                f"Host: 127.0.0.1:{port}\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n"
                "Sec-WebSocket-Version: 12\r\n"
                f"Origin: http://127.0.0.1:{port}\r\n"
                "\r\n"
            ).encode("ascii")
            response = _send_raw(port, raw)
            assert b"HTTP/1.1 400 Bad Request" in response
        finally:
            server.stop()

    def test_same_origin_upgrade_accepted(self) -> None:
        port = find_free_port()
        server = _start_server(port)
        try:
            raw = (
                f"GET /notes/ws HTTP/1.1\r\n"
                f"Host: 127.0.0.1:{port}\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n"
                "Sec-WebSocket-Version: 13\r\n"
                f"Origin: http://127.0.0.1:{port}\r\n"
                "\r\n"
            ).encode("ascii")
            response = _send_raw(port, raw)
            assert b"HTTP/1.1 101 Switching Protocols" in response
        finally:
            server.stop()

    def test_upgrade_rejected_when_notepad_crypto_unavailable(self) -> None:
        port = find_free_port()
        server = _start_server(port, disable_ecdh=True)
        try:
            raw = (
                f"GET /notes/ws HTTP/1.1\r\n"
                f"Host: 127.0.0.1:{port}\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n"
                "Sec-WebSocket-Version: 13\r\n"
                f"Origin: http://127.0.0.1:{port}\r\n"
                "\r\n"
            ).encode("ascii")
            response = _send_raw(port, raw)
            assert b"HTTP/1.1 501 Not Implemented" in response
        finally:
            server.stop()
