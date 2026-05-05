# STAGE-009 - Guard Notepad plaintext title and dirty transitions

## Status
OPEN

## Priority
MEDIUM

## Source findings
- `codex-analysis/20260505-193249/project-analysis-report.md` - Frontend & UX: dirty edits can be lost; title metadata is plaintext while docs imply broad E2E encryption.
- `codex-analysis/20260505-193249/agent-reports/frontend-developer.md` - MEDIUM: privacy copy misleading for titles and dirty edits can be lost before debounce save.
- `codex-analysis/20260505-193249/agent-reports/security-auditor.md` - MEDIUM: note titles are plaintext metadata.
- `codex-analysis/20260505-193249/agent-reports/api-documenter.md` - HIGH docs gap includes plaintext metadata fields.

## Goal
Make the UI honest about plaintext note titles and prevent recent dirty edits from being silently discarded during common Notepad transitions.

## Non-goals
- Do not encrypt titles in this stage.
- Do not implement durable key recovery.
- Do not redesign WebSocket save idempotency; that is STAGE-010.

## Scope
### Likely files to inspect
- `src/data/static/ui/notepad.js` - dirty state, debounce save, note switch/new/delete/clear/transport flows.
- `src/data/static/ui/core.js` - Notepad strings and privacy copy.
- `tools/browser_smoke.playwright.js` - Notepad UI smoke flows.
- `tests/test_ui_inspector_redaction.py` - title metadata redaction expectations.
- `src/notepad_service.py` - plaintext metadata behavior for title.

### Likely files to change
- `src/data/static/ui/notepad.js` - flush/confirm dirty transitions and title metadata warning behavior.
- `src/data/static/ui/core.js` - copy for title metadata and privacy claims.
- `tools/browser_smoke.playwright.js` - smoke coverage for dirty edit -> switch/new and title warning.
- `tests/test_ui_inspector_redaction.py` - adjust/extend metadata assertions if copy or title treatment changes.

### Files that must not be changed
- `src/security/keys.py` and `examples/notepad_client.py` - STAGE-002 owns key contract.
- `src/handlers/notepad.py` WebSocket protocol - STAGE-010 owns WS idempotency.
- `notes/**` - runtime/user note data.
- `.env*`, credentials, keys, certificates - never read or edit secrets.

## Dependencies
- Depends on: STAGE-002
- Blocks: STAGE-010

## Implementation steps
1. Identify every UI action that can replace or clear editor state: load, new, clear, delete-selected, transport switch, reconnect fallback if relevant.
2. Add a central guard that flushes pending debounce save or asks for explicit discard before destructive transitions.
3. Keep the guard ergonomic for empty/new notes and failed saves.
4. Add visible but concise UI copy that note bodies are encrypted while titles are server-visible metadata.
5. Add browser smoke or JS/unit-style coverage for dirty edit followed immediately by note switch/new.

## Acceptance criteria
- [ ] Dirty edits are not silently lost when switching notes or creating a new note before debounce save completes.
- [ ] Title privacy copy no longer implies titles are encrypted.
- [ ] Existing Notepad HTTP and WS happy paths still pass.
- [ ] Tests or smoke cover at least one dirty-transition regression.
- [ ] Redaction/inspector expectations remain explicit about title visibility.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Browser smoke | `python tools/browser_smoke.py` | Passes with new dirty-transition coverage if browser tooling available |
| Redaction tests | `pytest -q tests/test_ui_inspector_redaction.py` | Passes |
| Notepad handler tests | `pytest -q tests/test_handlers/test_notepad.py tests/test_websocket_handlers.py` | Passes |
| Manual UI review | Use bundled UI to type, immediately switch/new, and verify save/confirm behavior | No silent loss |

## Suggested subagents
- `explorer` - map Notepad state transitions and existing smoke hooks.
- `worker` - implement UI guard/copy and smoke test.
- `frontend-developer` - review UX and state behavior.

## Risks and rollback
- Risk: Confirm prompts or forced saves can make Notepad workflows noisy.
- Rollback: Revert UI guard and smoke changes, retaining only copy updates if title privacy wording is still needed.

## Completion notes
Filled by `close-plan-stage`.
