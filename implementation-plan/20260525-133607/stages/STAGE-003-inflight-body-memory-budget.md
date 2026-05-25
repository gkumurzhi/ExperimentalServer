# STAGE-003 - In-flight body memory budget

## Status
OPEN

## Priority
HIGH

## Source findings
- `codex-analysis/20260525-121051/project-analysis-report.md` - Critical & High Issues #2: standard uploads are fully buffered in memory.
- `codex-analysis/20260525-121051/agent-reports/performance-engineer.md` - HIGH memory issue: default concurrent upload ceiling is roughly `max_workers * max_upload_size`.
- `codex-analysis/20260525-121051/agent-reports/reviewer.md` - Missing blocker: fully buffered standard uploads can exhaust memory.

## Goal
Add a process-wide in-flight request body memory budget, or an equivalent streaming receive path, so concurrent valid uploads cannot allocate unbounded body memory.

## Non-goals
- Aggregate disk quota; covered by STAGE-001 and STAGE-002.
- Slow-body timing policy; covered by STAGE-004.
- Large response streaming optimization.

## Scope
### Likely files to inspect
- `src/http/io.py` - request body receive and buffering.
- `src/http/request.py` - `HTTPRequest.body` ownership.
- `src/request_pipeline.py` - receive/process boundary.
- `src/server.py` - worker/admission and configuration ownership.
- `src/cli.py` - `--workers` and `--max-size` knobs.
- `tests/test_http/test_io.py` - receive-layer tests.
- `tests/test_request_pipeline.py`, `tests/test_server_live.py` - integration/admission coverage.

### Likely files to change
- `src/http/io.py` - reserve/release body bytes or stream body to temp storage.
- `src/server.py` - own budget counter/semaphore and expose metrics.
- `src/cli.py` - add body memory budget flag or derive documented default.
- `src/metrics.py` - optional in-flight body bytes metric.
- `tests/` - add budget saturation, release-on-error, and concurrency tests.
- `README.md`, `SECURITY.md` - document memory planning bound.

### Files that must not be changed
- `.env`, credentials, private keys, certificates - secrets must not be read or stored.
- Docker/release workflow files - later stages own those unless needed for docs only.

## Dependencies
- Depends on: STAGE-001
- Blocks: STAGE-004

## Implementation steps
1. Decide whether this stage implements declared-length reservation or a streaming temp-file receive path; prefer reservation if streaming is too broad.
2. Reserve declared `Content-Length` against a process-wide budget before reading body bytes.
3. Reject over-budget bodies with a stable `413` or `503` response before reading the full body.
4. Release reservations on normal completion, parse errors, handler errors, and closed connections.
5. Add metrics or logging for current/peak in-flight body bytes if existing metrics patterns support it.
6. Add tests that simulate concurrent allowed bodies exceeding the aggregate budget.

## Acceptance criteria
- [ ] Concurrent request body memory is bounded by a configurable process-wide budget or equivalent streaming design.
- [ ] Budget rejection occurs before full body allocation.
- [ ] Reservations are released on success and all tested failure paths.
- [ ] Existing parser/body cap tests still pass.
- [ ] Operator docs state the relationship among workers, max request size, and body memory budget.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `python -m pytest tests/test_http/test_io.py tests/test_request_pipeline.py tests/test_server_live.py tests/test_metrics.py` | Receive, pipeline, live admission, and metrics tests pass |
| Type/lint/build | `ruff check src tests && ruff format --check src tests && mypy src` | No lint, format, or type regressions |
| Manual/static review | Inspect reservation lifecycle | Every reservation path has a matching release in `finally` or equivalent cleanup |

## Suggested subagents
- `explorer` - trace request receive lifecycle and failure paths.
- `worker` - implement budget reservation and metrics.
- `qa` - add concurrent body-budget tests.

## Risks and rollback
- Risk: Declared `Content-Length` reservation can be conservative for clients that disconnect early.
- Rollback: Make the budget configurable and ensure release-on-disconnect; revert to prior receive path only if tests show deadlocks or leaked reservations.

## Completion notes
Filled by `close-plan-stage`.

