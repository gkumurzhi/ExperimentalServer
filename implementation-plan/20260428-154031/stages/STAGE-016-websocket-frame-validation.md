# STAGE-016 — Validate WebSocket Frame Semantics

## Status
OPEN

## Priority
MEDIUM

## Source findings
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/websocket-engineer.md` — MEDIUM: FIN/fragmentation/RSV/unsupported opcode rules not enforced
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/websocket-engineer.md` — LOW: missing Host can still upgrade when Origin absent

## Goal
The WebSocket server rejects unsupported or malformed frame/handshake semantics before application side effects.

## Non-goals
- Do not implement full fragmented message reassembly unless chosen explicitly.
- Do not solve worker exhaustion; STAGE-017 owns resource limits.

## Scope
### Likely files to inspect
- `src/websocket.py` — parser constants and frame validation
- `src/server.py` — `_handle_notepad_ws()` close handling
- `src/request_pipeline.py` — upgrade path
- `tests/test_websocket*.py` and `tests/test_security/test_websocket_upgrade.py` — existing coverage

### Likely files to change
- `src/websocket.py` — validate FIN/RSV/opcode/control frame rules and Host if appropriate
- `src/server.py` — close with protocol-specific codes and suppress duplicate closes
- `tests/` — RSV, FIN=0, unknown opcode, control frame, close payload, Host regressions

### Files that must not be changed
- `uploads/**` — runtime user data; do not inspect contents unless an explicit disposable test fixture is created
- `notes/**` — encrypted runtime note data; do not inspect contents
- `.env*`, `*.key`, `*.pem`, `*.p12`, `*.pfx`, credential JSON — secret-heavy files
- `codex-analysis/**` — source analysis artifacts; read-only evidence only
- `implementation-plan/**` — planning artifacts; close-plan-stage may update status/report files only

## Dependencies
- Depends on: STAGE-004
- Blocks: STAGE-017, STAGE-023

## Implementation steps
1. Define policy for fragmented data frames: either reject with `1002` or assemble with a strict aggregate cap.
2. Reject RSV bits unless an extension is negotiated, unknown/reserved opcodes, fragmented/oversized control frames, and invalid close payloads.
3. Require `Host` for upgrade validation or document an explicit exception if compatibility requires it.
4. Track close-sent state to avoid duplicate contradictory close frames.
5. Add focused parser and live-upgrade tests.

## Acceptance criteria
- [ ] Malformed frame semantics do not reach NOTE application handlers.
- [ ] Protocol close codes preserve the first real error reason.
- [ ] Missing required handshake headers are rejected consistently.
- [ ] Tests cover the listed frame/handshake cases.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `pytest tests/test_websocket.py tests/test_websocket_handlers.py tests/test_security/test_websocket_upgrade.py tests/test_security/test_websocket_frame_limit.py -q` | WebSocket protocol tests pass |
| Type/lint/build | `python -m compileall src tests` | Compilation succeeds |
| Manual/static review | Map parser outcomes to close codes | Unsupported frame states fail before side effects |

## Suggested subagents
- `websocket-engineer` — RFC behavior.
- `qa-expert` — edge-case coverage.

## Risks and rollback
- Risk: Some non-compliant clients may stop working.
- Rollback: Revert WebSocket validation and tests for this stage.

## Completion notes
Filled by `close-plan-stage`.
