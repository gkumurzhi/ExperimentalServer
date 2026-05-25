"""Socket I/O for HTTP: framing, timeouts, and Content-Length enforcement.

Kept separate from the main server loop so that protocol framing can be
unit-tested against in-memory sockets without starting a full server.
"""

from __future__ import annotations

import logging
import socket
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
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
    "body_incomplete",
    "unsupported_transfer_encoding",
    "invalid_content_length",
    "body_memory_budget_exceeded",
]
ReceiveRejectCallback = Callable[[ReceiveRejectionReason], None]


class BodyMemoryBudget:
    """Thread-safe process-wide budget for declared request body bytes."""

    def __init__(self, max_bytes: int) -> None:
        if max_bytes <= 0:
            raise ValueError("body_memory_budget must be greater than 0")
        self.max_bytes = max_bytes
        self._lock = threading.Lock()
        self._current_bytes = 0
        self._peak_bytes = 0
        self._rejected = 0

    def try_reserve(self, byte_count: int) -> BodyMemoryReservation | None:
        """Reserve body bytes or return ``None`` when the process budget is full."""
        if byte_count < 0:
            raise ValueError("byte_count must be at least 0")
        if byte_count == 0:
            return None

        with self._lock:
            if self._current_bytes + byte_count > self.max_bytes:
                self._rejected += 1
                return None
            self._current_bytes += byte_count
            self._peak_bytes = max(self._peak_bytes, self._current_bytes)
        return BodyMemoryReservation(self, byte_count)

    def _release(self, byte_count: int) -> None:
        with self._lock:
            self._current_bytes = max(0, self._current_bytes - byte_count)

    def snapshot(self) -> dict[str, int]:
        """Return current body-budget counters."""
        with self._lock:
            return {
                "max_bytes": self.max_bytes,
                "current_bytes": self._current_bytes,
                "peak_bytes": self._peak_bytes,
                "rejected": self._rejected,
            }


class BodyMemoryReservation:
    """Idempotent handle for a body-memory reservation."""

    def __init__(self, budget: BodyMemoryBudget, byte_count: int) -> None:
        self.budget = budget
        self.byte_count = byte_count
        self._lock = threading.Lock()
        self._released = False

    def release(self) -> None:
        """Release this reservation once."""
        with self._lock:
            if self._released:
                return
            self._released = True
        self.budget._release(self.byte_count)


@dataclass
class RequestReceiveResult:
    """Raw request bytes plus any body-memory reservation held for processing."""

    data: bytes
    body_reservation: BodyMemoryReservation | None = None
    rejection_reason: ReceiveRejectionReason | None = None

    def release_body_reservation(self) -> None:
        """Release the held body reservation, if any."""
        if self.body_reservation is None:
            return
        self.body_reservation.release()
        self.body_reservation = None


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
    return receive_request_result(
        client_socket,
        max_upload_size=max_upload_size,
        max_header_size=max_header_size,
        idle_timeout=idle_timeout,
        on_reject=on_reject,
    ).data


def receive_request_result(
    client_socket: socket.socket,
    *,
    max_upload_size: int,
    max_header_size: int = DEFAULT_MAX_HEADER_SIZE,
    idle_timeout: float | None = None,
    on_reject: ReceiveRejectCallback | None = None,
    body_memory_budget: BodyMemoryBudget | None = None,
) -> RequestReceiveResult:
    """Read one complete HTTP request and hold any body-memory reservation.

    The reservation is intentionally returned to the caller instead of released
    here because the raw request bytes and parsed ``HTTPRequest.body`` remain
    live until request processing finishes.
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
    body_reservation: BodyMemoryReservation | None = None

    def reject(reason: ReceiveRejectionReason) -> RequestReceiveResult:
        nonlocal body_reservation
        _record_rejection(on_reject, reason)
        if body_reservation is not None:
            body_reservation.release()
            body_reservation = None
        return RequestReceiveResult(b"", rejection_reason=reason)

    try:
        while True:
            elapsed = time.monotonic() - start_time
            if not headers_received and elapsed > HEADER_TIMEOUT:
                logger.warning("Header receive timeout (%.0fs)", elapsed)
                return reject("header_timeout")
            if headers_received and elapsed > HEADER_TIMEOUT + BODY_TIMEOUT:
                logger.warning("Body receive timeout (%.0fs)", elapsed)
                return reject("body_timeout")

            try:
                recv_size = RECV_CHUNK
                if not headers_received:
                    header_probe_limit = max_header_size + len(HEADER_TERMINATOR)
                    recv_size = min(RECV_CHUNK, max(1, header_probe_limit - total_size))
                else:
                    body_received = total_size - header_end_pos - len(HEADER_TERMINATOR)
                    if body_received >= content_length:
                        break
                    recv_size = min(RECV_CHUNK, max(1, content_length - body_received))

                chunk = client_socket.recv(recv_size)
                if not chunk:
                    if headers_received:
                        body_received = total_size - header_end_pos - len(HEADER_TERMINATOR)
                        if body_received < content_length:
                            logger.warning(
                                "Request body incomplete (%d bytes < %d bytes), dropping",
                                body_received,
                                content_length,
                            )
                            return reject("body_incomplete")
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
                            logger.warning(
                                "Request headers too large (%d bytes > %d bytes), dropping",
                                header_end_pos,
                                max_header_size,
                            )
                            return reject("header_too_large")
                        headers_part = data[:header_end_pos].decode("utf-8", errors="replace")
                        if _has_transfer_encoding(headers_part):
                            logger.warning("Transfer-Encoding is not supported; dropping request")
                            return reject("unsupported_transfer_encoding")
                        parsed = _parse_content_length(headers_part)
                        if parsed is None:
                            return reject("invalid_content_length")
                        content_length = parsed
                        if content_length > max_upload_size:
                            logger.warning(
                                "Declared Content-Length too large (%d bytes > %d bytes), dropping",
                                content_length,
                                max_upload_size,
                            )
                            return reject("body_too_large")
                        if content_length > 0 and body_memory_budget is not None:
                            body_reservation = body_memory_budget.try_reserve(content_length)
                            if body_reservation is None:
                                logger.warning(
                                    "Request body memory budget exceeded "
                                    "(declared=%d bytes, budget=%d bytes)",
                                    content_length,
                                    body_memory_budget.max_bytes,
                                )
                                return reject("body_memory_budget_exceeded")
                        headers_received = True
                        body_received = total_size - header_end_pos - len(HEADER_TERMINATOR)
                        if body_received > max_upload_size:
                            logger.warning(
                                "Request body too large (%d bytes), dropping",
                                body_received,
                            )
                            return reject("body_too_large")
                        if body_received >= content_length:
                            break
                    elif len(data) > max_header_size + len(HEADER_TERMINATOR) - 1:
                        logger.warning(
                            "Request headers too large (>%d bytes), dropping",
                            max_header_size,
                        )
                        return reject("header_too_large")
                else:
                    body_received = total_size - header_end_pos - len(HEADER_TERMINATOR)
                    if body_received > max_upload_size:
                        logger.warning("Request body too large (%d bytes), dropping", body_received)
                        return reject("body_too_large")
                    if body_received >= content_length:
                        break

            except TimeoutError:
                if not headers_received:
                    break
                continue

        result = b"".join(chunks)
        if headers_received:
            expected_size = header_end_pos + len(HEADER_TERMINATOR) + content_length
            result = result[:expected_size]
        if result:
            logger.debug("Received %d bytes", len(result))
        return RequestReceiveResult(result, body_reservation=body_reservation)
    except BaseException:
        if body_reservation is not None:
            body_reservation.release()
            body_reservation = None
        raise
