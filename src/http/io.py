"""Socket I/O for HTTP: framing, timeouts, and Content-Length enforcement.

Kept separate from the main server loop so that protocol framing can be
unit-tested against in-memory sockets without starting a full server.
"""

from __future__ import annotations

import logging
import socket
import time
from collections.abc import Callable
from typing import Literal

logger = logging.getLogger("httpserver")

HEADER_TIMEOUT = 30.0
BODY_TIMEOUT = 300.0
DEFAULT_IDLE_TIMEOUT = 5.0
DEFAULT_MAX_HEADER_SIZE = 64 * 1024
RECV_CHUNK = 65536
HEADER_TERMINATOR = b"\r\n\r\n"

ReceiveRejectionReason = Literal[
    "header_too_large",
    "body_too_large",
    "header_timeout",
    "body_timeout",
    "unsupported_transfer_encoding",
    "invalid_content_length",
]
ReceiveRejectCallback = Callable[[ReceiveRejectionReason], None]


def _record_rejection(
    on_reject: ReceiveRejectCallback | None,
    reason: ReceiveRejectionReason,
) -> None:
    if on_reject is None:
        return
    try:
        on_reject(reason)
    except Exception:
        logger.exception("Receive rejection callback failed")


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


def _has_transfer_encoding(headers_part: str) -> bool:
    """Return True when the request advertises any Transfer-Encoding."""
    for line in headers_part.split("\r\n"):
        if line.lower().startswith("transfer-encoding:"):
            return True
    return False


def receive_request(
    client_socket: socket.socket,
    *,
    max_upload_size: int,
    max_header_size: int = DEFAULT_MAX_HEADER_SIZE,
    idle_timeout: float | None = None,
    on_reject: ReceiveRejectCallback | None = None,
) -> bytes:
    """Read one complete HTTP request from ``client_socket``.

    Returns the raw request bytes or an empty ``bytes`` on any framing error
    (timeout, oversized headers/body, conflicting Content-Length). The caller is
    responsible for closing the socket when empty is returned.

    Args:
        client_socket: Accepted (and optionally TLS-wrapped) client socket.
        max_upload_size: Hard cap on request body bytes.
        max_header_size: Hard cap on request header bytes before ``\\r\\n\\r\\n``.
        idle_timeout: Initial timeout for the first ``recv`` (used by
            keep-alive loops waiting for the next request). ``None`` uses the
            default 5 s.
        on_reject: Optional callback invoked with the receive-layer rejection reason.
    """
    if max_upload_size <= 0:
        raise ValueError("max_upload_size must be greater than 0")
    if max_header_size <= 0:
        raise ValueError("max_header_size must be greater than 0")

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
            _record_rejection(on_reject, "header_timeout")
            logger.warning("Header receive timeout (%.0fs)", elapsed)
            return b""
        if headers_received and elapsed > HEADER_TIMEOUT + BODY_TIMEOUT:
            _record_rejection(on_reject, "body_timeout")
            logger.warning("Body receive timeout (%.0fs)", elapsed)
            return b""

        try:
            recv_size = RECV_CHUNK
            if not headers_received:
                header_probe_limit = max_header_size + len(HEADER_TERMINATOR)
                recv_size = min(RECV_CHUNK, max(1, header_probe_limit - total_size))

            chunk = client_socket.recv(recv_size)
            if not chunk:
                break

            if first_recv and idle_timeout is not None:
                client_socket.settimeout(DEFAULT_IDLE_TIMEOUT)
                first_recv = False

            chunks.append(chunk)
            total_size += len(chunk)

            if not headers_received:
                data = b"".join(chunks)
                header_end_pos = data.find(HEADER_TERMINATOR)
                if header_end_pos >= 0:
                    if header_end_pos > max_header_size:
                        _record_rejection(on_reject, "header_too_large")
                        logger.warning(
                            "Request headers too large (%d bytes > %d bytes), dropping",
                            header_end_pos,
                            max_header_size,
                        )
                        return b""
                    headers_part = data[:header_end_pos].decode("utf-8", errors="replace")
                    if _has_transfer_encoding(headers_part):
                        _record_rejection(on_reject, "unsupported_transfer_encoding")
                        logger.warning("Transfer-Encoding is not supported; dropping request")
                        return b""
                    parsed = _parse_content_length(headers_part)
                    if parsed is None:
                        _record_rejection(on_reject, "invalid_content_length")
                        return b""
                    content_length = parsed
                    if content_length > max_upload_size:
                        _record_rejection(on_reject, "body_too_large")
                        logger.warning(
                            "Declared Content-Length too large (%d bytes > %d bytes), dropping",
                            content_length,
                            max_upload_size,
                        )
                        return b""
                    headers_received = True
                    body_received = total_size - header_end_pos - len(HEADER_TERMINATOR)
                    if body_received > max_upload_size:
                        _record_rejection(on_reject, "body_too_large")
                        logger.warning("Request body too large (%d bytes), dropping", body_received)
                        return b""
                    if body_received >= content_length:
                        break
                elif len(data) > max_header_size + len(HEADER_TERMINATOR) - 1:
                    _record_rejection(on_reject, "header_too_large")
                    logger.warning(
                        "Request headers too large (>%d bytes), dropping",
                        max_header_size,
                    )
                    return b""
            else:
                body_received = total_size - header_end_pos - len(HEADER_TERMINATOR)
                if body_received > max_upload_size:
                    _record_rejection(on_reject, "body_too_large")
                    logger.warning("Request body too large (%d bytes), dropping", body_received)
                    return b""
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
