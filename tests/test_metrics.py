"""Tests for src.metrics.MetricsCollector."""

from __future__ import annotations

import threading

import pytest

from src.metrics import MetricsCollector


class TestMetricsCollector:
    def test_snapshot_on_fresh_collector_is_zero(self) -> None:
        m = MetricsCollector()
        snap = m.snapshot()

        assert snap["total_requests"] == 0
        assert snap["total_errors"] == 0
        assert snap["client_errors"] == 0
        assert snap["server_errors"] == 0
        assert snap["bytes_sent"] == 0
        assert snap["bytes_received"] == 0
        assert snap["status_counts"] == {}
        assert snap["receive_rejections"] == {}
        assert snap["connections"] == {"active": 0, "accepted": 0, "closed": 0}
        assert snap["receive"] == {
            "bytes": 0,
            "rejections": 0,
            "rejection_reasons": {},
        }
        assert snap["timeouts"] == {}
        assert snap["request_latency_ms"] == {
            "count": 0,
            "total": 0.0,
            "avg": 0.0,
            "max": 0.0,
        }
        assert snap["request_admission"] == {"active": 0, "accepted": 0, "rejected": 0}
        assert snap["websocket"] == {
            "active": 0,
            "rejected_admissions": 0,
            "closed": 0,
            "protocol_errors": 0,
            "message_too_big": 0,
            "incomplete_frame_timeouts": 0,
            "idle_pings": 0,
            "errors": 0,
        }
        assert snap["worker"] == {
            "exceptions": 0,
            "exception_sources": {},
            "last_exception_type": None,
        }
        assert snap["uptime_seconds"] == 0

    def test_mark_started_enables_uptime(self) -> None:
        m = MetricsCollector()
        m.mark_started()

        snap = m.snapshot()
        assert isinstance(snap["uptime_seconds"], float)
        # uptime is >= 0; exact value depends on timing
        assert snap["uptime_seconds"] >= 0

    def test_record_increments_counters(self) -> None:
        m = MetricsCollector()
        m.record(200, 100)
        m.record(200, 50)
        m.record(404, 30)
        m.record(500, 0)

        snap = m.snapshot()
        assert snap["total_requests"] == 4
        assert snap["total_errors"] == 1
        assert snap["client_errors"] == 1
        assert snap["server_errors"] == 1
        assert snap["bytes_sent"] == 180
        assert snap["status_counts"] == {200: 2, 404: 1, 500: 1}

    def test_snapshot_returns_defensive_copy(self) -> None:
        m = MetricsCollector()
        m.record(200, 10)
        m.record_receive_rejection("header_too_large")
        m.record_worker_exception("handle_client", RuntimeError("boom"))

        snap = m.snapshot()
        assert isinstance(snap["status_counts"], dict)
        snap["status_counts"][500] = 999
        snap["receive_rejections"]["body_too_large"] = 999  # type: ignore[index]
        snap["receive"]["rejection_reasons"]["body_too_large"] = 999  # type: ignore[index]
        snap["worker"]["exception_sources"]["worker_future"] = 999  # type: ignore[index]

        # Original state must not be affected
        snap2 = m.snapshot()
        assert snap2["status_counts"] == {200: 1}
        assert snap2["receive_rejections"] == {"header_too_large": 1}
        assert snap2["receive"] == {
            "bytes": 0,
            "rejections": 1,
            "rejection_reasons": {"header_too_large": 1},
        }
        assert snap2["worker"] == {
            "exceptions": 1,
            "exception_sources": {"handle_client": 1},
            "last_exception_type": "RuntimeError",
        }

    def test_receive_rejection_counts_are_isolated(self) -> None:
        m = MetricsCollector()
        m.record_receive_rejection("header_too_large")
        m.record_receive_rejection("header_too_large")
        m.record_receive_rejection("body_too_large")

        snap = m.snapshot()
        assert snap["receive_rejections"] == {
            "header_too_large": 2,
            "body_too_large": 1,
        }
        assert snap["receive"] == {
            "bytes": 0,
            "rejections": 3,
            "rejection_reasons": {
                "header_too_large": 2,
                "body_too_large": 1,
            },
        }

    def test_error_counters_are_status_based(self) -> None:
        m = MetricsCollector()
        m.record(404, 10)
        m.record(500, 0)
        m.record(503, 0, error=True)

        snap = m.snapshot()
        assert snap["client_errors"] == 1
        assert snap["server_errors"] == 2
        assert snap["total_errors"] == snap["server_errors"]
        assert snap["status_counts"] == {404: 1, 500: 1, 503: 1}

    def test_error_flag_counts_exceptional_server_failures(self) -> None:
        m = MetricsCollector()
        m.record(200, 0, error=True)

        snap = m.snapshot()
        assert snap["total_errors"] == 1
        assert snap["client_errors"] == 0
        assert snap["server_errors"] == 1
        assert snap["status_counts"] == {200: 1}

    def test_concurrent_record_is_thread_safe(self) -> None:
        m = MetricsCollector()

        def worker() -> None:
            for _ in range(1000):
                m.record(200, 1)

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        snap = m.snapshot()
        assert snap["total_requests"] == 8 * 1000
        assert snap["bytes_sent"] == 8 * 1000

    @pytest.mark.parametrize("status", [200, 301, 404, 500])
    def test_status_buckets_are_isolated(self, status: int) -> None:
        m = MetricsCollector()
        m.record(status, 10)

        snap = m.snapshot()
        counts: dict[int, int] = snap["status_counts"]  # type: ignore[assignment]
        assert counts == {status: 1}

    def test_websocket_counters_are_thread_safe(self) -> None:
        m = MetricsCollector()
        m.record_websocket_opened()
        m.record_websocket_opened()
        m.record_websocket_rejected()
        m.record_websocket_protocol_error()
        m.record_websocket_message_too_big()
        m.record_websocket_incomplete_frame_timeout()
        m.record_websocket_idle_ping()
        m.record_websocket_error()
        m.record_websocket_closed()

        snap = m.snapshot()
        assert snap["websocket"] == {
            "active": 1,
            "rejected_admissions": 1,
            "closed": 1,
            "protocol_errors": 1,
            "message_too_big": 1,
            "incomplete_frame_timeouts": 1,
            "idle_pings": 1,
            "errors": 1,
        }

    def test_request_admission_counters_are_thread_safe(self) -> None:
        m = MetricsCollector()
        m.record_request_admission_accepted()
        m.record_request_admission_accepted()
        m.record_request_admission_rejected()
        m.record_request_admission_released()

        snap = m.snapshot()
        assert snap["request_admission"] == {
            "active": 1,
            "accepted": 2,
            "rejected": 1,
        }

    def test_connection_latency_timeout_and_worker_counters(self) -> None:
        m = MetricsCollector()
        m.record_connection_opened()
        m.record_connection_opened()
        m.record_connection_closed()
        m.record_bytes_received(100)
        m.record_bytes_received(23)
        m.record_request_latency(10.0)
        m.record_request_latency(30.0)
        m.record_timeout("websocket_incomplete_frame")
        m.record_receive_rejection("header_timeout")
        m.record_worker_exception("handle_client", RuntimeError("boom"))

        snap = m.snapshot()
        assert snap["connections"] == {"active": 1, "accepted": 2, "closed": 1}
        assert snap["bytes_received"] == 123
        assert snap["receive"]["bytes"] == 123  # type: ignore[index]
        assert snap["request_latency_ms"] == {
            "count": 2,
            "total": 40.0,
            "avg": 20.0,
            "max": 30.0,
        }
        assert snap["timeouts"] == {
            "websocket_incomplete_frame": 1,
            "header_timeout": 1,
        }
        assert snap["worker"] == {
            "exceptions": 1,
            "exception_sources": {"handle_client": 1},
            "last_exception_type": "RuntimeError",
        }

    def test_concurrent_operational_updates_are_thread_safe(self) -> None:
        m = MetricsCollector()

        def worker() -> None:
            for _ in range(250):
                m.record(200, 1)
                m.record_bytes_received(2)
                m.record_connection_opened()
                m.record_connection_closed()
                m.record_receive_rejection("body_timeout")
                m.record_request_admission_accepted()
                m.record_request_admission_released()
                m.record_request_admission_rejected()
                m.record_request_latency(1.5)
                m.record_websocket_opened()
                m.record_websocket_closed()
                m.record_websocket_rejected()
                m.record_timeout("websocket_incomplete_frame")
                m.record_worker_exception("worker_future", RuntimeError("boom"))

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        snap = m.snapshot()
        assert snap["total_requests"] == 1000
        assert snap["bytes_sent"] == 1000
        assert snap["bytes_received"] == 2000
        assert snap["connections"] == {"active": 0, "accepted": 1000, "closed": 1000}
        assert snap["receive_rejections"] == {"body_timeout": 1000}
        assert snap["timeouts"] == {
            "body_timeout": 1000,
            "websocket_incomplete_frame": 1000,
        }
        assert snap["request_admission"] == {
            "active": 0,
            "accepted": 1000,
            "rejected": 1000,
        }
        assert snap["request_latency_ms"] == {
            "count": 1000,
            "total": 1500.0,
            "avg": 1.5,
            "max": 1.5,
        }
        assert snap["websocket"]["active"] == 0  # type: ignore[index]
        assert snap["websocket"]["closed"] == 1000  # type: ignore[index]
        assert snap["websocket"]["rejected_admissions"] == 1000  # type: ignore[index]
        assert snap["worker"] == {
            "exceptions": 1000,
            "exception_sources": {"worker_future": 1000},
            "last_exception_type": "RuntimeError",
        }
