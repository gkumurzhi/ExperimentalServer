# performance-engineer Report
_Generated: 2026-06-15 00:27:59 Europe/Moscow_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/analysis-plan.md_

## Summary
The nested `performance-engineer` subagent was spawned but could not read files because its sandbox failed with `bwrap: loopback: Failed RTM_NEWADDR: Operation not permitted`. I completed the report in-process from read-only inspection of the plan, prior reports, and relevant code. No files were modified and no tests/benchmarks were run.

Highest-risk performance boundary: upload and listing paths are functionally guarded but not yet benchmarked or instrumented enough for capacity planning.

## Documentation Checks
No new Context7 lookup was needed. Recommendations are based on repo-internal Python stdlib behavior and existing pytest/benchmark setup. Parent checks already covered pytest and Docker in [analysis-plan.md](/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/analysis-plan.md:67).

`pytest-benchmark` is available in test extras, but I found no current benchmark files: [pyproject.toml](/home/user/PycharmProjects/ExperimentalHTTPServer/pyproject.toml:62).

## Detailed Findings
Hot paths needing benchmarks before wider use:

- Upload receive/parse/publish: request bodies are fully accumulated in memory in [src/http/io.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/http/io.py:231), joined in [src/http/io.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/http/io.py:423), parsed/split again in [src/http/request.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/http/request.py:39), then written through `publish_bytes` in [src/handlers/files.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/files.py:436).
- Upload quota/publish path: `publish_bytes()` reserves, writes, re-checks quota, and links atomically, but quota checks call `current_usage()` which walks `uploads/` recursively: [src/storage.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/storage.py:100), [src/storage.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/storage.py:179).
- Large `INFO` directory listings: pagination is documented, but implementation sorts/materializes all visible entries before slicing: [src/handlers/info.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/info.py:69). Existing tests cover only five files: [tests/test_handlers/test_handler_integration.py](/home/user/PycharmProjects/ExperimentalHTTPServer/tests/test_handlers/test_handler_integration.py:360).
- Notepad save/list quotas: save runs aggregate usage scan under the note lock before writing: [src/notepad_service.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/notepad_service.py:410), [src/notepad_service.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/notepad_service.py:552). Listing is bounded by `max_listed_notes`, but still should be benchmarked near 1,000 notes: [src/notepad_service.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/notepad_service.py:451).
- Slow readers/writers: receive-side timeouts and response-stream deadlines are covered and metered: [tests/test_server_live.py](/home/user/PycharmProjects/ExperimentalHTTPServer/tests/test_server_live.py:293), [tests/test_server_live.py](/home/user/PycharmProjects/ExperimentalHTTPServer/tests/test_server_live.py:339).
- WebSocket slots: active/rejected slot metrics exist and are tested, but slot hold duration and message throughput are not: [src/metrics.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/metrics.py:231), [tests/test_server_live.py](/home/user/PycharmProjects/ExperimentalHTTPServer/tests/test_server_live.py:653).

Measurability:
- Body memory reservation is measurable for admission via `body_memory`, but not true RSS/temporary copies: [src/server.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/server.py:455).
- Disk quotas are not measurable enough; there is no quota-scan latency, current upload usage, or quota-rejection-by-reason metric.
- Large listings are not measurable enough; only total request latency captures them.
- Slow-reader behavior is measurable enough for failures.
- WebSocket slots are measurable for admission, not capacity modeling.

## Issues Found
- [MEDIUM] Upload quota checks scan `uploads/` even when aggregate upload limits are disabled.
  - Evidence: default upload quota is unlimited in [src/server.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/server.py:103), but `publish_bytes()` still calls `_check_accepts()` and `current_usage()` in [src/storage.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/storage.py:149).
  - Impact: upload latency grows with existing file count even for default local usage.
  - Confidence: high.

- [MEDIUM] `INFO` pagination does not bound scan/allocation cost.
  - Evidence: `sorted(file_path.iterdir())` builds all entries before `offset/limit`: [src/handlers/info.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/info.py:70).
  - Impact: a large `uploads/` directory can cause slow responses and memory spikes.
  - Confidence: high.

- [LOW/MEDIUM] `/metrics` has latency avg/max but no distribution or phase timings.
  - Evidence: only count/total/avg/max are tracked: [src/metrics.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/metrics.py:85), [src/metrics.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/metrics.py:220).
  - Impact: capacity decisions cannot distinguish normal latency from tail latency or identify quota/listing/upload bottlenecks.
  - Confidence: high.

## Concrete Recommendations
Immediate: add benchmarks for upload quota scans, ordinary upload at max size/concurrency, `INFO` listing at 1k/10k entries, Notepad save/list near limits, slow body timeout under worker pressure, and WebSocket slot saturation.

Smallest code mitigation: short-circuit `UploadStorageService._check_accepts()` when `policy.has_limits` is false, after validating `size >= 0`. Expected risk reduction: removes an O(file-count) scan from default uploads.

For `/metrics`: keep current counters/gauges, but add fixed request-latency buckets and operation-specific timing counters for `upload_quota_scan_ms`, `upload_publish_ms`, `info_listing_ms`, and `notepad_save_ms` before promoting wider usage.

## Quick Wins
- Add `tests/benchmarks/` using existing `pytest-benchmark`.
- Benchmark `INFO /uploads?limit=100` with large directories.
- Add a no-limit upload quota test proving `current_usage()` is not called.
- Add storage quota rejection counters by reason.

## Deeper Improvements
- Streaming upload-to-temp-file path to avoid full request body buffering.
- Cached/incremental upload usage accounting if aggregate quotas become common.
- Bounded or cursor-style directory listing semantics if `INFO` must handle very large directories.
- WebSocket connection duration/message counters, or separate worker budgeting if Notepad becomes core product.

## Open Questions
- What target workload defines "wider use": max files, max upload size, concurrent clients, and expected directory sizes?
- Should exact `INFO.total_items` remain required for large directories?
- Is `/metrics` intended as local diagnostics only, or an operator-facing contract?
