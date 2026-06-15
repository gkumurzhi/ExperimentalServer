# STAGE-011 - WebSocket and Notepad safety

## Status
OPEN

## Priority
MEDIUM

## Source findings
- `codex-analysis/20260614-225437/agent-reports/websocket-engineer.md` - Issues: no server-side idempotency for `opId`, no conflict contract, send failures are swallowed, binary frame policy unclear.
- `codex-analysis/20260614-225437/agent-reports/security-auditor.md` - F3: WebSocket destructive note operations do not independently check `note_delete`/`note_clear` after upgrade.
- `codex-analysis/20260614-225437/agent-reports/api-designer.md` - WebSocket errors differ from HTTP errors; v1 should normalize later.
- `codex-analysis/20260614-225437/project-analysis-report.md` - WebSocket is lab-grade, not workspace sync-grade.

## Goal
Apply bounded legacy WebSocket/Notepad safety fixes and documentation without presenting `/notes/ws` as a full workspace sync protocol.

## Non-goals
- Do not implement WebSocket v1, revisions, replay, resume tokens, or collaborative conflict handling.
- Do not add fragmentation support unless required by an existing testable client contract.
- Do not make Notepad durable or recoverable.

## Scope
### Likely files to inspect
- `src/handlers/notepad.py` - WebSocket message handling, delete/clear operations, `_ws_send_json`.
- `src/server.py` - WebSocket upgrade, loop, binary/text dispatch, ping behavior, frame timeout.
- `src/websocket.py` - frame parser, close codes, binary/fragmentation behavior.
- `API.md` and `docs/api.md` - WebSocket message and close-code docs.
- `tests/test_websocket.py`, `tests/test_websocket_handlers.py`, `tests/test_security/test_websocket_upgrade.py`, `tests/test_server_live.py` - existing WS coverage.

### Likely files to change
- `src/handlers/notepad.py` - add message-level `note_delete`/`note_clear` checks and make send failure observable or connection-ending.
- `src/server.py` or `src/websocket.py` - clarify/enforce binary frame policy if docs and implementation disagree.
- `tests/test_websocket_handlers.py` - add regression tests for destructive capability checks, `opId` semantics, send-failure behavior if injectable, and duplicate `opId` documentation examples.
- `tests/test_websocket.py` or `tests/test_server_live.py` - add slow incomplete-frame trickle or binary-frame policy tests if feasible.
- `API.md` and `docs/api.md` - document legacy `opId` as correlation, conflict/last-write-wins limits, binary-frame policy, and close-code semantics.

### Files that must not be changed
- `src/notepad_service.py` durable/revision model - conflict handling is future work unless a tiny test helper is needed.
- `src/data/static/ui/**` - UI changes are STAGE-005 unless WS error display needs a small integration hook.
- API v1 endpoint files - do not add a v1 route in this stage.
- `.env*`, credentials, keys, certificates - secrets are out of scope.

## Dependencies
- Depends on: STAGE-003, STAGE-010
- Blocks: `None`

## Implementation steps
1. Add message-level capability checks for WebSocket `delete` and `clear`, matching HTTP NOTE `note_delete` and `note_clear`.
2. Add regression tests for a custom/future profile where `websocket_notes=True` but destructive note capabilities are false.
3. Make `_ws_send_json` report success/failure, update metrics or close the socket on failure, and test the behavior where practical.
4. Decide legacy binary-frame behavior: either document binary JSON as supported or close binary frames with `1003`.
5. Document `opId` as correlation-only, not server dedupe, and document last-write-wins/no-conflict semantics.
6. Add a slow incomplete-frame trickle test if feasible without making the suite flaky.

## Acceptance criteria
- [ ] WebSocket `delete` and `clear` reject operations when `note_delete` or `note_clear` is false, even if WebSocket notes are enabled.
- [ ] Tests cover destructive WebSocket capability checks for a divergent/custom profile.
- [ ] Send failures are not silently ignored after side effects; behavior is observable in tests or metrics/logging and documented.
- [ ] Binary-frame policy is consistent between implementation, tests, and API docs.
- [ ] Legacy `opId`, retry, and conflict semantics are documented without promising server-side idempotency.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted WS tests | `python -m pytest tests/test_websocket.py tests/test_websocket_handlers.py tests/test_security/test_websocket_upgrade.py` | Exits 0. |
| Live WS tests | `python -m pytest tests/test_server_live.py` | Exits 0 or records unrelated existing failures. |
| Docs checks | `python tools/sync_docs.py --check && python tools/check_stale_docs.py` | Exits 0. |
| Manual/static review | Trace WS delete/clear, send failure, binary policy, and docs | Legacy behavior is safer and accurately documented. |

## Suggested subagents
- `explorer` - map current WS message paths and test seams.
- `worker` - implement capability checks, send-failure behavior, tests, and docs.
- `security-reviewer` - review destructive operation checks if available.

## Risks and rollback
- Risk: changing send-failure behavior can affect clients that rely on silent continuation.
- Rollback: keep capability checks, but revert send-failure handling to previous behavior and document the unresolved risk if tests show compatibility problems.

## Completion notes
Filled by `close-plan-stage`.
