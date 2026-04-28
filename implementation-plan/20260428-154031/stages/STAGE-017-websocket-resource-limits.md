# STAGE-017 — Bound WebSocket Resource Use

## Status
OPEN

## Priority
MEDIUM

## Source findings
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/websocket-engineer.md` — MEDIUM: long-lived WS can pin all worker threads
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/performance-engineer.md` — MEDIUM: partial frames retain near-limit buffers and workers

## Goal
WebSocket connections have explicit resource limits for concurrency, partial-frame lifetime, and buffering.

## Non-goals
- Do not migrate to asyncio.
- Do not redesign NOTE application protocol; STAGE-018 may add metrics only.

## Scope
### Likely files to inspect
- `src/server.py` — worker pool and `_handle_notepad_ws()` loop
- `src/websocket.py` — max frame size and parse state
- `src/metrics.py` — active connection counters if needed
- `docs/ADR/ADR-005-threadpool-over-asyncio.md` — stated concurrency target

### Likely files to change
- `src/server.py` — WS connection admission/semaphore and incomplete-frame timeout
- `src/websocket.py` — expose expected length or safer buffer handling if needed
- `src/metrics.py` — optional active WS counters
- `tests/` — slow/incomplete frame and connection-budget tests

### Files that must not be changed
- `uploads/**` — runtime user data; do not inspect contents unless an explicit disposable test fixture is created
- `notes/**` — encrypted runtime note data; do not inspect contents
- `.env*`, `*.key`, `*.pem`, `*.p12`, `*.pfx`, credential JSON — secret-heavy files
- `codex-analysis/**` — source analysis artifacts; read-only evidence only
- `implementation-plan/**` — planning artifacts; close-plan-stage may update status/report files only

## Dependencies
- Depends on: STAGE-016
- Blocks: STAGE-018

## Implementation steps
1. Add a small WebSocket connection budget separate from or derived from worker count.
2. Close connections that keep an incomplete frame across a defined idle/timeout threshold.
3. Avoid repeated immutable `buf += chunk` copying where practical.
4. Add tests for connection budget and slow incomplete frame behavior.

## Acceptance criteria
- [ ] Idle WebSockets cannot occupy all request workers without an explicit configured budget.
- [ ] Incomplete near-limit frames are closed after a bounded idle period.
- [ ] Metrics/logging can distinguish rejected WS admissions if implemented.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `pytest tests/test_websocket.py tests/test_server_live.py tests/test_security/test_websocket_frame_limit.py -q` | WS resource-limit tests pass |
| Type/lint/build | `python -m compileall src tests` | Compilation succeeds |
| Manual/static review | Inspect worker/WS loop limits | No unbounded idle WS loop without admission control remains |

## Suggested subagents
- `websocket-engineer` — connection lifecycle.
- `performance-engineer` — memory/worker pressure.

## Risks and rollback
- Risk: Legitimate concurrent WS clients may be limited by default.
- Rollback: Revert WS resource-limit changes and tests for this stage.

## Completion notes
Filled by `close-plan-stage`.
