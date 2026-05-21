# STAGE-004 - Add Notepad payload size limits

## Status
OPEN

## Priority
HIGH

## Source findings
- `project-analysis-report.md` - F-004: before operation beyond trusted local use, Notepad needs explicit encoded/decoded size limits.

## Goal
Add explicit, documented Notepad encrypted-blob size limits for HTTP and WebSocket saves, independent of generic request/frame caps.

## Non-goals
- Do not change encryption format or note ID contract.
- Do not alter idempotent save behavior from the closed STAGE-010.

## Scope
### Likely files to inspect
- `src/notepad_service.py` - save validation.
- `src/handlers/notepad.py` - HTTP/WS mapping.
- `src/websocket.py` and WebSocket frame limits - interaction with frame cap.
- `API.md`, `docs/api.md` - protocol docs.
- `tests/test_handlers/test_notepad.py`, `tests/test_websocket_handlers.py` - contract tests.

### Likely files to change
- `src/notepad_service.py` - encoded/decoded limit validation.
- `src/handlers/notepad.py` - transport-specific error mapping if needed.
- API docs and targeted tests.

### Files that must not be changed
- Static Notepad UI behavior unless a visible error path requires a small update.

## Dependencies
- Depends on: STAGE-001
- Blocks: STAGE-008

## Implementation steps
1. Decide limit defaults and whether they follow `--max-size` or have a dedicated setting.
2. Add tests for oversized base64 field, oversized decoded ciphertext, and boundary success over HTTP and WS.
3. Implement validation before expensive decode where possible.
4. Preserve idempotency fields and response shape.
5. Update API docs and sync mirrors.

## Acceptance criteria
- [ ] Oversized Notepad HTTP saves return a deterministic error before writing.
- [ ] Oversized Notepad WS saves return a deterministic `saved` error payload with status.
- [ ] Boundary payloads still save/load successfully.
- [ ] API docs describe the limit and relation to generic caps.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| HTTP tests | `pytest -q tests/test_handlers/test_notepad.py` | Pass. |
| WS tests | `pytest -q tests/test_websocket_handlers.py` | Pass. |
| Docs sync | `python tools/sync_docs.py --check` | Pass. |

## Suggested subagents
- `explorer` - inspect current Notepad save contracts and test helpers.
- `backend-developer` - implement validation and docs.

## Risks and rollback
- Risk: Limit defaults can surprise users with existing large encrypted notes.
- Rollback: Raise default, make configurable, or document migration guidance.

## Completion notes
Filled by `close-plan-stage`.
