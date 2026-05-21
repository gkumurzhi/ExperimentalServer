# STAGE-003 - Add bounded request admission before worker submission

## Status
OPEN

## Priority
HIGH

## Source findings
- `project-analysis-report.md` - F-003: accepted sockets are submitted to `ThreadPoolExecutor` without global queue/admission control.

## Goal
Prevent unbounded socket submission and preserve worker capacity under keep-alive, slow-client, and WebSocket pressure.

## Non-goals
- Do not replace the ThreadPoolExecutor architecture.
- Do not implement full async I/O.

## Scope
### Likely files to inspect
- `src/server.py` - accept loop, executor submission, WebSocket admission.
- `src/metrics.py` - counters/snapshot.
- `tests/test_server_methods.py`, `tests/test_server_live.py` - worker and WebSocket tests.
- `docs/ADR/ADR-005-threadpool-over-asyncio.md` - architectural note if behavior changes.

### Likely files to change
- `src/server.py` - semaphore/queue admission before `executor.submit`.
- `src/metrics.py` - admission counters.
- Tests for saturation, release on failures, and WebSocket budget interactions.

### Files that must not be changed
- `src/http/io.py` - receive parser changes belong to STAGE-002 unless a small hook is unavoidable.

## Dependencies
- Depends on: STAGE-002
- Blocks: STAGE-006, STAGE-008

## Implementation steps
1. Add failing tests showing submit is bounded and permits are released on normal close, exceptions, and TLS handshake failures.
2. Add admission primitive before executor submission.
3. Define rejection behavior for overload, including socket close or simple 503 where safe.
4. Preserve existing WebSocket admission semantics and reserve HTTP capacity.
5. Record admission accepted/rejected/active metrics.

## Acceptance criteria
- [ ] Accepted sockets cannot grow an unbounded executor queue.
- [ ] Admission permits are released on every tested exit path.
- [ ] WebSocket pressure cannot consume all default worker capacity.
- [ ] Existing keep-alive and WebSocket tests still pass.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `pytest -q tests/test_server_methods.py tests/test_server_live.py -k 'worker or websocket or keep_alive or admission'` | Pass. |
| Metrics tests | `pytest -q tests/test_metrics.py` | Pass with new counters. |
| Static review | Inspect accept loop | No `executor.submit` without prior admission. |

## Suggested subagents
- `backend-developer` - implement admission and tests.
- `performance-engineer` - review saturation and release paths.

## Risks and rollback
- Risk: Admission release bugs can deadlock the server.
- Rollback: Revert admission primitive and keep receive/header caps from STAGE-002.

## Completion notes
Filled by `close-plan-stage`.
