# STAGE-006 - Expand operational metrics and worker exception visibility

## Status
CLOSED

## Priority
MEDIUM

## Source findings
- `project-analysis-report.md` - F-006: metrics lack active/queued work, receive-layer drops, timeout/limit rejections, latency, and worker exception visibility.

## Goal
Expose enough metrics and logs to distinguish overload, slow clients, receive rejections, WebSocket pressure, and worker failures.

## Non-goals
- Do not introduce an external metrics backend.
- Do not change `/metrics` to a non-JSON format.

## Scope
### Likely files to inspect
- `src/metrics.py` - snapshot and counters.
- `src/server.py` - worker lifecycle, receive, admission, WebSocket counters.
- `src/request_pipeline.py` - request timing and direct responses.
- `tests/test_metrics.py`, `tests/test_server_methods.py`, `tests/test_handlers/test_handler_integration.py`.

### Likely files to change
- `src/metrics.py` - new counters/gauges/timing fields.
- `src/server.py` - worker future/exception logging and metric hooks.
- Docs/API examples for `/metrics`.

### Files that must not be changed
- UI dashboards unless metrics display changes are explicitly scoped.

## Dependencies
- Depends on: STAGE-003
- Blocks: STAGE-008

## Implementation steps
1. Define metric names for active connections, admission rejected, receive drops, timeouts, bytes received, latency, WebSocket close/rejects, and worker exceptions.
2. Add unit tests for metrics increments and snapshot immutability.
3. Hook metrics into server receive/admission/worker lifecycle paths.
4. Ensure worker exceptions are logged or retained rather than silently disappearing.
5. Update `/metrics` docs and examples.

## Acceptance criteria
- [x] `/metrics` exposes active/admission/receive/timeout/error signals.
- [x] Worker exceptions are visible in logs or metrics.
- [x] Existing request/status/bytes metrics remain backward compatible or documented.
- [x] Metrics tests cover concurrent updates.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Metrics tests | `pytest -q tests/test_metrics.py tests/test_handlers/test_handler_integration.py::TestGetMetrics` | Pass. |
| Server tests | `pytest -q tests/test_server_methods.py -k 'metrics or worker or handle_client'` | Pass. |
| Static review | Inspect worker lifecycle | Exceptions are recorded/logged. |

## Suggested subagents
- `sre-engineer` - review operational signal names and overload observability.
- `backend-developer` - implement hooks and tests.

## Risks and rollback
- Risk: Metrics schema changes can affect clients.
- Rollback: Keep old fields and add new fields under nested keys.

## Completion notes
Closed 2026-05-21T23:55:01+03:00.

- Added additive `/metrics` fields for active worker connections, receive bytes/rejections, timeout buckets, request latency aggregates, expanded WebSocket pressure/error counters, and worker exception visibility while preserving existing top-level request/status/error/bytes fields.
- Worker failures are now logged and counted from `_handle_client`, worker future completion, and worker submission failure paths.
- Updated metrics/server/request-pipeline tests, live admission/WebSocket smoke assertions, and `/metrics` API documentation.
- Verification passed: metrics `TestMetrics`, server `metrics or worker or handle_client` selector, request pipeline tests, live admission/WebSocket smoke, `py_compile`, Ruff lint/format, and `git diff --check`. Local `mypy` could not run because the `mypy` package is not installed.
