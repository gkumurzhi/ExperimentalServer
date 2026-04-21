"""Tests for src.http.io.receive_request and header framing guards."""

from __future__ import annotations

import socket
import threading
import time

import pytest

from src.http.io import _has_transfer_encoding, _parse_content_length, receive_request


class TestParseContentLength:
    def test_returns_zero_when_header_absent(self) -> None:
        assert _parse_content_length("Host: x\r\nConnection: close") == 0

    def test_returns_parsed_value(self) -> None:
        assert _parse_content_length("Host: x\r\nContent-Length: 42") == 42

    def test_rejects_negative_value(self) -> None:
        assert _parse_content_length("Content-Length: -1") is None

    def test_rejects_non_integer(self) -> None:
        assert _parse_content_length("Content-Length: abc") is None

    def test_rejects_conflicting_values(self) -> None:
        """Duplicate Content-Length with different values is an HTTP smuggling vector."""
        assert _parse_content_length("Content-Length: 10\r\nContent-Length: 20") is None

    def test_accepts_duplicate_same_value(self) -> None:
        """Duplicate but identical Content-Length is permitted by RFC 7230."""
        assert _parse_content_length("Content-Length: 10\r\nContent-Length: 10") == 10

    def test_case_insensitive(self) -> None:
        assert _parse_content_length("content-length: 5") == 5
        assert _parse_content_length("CONTENT-LENGTH: 7") == 7


class TestTransferEncodingDetection:
    def test_detects_transfer_encoding(self) -> None:
        headers = "Host: x\r\nTransfer-Encoding: chunked\r\nConnection: close"
        assert _has_transfer_encoding(headers) is True

    def test_case_insensitive(self) -> None:
        headers = "Host: x\r\nTRANSFER-ENCODING: chunked"
        assert _has_transfer_encoding(headers) is True

    def test_absent_header_returns_false(self) -> None:
        headers = "Host: x\r\nContent-Length: 0"
        assert _has_transfer_encoding(headers) is False


@pytest.fixture
def socket_pair() -> tuple[socket.socket, socket.socket]:
    server, client = socket.socketpair()
    yield server, client
    server.close()
    client.close()


class TestReceiveRequest:
    def test_reads_simple_get_request(
        self,
        socket_pair: tuple[socket.socket, socket.socket],
    ) -> None:
        server, client = socket_pair
        request = b"GET / HTTP/1.1\r\nHost: x\r\n\r\n"
        client.sendall(request)

        result = receive_request(server, max_upload_size=1024 * 1024)
        assert result == request

    def test_reads_request_with_body(
        self,
        socket_pair: tuple[socket.socket, socket.socket],
    ) -> None:
        server, client = socket_pair
        body = b"a=1&b=2"
        request = (
            f"POST /form HTTP/1.1\r\nHost: x\r\nContent-Length: {len(body)}\r\n\r\n"
        ).encode() + body
        client.sendall(request)

        result = receive_request(server, max_upload_size=1024 * 1024)
        assert result == request

    def test_rejects_request_exceeding_size_limit(
        self,
        socket_pair: tuple[socket.socket, socket.socket],
    ) -> None:
        server, client = socket_pair
        body = b"A" * (200 * 1024)  # 200 KB
        request = (
            f"POST / HTTP/1.1\r\nHost: x\r\nContent-Length: {len(body)}\r\n\r\n"
        ).encode() + body

        # Send in a background thread so we don't deadlock on the buffer
        def sender() -> None:
            try:
                client.sendall(request)
            except OSError:
                pass

        t = threading.Thread(target=sender)
        t.start()

        result = receive_request(server, max_upload_size=64 * 1024)
        t.join(timeout=2)

        assert result == b""

    def test_rejects_conflicting_content_length(
        self,
        socket_pair: tuple[socket.socket, socket.socket],
    ) -> None:
        server, client = socket_pair
        request = (
            b"POST / HTTP/1.1\r\nHost: x\r\nContent-Length: 5\r\nContent-Length: 10\r\n\r\nhello"
        )
        client.sendall(request)

        result = receive_request(server, max_upload_size=1024 * 1024)
        assert result == b""

    def test_rejects_transfer_encoding_without_content_length(
        self,
        socket_pair: tuple[socket.socket, socket.socket],
    ) -> None:
        server, client = socket_pair
        request = (
            b"POST / HTTP/1.1\r\nHost: x\r\nTransfer-Encoding: chunked\r\n\r\n"
            b"5\r\nhello\r\n0\r\n\r\n"
        )
        client.sendall(request)

        result = receive_request(server, max_upload_size=1024 * 1024)
        assert result == b""

    def test_rejects_transfer_encoding_with_content_length(
        self,
        socket_pair: tuple[socket.socket, socket.socket],
    ) -> None:
        server, client = socket_pair
        request = (
            b"POST / HTTP/1.1\r\nHost: x\r\nContent-Length: 5\r\n"
            b"Transfer-Encoding: chunked\r\n\r\n5\r\nhello\r\n0\r\n\r\n"
        )
        client.sendall(request)

        result = receive_request(server, max_upload_size=1024 * 1024)
        assert result == b""

    def test_timeout_when_no_data(
        self,
        socket_pair: tuple[socket.socket, socket.socket],
    ) -> None:
        server, _client = socket_pair
        # Don't send anything; receiver should time out and return empty
        start = time.monotonic()
        result = receive_request(server, max_upload_size=1024 * 1024, idle_timeout=0.1)
        elapsed = time.monotonic() - start

        assert result == b""
        assert elapsed < 2.0  # quick timeout, not the 30 s header budget
