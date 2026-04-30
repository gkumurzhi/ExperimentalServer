"""Thread-safe in-memory metrics collector."""

import threading
import time


class MetricsCollector:
    """Aggregates request-level counters and exposes snapshots.

    Thread-safe: every mutation holds a single lock.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._start_time: float = 0.0
        self._request_count: int = 0
        self._error_count: int = 0
        self._bytes_sent: int = 0
        self._status_counts: dict[int, int] = {}
        self._websocket_active: int = 0
        self._websocket_rejected_admissions: int = 0

    def mark_started(self) -> None:
        """Mark the moment the server began accepting connections."""
        self._start_time = time.monotonic()

    def record(self, status_code: int, response_size: int, *, error: bool = False) -> None:
        """Record a single completed request."""
        with self._lock:
            self._request_count += 1
            self._bytes_sent += response_size
            self._status_counts[status_code] = self._status_counts.get(status_code, 0) + 1
            if error:
                self._error_count += 1

    def record_websocket_opened(self) -> None:
        """Record a WebSocket connection admitted by the server."""
        with self._lock:
            self._websocket_active += 1

    def record_websocket_closed(self) -> None:
        """Record a WebSocket connection leaving the active set."""
        with self._lock:
            self._websocket_active = max(0, self._websocket_active - 1)

    def record_websocket_rejected(self) -> None:
        """Record a WebSocket admission rejected by the resource budget."""
        with self._lock:
            self._websocket_rejected_admissions += 1

    def snapshot(self) -> dict[str, object]:
        """Return a read-only view of current metrics."""
        with self._lock:
            uptime = time.monotonic() - self._start_time if self._start_time else 0.0
            return {
                "uptime_seconds": round(uptime, 1),
                "total_requests": self._request_count,
                "total_errors": self._error_count,
                "bytes_sent": self._bytes_sent,
                "status_counts": dict(self._status_counts),
                "websocket": {
                    "active": self._websocket_active,
                    "rejected_admissions": self._websocket_rejected_admissions,
                },
            }
