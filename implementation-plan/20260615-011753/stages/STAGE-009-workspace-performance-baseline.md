# STAGE-009 - Workspace performance baseline

## Status
CLOSED

## Priority
MEDIUM

## Source findings
- `codex-analysis/20260614-225437/agent-reports/performance-engineer.md` - Issues: no-limit upload quota scans still walk `uploads/`; `INFO` pagination materializes all entries; no benchmark files exist.
- `codex-analysis/20260614-225437/project-analysis-report.md` - Performance & Reliability: add benchmarks and short-circuit quota scans when aggregate upload limits are disabled.
- `codex-analysis/20260614-225437/agent-reports/project-manager.md` - STAGE-009: benchmark uploads, quota scans, large `INFO`, Notepad list/save, and WebSocket slots.

## Goal
Add benchmark coverage for workspace hot paths and remove the default no-limit upload quota scan without changing public API semantics.

## Non-goals
- Do not implement streaming uploads.
- Do not change `INFO` pagination semantics or `total_items` behavior yet.
- Do not redesign metrics into an operator-facing contract unless benchmark data justifies a later stage.

## Scope
### Likely files to inspect
- `src/storage.py` - `UploadStorageService._check_accepts()`, `current_usage()`, quota policy.
- `src/handlers/info.py` - directory listing materialization and pagination.
- `src/notepad_service.py` - save/list quota scans and listing limit.
- `src/http/io.py` and `src/http/request.py` - upload receive/body parsing hot path.
- `src/metrics.py` - current latency/count metrics.
- `pyproject.toml` - `pytest-benchmark` availability.
- Existing tests under `tests/test_handlers/`, `tests/test_server_live.py`, and `tests/test_metrics.py`.

### Likely files to change
- `tests/benchmarks/` - add benchmark tests for upload quota scans, upload publish, INFO listing, Notepad save/list, slow body behavior, and WebSocket slots where practical.
- `src/storage.py` - short-circuit aggregate usage scan when upload policy has no limits.
- `tests/test_handlers/test_files.py` or a focused storage test - prove `current_usage()` is not called for no-limit upload policy.
- `README.md` or contributor docs - document how to run benchmarks if needed.

### Files that must not be changed
- API docs or `INFO` response contract - semantic changes belong to a later API/performance stage.
- `src/http/io.py` streaming behavior - out of scope for this baseline stage.
- `.github/workflows/**` - do not make benchmarks a hard CI gate unless explicitly lightweight and stable.
- `.env*`, credentials, keys, certificates - secrets are out of scope.

## Dependencies
- Depends on: STAGE-003
- Blocks: `None`

## Implementation steps
1. Add `tests/benchmarks/` using existing `pytest-benchmark` dependency.
2. Add benchmark cases for upload quota scan/publish, large `INFO` listing, Notepad save/list near limits, and WebSocket slot saturation where feasible without external services.
3. Implement the smallest no-limit upload quota optimization: validate size, then skip aggregate usage scan when policy has no limits.
4. Add a targeted regression test proving no-limit upload does not call `current_usage()`.
5. Run targeted storage/info tests and benchmark collection.
6. Record benchmark baselines and environment notes in the stage report rather than enforcing brittle thresholds immediately.

## Acceptance criteria
- [x] Benchmark files exist and can be collected by pytest.
- [x] Baseline benchmark results are recorded in the stage report with environment notes.
- [x] No-limit upload policy avoids unnecessary aggregate usage scans.
- [x] Existing quota behavior remains unchanged when upload limits are enabled.
- [x] `INFO` and Notepad benchmarks expose current behavior without changing API semantics.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Benchmark collection | `python -m pytest tests/benchmarks --benchmark-only` | Benchmarks collect and run when `pytest-benchmark` is installed. |
| Targeted storage tests | `python -m pytest tests/test_handlers/test_files.py tests/test_handlers/test_handler_integration.py` | Exits 0. |
| Metrics/live tests | `python -m pytest tests/test_metrics.py tests/test_server_live.py` | Exits 0 or records unrelated existing failures. |
| Manual/static review | Inspect `src/storage.py` no-limit branch | Limited policies still call quota checks; no-limit policies skip aggregate scan. |

## Suggested subagents
- `explorer` - map hot paths and existing test helpers.
- `worker` - add benchmarks and no-limit quota fix.
- `performance-reviewer` - review benchmark noise and baseline reporting if available.

## Risks and rollback
- Risk: benchmarks can be slow or flaky if they depend on large file counts or live sockets.
- Rollback: keep the no-limit quota test/fix if correct, but mark heavy benchmarks as optional or reduce dataset size before closing.

## Completion notes
Closed 2026-06-15 16:40:18 +0300. Added workspace hot-path benchmark coverage for upload quota scan, no-limit publish, INFO listing, Notepad save/list, chunked receive, and WebSocket slots; recorded local baseline numbers in `stage-reports/STAGE-009-20260615-161853.md`. `UploadStorageService._check_accepts()` now skips aggregate `current_usage()` scans when byte/file-count limits are disabled while preserving limited-policy behavior and reserved-free-space checks.
