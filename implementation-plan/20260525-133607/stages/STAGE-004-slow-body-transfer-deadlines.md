# STAGE-004 - Slow body and transfer deadlines

## Status
CLOSED

## Priority
HIGH

## Source findings
- `codex-analysis/20260525-121051/project-analysis-report.md` - Critical & High Issues #3: slow/incomplete request bodies can occupy all workers for about 330 seconds.
- `codex-analysis/20260525-121051/agent-reports/performance-engineer.md` - HIGH slow-body and MEDIUM slow-download issues.
- `codex-analysis/20260525-121051/agent-reports/reviewer.md` - Final priority order includes slow-body protection under resource controls.

## Goal
Add configurable request body idle/deadline/read-rate protection and basic streamed response transfer protection so slow clients cannot monopolize workers indefinitely.

## Non-goals
- Reverse proxy buffering/rate limiting configuration.
- Replacing threadpool architecture.
- Full sendfile optimization, unless it is a small local improvement.

## Scope
### Likely files to inspect
- `src/http/io.py` - header/body timeout constants and receive loop.
- `src/server.py` - worker loop, `_send_response()`, streamed file send behavior.
- `src/metrics.py` - timeout/abort counters.
- `src/cli.py` - runtime knobs.
- `tests/test_http/test_io.py` - timeout and receive tests.
- `tests/test_server_live.py` - live slow-client/admission tests.

### Likely files to change
- `src/http/io.py` - body idle timeout, deadline, and/or minimum read-rate logic.
- `src/server.py` - response send deadline/abort handling and metrics.
- `src/cli.py` - flags for body timeout/read-rate and possibly response deadline.
- `src/metrics.py` - slow-body and stream-abort counters if metrics patterns allow.
- `tests/` - slow body, deadline, and slow reader regression tests.
- `README.md`, `SECURITY.md` - operator guidance.

### Files that must not be changed
- Package/release workflows - not part of this stage.
- `.env`, credentials, private keys, certificates - secrets must not be read or stored.

## Dependencies
- Depends on: STAGE-003
- Blocks: None

## Implementation steps
1. Add a configurable body idle timeout and/or minimum read-rate threshold with test-friendly defaults.
2. Keep existing header timeout behavior intact.
3. Record slow-body rejection separately from malformed request rejection where metrics/logging exist.
4. Add a total streamed-response deadline or abort condition for very slow response readers.
5. Ensure live tests avoid flaky timing by using small local timeouts and deterministic socket control.
6. Document the new knobs and deployment guidance.

## Acceptance criteria
- [x] Slow or incomplete bodies are closed well before the prior default combined 330 second budget when configured.
- [x] Normal slow-but-valid local tests remain possible through configurable thresholds.
- [x] Slow-body events are distinguishable in metrics or logs.
- [x] Streamed response sends have a bounded transfer/idle behavior.
- [x] Existing keep-alive and request size tests still pass.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `python -m pytest tests/test_http/test_io.py tests/test_server_live.py tests/test_metrics.py` | Slow-body, live admission, and metrics tests pass |
| Type/lint/build | `ruff check src tests && ruff format --check src tests && mypy src` | No lint, format, or type regressions |
| Manual/static review | Inspect timeout defaults and docs | Defaults are documented and do not make local normal uploads unexpectedly fail |

## Suggested subagents
- `explorer` - identify existing timeout constants and live-test helper patterns.
- `worker` - implement receive/send deadline behavior.
- `qa` - design timing-tolerant slow-client tests.

## Risks and rollback
- Risk: Timing tests can be flaky on slow CI runners.
- Rollback: Keep thresholds configurable and test with small deterministic sockets rather than wall-clock-heavy sleeps.

## Completion notes
Closed 2026-05-25 18:14:47 MSK.

- Added configurable request-body idle timeout, total body deadline, and optional minimum average body read-rate enforcement.
- Added bounded streamed-response sends with per-chunk idle timeout, optional total transfer deadline, and stream abort metrics.
- Added CLI flags and documentation for slow-body and streamed-response controls.
- Added receive, live, metrics, CLI, and adjacent send/pipeline regression coverage.
- Verification passed for targeted tests, adjacent tests, ruff lint/format, and `git diff --check`; `mypy` could not run because the local environment lacks the `mypy` package.
