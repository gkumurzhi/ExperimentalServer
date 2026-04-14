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
        assert snap["bytes_sent"] == 0
        assert snap["status_counts"] == {}
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
        m.record(404, 30, error=True)

        snap = m.snapshot()
        assert snap["total_requests"] == 3
        assert snap["total_errors"] == 1
        assert snap["bytes_sent"] == 180
        assert snap["status_counts"] == {200: 2, 404: 1}

    def test_snapshot_returns_defensive_copy(self) -> None:
        m = MetricsCollector()
        m.record(200, 10)

        snap = m.snapshot()
        assert isinstance(snap["status_counts"], dict)
        snap["status_counts"][500] = 999

        # Original state must not be affected
        snap2 = m.snapshot()
        assert snap2["status_counts"] == {200: 1}

    def test_error_flag_only_counts_on_true(self) -> None:
        m = MetricsCollector()
        m.record(500, 0)
        m.record(500, 0, error=True)

        snap = m.snapshot()
        assert snap["total_errors"] == 1
        assert snap["status_counts"][500] == 2

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
