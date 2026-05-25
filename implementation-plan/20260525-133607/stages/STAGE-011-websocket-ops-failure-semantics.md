# STAGE-011 - WebSocket operations and failure semantics

## Status
CLOSED

## Priority
MEDIUM

## Source findings
- `codex-analysis/20260525-121051/agent-reports/performance-engineer.md` - LOW WebSocket resource knobs exist in code but are not exposed in CLI.
- `codex-analysis/20260525-121051/agent-reports/python-pro.md` - MEDIUM unexpected WebSocket failures close as normal `1000` and log only at debug.
- `codex-analysis/20260525-121051/project-analysis-report.md` - Short term: add CLI knobs for WebSocket capacity/incomplete-frame timeout and better error close semantics.

## Goal
Expose WebSocket operational limits in the CLI and make unexpected WebSocket failures observable to clients and operators.

## Non-goals
- Full WebSocket specialist redesign; the specialist report was incomplete.
- Changing Notepad encryption/session semantics.
- Feature gating beyond consuming STAGE-006 profile availability.

## Scope
### Likely files to inspect
- `src/server.py` - WebSocket admission, frame loop, exception handling.
- `src/websocket.py` - close codes and parser behavior.
- `src/cli.py` - runtime flags.
- `src/metrics.py` - counters if available.
- `tests/test_websocket.py`, `tests/test_websocket_handlers.py`, `tests/test_server_live.py` - WebSocket coverage.

### Likely files to change
- `src/cli.py` - add WebSocket max connections and frame idle timeout flags.
- `src/server.py` - wire CLI values, log unexpected exceptions, send `1011` or explicit error frame, increment metrics.
- `tests/` - add CLI, close-code/error, and admission tests.
- `README.md`, `API.md` - document WebSocket operation knobs and failure behavior.

### Files that must not be changed
- Notepad storage policy beyond existing interfaces.
- Docker/release workflows unless docs need command examples.

## Dependencies
- Depends on: STAGE-006
- Blocks: None

## Implementation steps
1. Add CLI flags for `max_websocket_connections` and `websocket_frame_idle_timeout`.
2. Validate flag bounds consistently with constructor assumptions.
3. Wire flags through CLI config into `ExperimentalHTTPServer`.
4. Change unexpected WebSocket exceptions to non-debug exception logging and failure close semantics such as `1011`.
5. Add metrics for unexpected WebSocket internal errors if metrics patterns allow.
6. Add tests for CLI propagation, admission limits, incomplete-frame timeout, and unexpected failure close behavior.

## Acceptance criteria
- [x] Operators can configure WebSocket connection budget and incomplete-frame timeout from CLI.
- [x] Invalid WebSocket CLI values fail clearly before server start.
- [x] Unexpected internal WebSocket errors are logged as failures and do not close as normal `1000`.
- [x] Existing WebSocket frame cap and admission tests still pass.
- [x] Docs describe the new knobs and default behavior.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `python -m pytest tests/test_websocket.py tests/test_websocket_handlers.py tests/test_server_live.py tests/test_cli.py` | WebSocket and CLI tests pass |
| Type/lint/build | `ruff check src tests && ruff format --check src tests && mypy src` | No lint, format, or type regressions |
| Manual/static review | Inspect WebSocket exception path | Unexpected failures use explicit failure close semantics and actionable logging |

## Suggested subagents
- `explorer` - map current WebSocket config and exception paths.
- `worker` - implement CLI knobs and failure semantics.
- `qa` - add focused WebSocket regression tests.

## Risks and rollback
- Risk: Close-code tests may need low-level frame inspection and can be brittle.
- Rollback: Assert observable client error frame or server metric/log when close-code capture is unreliable.

## Completion notes
Closed 2026-05-25 21:00:08 MSK. Added CLI flags for WebSocket admission budget and incomplete-frame timeout, wired them into `ExperimentalHTTPServer`, and documented defaults. Unexpected WebSocket internal failures now log at error level, increment `metrics.websocket.errors`, and close with `1011 Internal error` rather than normal `1000`. Targeted WebSocket/CLI tests, adjacent server-method frame/admission tests, lint, format, isolated pinned mypy, stale-doc guard, diff whitespace check, and scoped explorer subagent verification passed. Report: `stage-reports/STAGE-011-20260525-205403.md`.
