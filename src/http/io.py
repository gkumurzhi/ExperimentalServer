"""Socket I/O for HTTP: framing, timeouts, and Content-Length enforcement.

Kept separate from the main server loop so that protocol framing can be
unit-tested against in-memory sockets without starting a full server.
"""

from __future__ import annotations

import logging
import socket
import time

logger = logging.getLogger("httpserver")

HEADER_TIMEOUT = 30.0
BODY_TIMEOUT = 300.0
DEFAULT_IDLE_TIMEOUT = 5.0
RECV_CHUNK = 65536


def _parse_content_length(headers_part: str) -> int | None:
    """Return a single non-negative Content-Length, or ``None`` on conflict/parse error.

    Detects HTTP smuggling attempts via duplicate differing Content-Length headers.
    """
    values: list[int] = []
    for line in headers_part.split("\r\n"):
        if line.lower().startswith("content-length:"):
            try:
                values.append(int(line.split(":", 1)[1].strip()))
            except ValueError:
                return None
    if not values:
        return 0
    if len(set(values)) > 1 or values[0] < 0:
        return None
    return values[0]


def receive_request(
    client_socket: socket.socket,
    *,
    max_upload_size: int,
    idle_timeout: float | None = None,
) -> bytes:
    """Read one complete HTTP request from ``client_socket``.

    Returns the raw request bytes or an empty ``bytes`` on any framing error
    (timeout, oversized body, conflicting Content-Length). The caller is
    responsible for closing the socket when empty is returned.

    Args:
        client_socket: Accepted (and optionally TLS-wrapped) client socket.
        max_upload_size: Hard cap on total request bytes.
        idle_timeout: Initial timeout for the first ``recv`` (used by
            keep-alive loops waiting for the next request). ``None`` uses the
            default 5 s.
    """
    chunks: list[bytes] = []
    total_size = 0
    start_time = time.monotonic()

    initial_timeout = idle_timeout if idle_timeout is not None else DEFAULT_IDLE_TIMEOUT
    client_socket.settimeout(initial_timeout)

    headers_received = False
    content_length = 0
    header_end_pos = 0
    first_recv = True

    while True:
        elapsed = time.monotonic() - start_time
        if not headers_received and elapsed > HEADER_TIMEOUT:
            logger.warning("Header receive timeout (%.0fs)", elapsed)
            return b""
        if headers_received and elapsed > HEADER_TIMEOUT + BODY_TIMEOUT:
            logger.warning("Body receive timeout (%.0fs)", elapsed)
            return b""

        try:
            chunk = client_socket.recv(RECV_CHUNK)
            if not chunk:
                break

            if first_recv and idle_timeout is not None:
                client_socket.settimeout(DEFAULT_IDLE_TIMEOUT)
                first_recv = False

            chunks.append(chunk)
            total_size += len(chunk)

            if total_size > max_upload_size + RECV_CHUNK:
                logger.warning("Request too large (%d bytes), dropping", total_size)
                return b""

            if not headers_received:
                data = b"".join(chunks)
                if b"\r\n\r\n" in data:
                    header_end_pos = data.find(b"\r\n\r\n")
                    headers_part = data[:header_end_pos].decode("utf-8", errors="replace")
                    parsed = _parse_content_length(headers_part)
                    if parsed is None:
                        return b""
                    content_length = parsed
                    headers_received = True
                    body_received = total_size - header_end_pos - 4
                    if body_received >= content_length:
                        break
            else:
                body_received = total_size - header_end_pos - 4
                if body_received >= content_length:
                    break

        except TimeoutError:
            if not headers_received:
                break
            continue

    result = b"".join(chunks)
    if result:
        logger.debug("Received %d bytes", len(result))
    return result
