# STAGE-004 — Enforce WebSocket Client Masking

## Status
OPEN

## Priority
HIGH

## Source findings
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/websocket-engineer.md` — HIGH: client masking is not enforced
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/qa-expert.md` — tests assert permissive unmasked parsing
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/security-auditor.md` — WebSocket accepts unmasked client frames

## Goal
Inbound client WebSocket frames without masks are rejected with protocol error behavior while server-frame helpers remain usable.

## Non-goals
- Do not implement full fragmentation/RSV/opcode validation; STAGE-015 owns that.
- Do not redesign NOTE WebSocket application messages.

## Scope
### Likely files to inspect
- `src/websocket.py` — frame parser/build helpers
- `src/server.py` — `_handle_notepad_ws()` receive loop
- `tests/test_websocket.py`, `tests/test_websocket_handlers.py`, `tests/test_security/test_websocket_frame_limit.py` — parser and server tests

### Likely files to change
- `src/websocket.py` — add inbound require-mask mode or parser split
- `src/server.py` — use require-mask parsing for client traffic and close with `1002`
- `tests/test_websocket*.py` — update helper tests and add unmasked rejection regression

### Files that must not be changed
- `uploads/**` — runtime user data; do not inspect contents unless an explicit disposable test fixture is created
- `notes/**` — encrypted runtime note data; do not inspect contents
- `.env*`, `*.key`, `*.pem`, `*.p12`, `*.pfx`, credential JSON — secret-heavy files
- `codex-analysis/**` — source analysis artifacts; read-only evidence only
- `implementation-plan/**` — planning artifacts; close-plan-stage may update status/report files only

## Dependencies
- Depends on: None
- Blocks: STAGE-015, STAGE-016, STAGE-023

## Implementation steps
1. Split generic frame parsing from inbound client parsing, or add a `require_mask` parameter with safe default at server call sites.
2. When an inbound frame is unmasked, send close code `1002` and terminate without processing payload.
3. Keep unmasked server-to-client frame construction/parsing available only for tests/helpers that need it.
4. Update tests that currently encode unmasked inbound parsing as acceptable behavior.

## Acceptance criteria
- [ ] Unmasked client frames sent to `/notes/ws` are rejected and not dispatched to NOTE handlers.
- [ ] Server-to-client frame tests still have a valid helper path.
- [ ] Regression tests verify close/protocol-error behavior.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `pytest tests/test_websocket.py tests/test_websocket_handlers.py tests/test_security/test_websocket_frame_limit.py -q` | WebSocket tests pass with unmasked client rejection |
| Type/lint/build | `python -m compileall src tests` | Compilation succeeds |
| Manual/static review | Inspect `_handle_notepad_ws()` parser call | Inbound traffic requires masking |

## Suggested subagents
- `websocket-engineer` — RFC behavior review.
- `qa-expert` — regression coverage review.

## Risks and rollback
- Risk: Existing non-browser test clients may need helper updates to send masked frames.
- Rollback: Revert WebSocket parser/server/test changes for this stage.

## Completion notes
Filled by `close-plan-stage`.
