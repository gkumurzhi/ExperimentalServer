# STAGE-002 - Notes and SMUGGLE storage policy

## Status
CLOSED

## Priority
HIGH

## Source findings
- `codex-analysis/20260525-121051/project-analysis-report.md` - Critical & High Issues #1: notes and SMUGGLE artifacts contribute to unbounded accumulated storage.
- `codex-analysis/20260525-121051/agent-reports/performance-engineer.md` - HIGH storage issue and MEDIUM listing issue: notes scan all `*.enc`; SMUGGLE temp artifacts only clean on some lifecycle paths.
- `codex-analysis/20260525-121051/agent-reports/qa-expert.md` - HIGH test gap: repeated valid uploads/notes lack aggregate quota regression tests.

## Goal
Extend storage policy enforcement to Notepad and SMUGGLE artifacts, including bounded listing behavior and cleanup/retention tests.

## Non-goals
- Redesigning Notepad durable encryption or recovery semantics.
- Per-user Notepad authorization.
- Full UI redesign for note quota display.

## Scope
### Likely files to inspect
- `src/notepad_service.py` - note save/list/delete/clear and metadata handling.
- `src/handlers/notepad.py` - HTTP and WebSocket Notepad operations.
- `src/handlers/smuggle.py` - SMUGGLE temp artifact creation and cleanup.
- `src/server.py` - notes/uploads directory ownership and cleanup hooks.
- `tests/test_handlers/test_notepad.py` - Notepad API tests.
- `tests/test_websocket_handlers.py` - WebSocket Notepad tests.

### Likely files to change
- `src/notepad_service.py` - enforce note byte/count policy and improve bounded listing.
- `src/handlers/notepad.py` - map quota failures to clear client errors for HTTP and WebSocket.
- `src/handlers/smuggle.py` - apply temp artifact count/age/bytes policy.
- `src/server.py` - schedule startup/periodic cleanup if needed.
- `tests/` - add note quota, SMUGGLE retention, and listing bound tests.
- `README.md`, `API.md`, `docs/threat-model.md` - document note/SMUGGLE storage limits.

### Files that must not be changed
- `.env`, credentials, private keys, certificates - secrets must not be read or stored.
- `codex-analysis/**` - analysis evidence only.

## Dependencies
- Depends on: STAGE-001
- Blocks: STAGE-006

## Implementation steps
1. Reuse or extend the storage policy from STAGE-001 for notes and SMUGGLE temp artifacts.
2. Add note count and total note byte checks before writing note blobs/metadata.
3. Add SMUGGLE temp artifact max count, max bytes, and/or max age cleanup behavior.
4. Bound Notepad listing work with pagination, iteration limits, or an explicit metadata index.
5. Ensure HTTP and WebSocket Notepad quota failures return stable error contracts.
6. Add tests for over-quota notes, SMUGGLE cleanup, clear behavior, and bounded listing.

## Acceptance criteria
- [x] Notepad saves reject writes that exceed configured note count or total bytes and leave no partial note state.
- [x] SMUGGLE temp artifacts are bounded by age/count/bytes and cleanup is exercised by tests.
- [x] Notepad listing no longer requires unbounded full-directory work before applying response limits.
- [x] Existing Notepad per-note size and rollback tests still pass.
- [x] Docs describe storage limits for uploads, notes, and SMUGGLE separately or via a clear shared policy.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `python -m pytest tests/test_handlers/test_notepad.py tests/test_websocket_handlers.py tests/test_server_methods.py` | Note, WebSocket note, and SMUGGLE/method behavior pass |
| Type/lint/build | `ruff check src tests && ruff format --check src tests && mypy src` | No lint, format, or type regressions |
| Manual/static review | Inspect quota failure paths | Failed writes clean temp/metadata state and return stable HTTP/WS errors |

## Suggested subagents
- `explorer` - map all note and SMUGGLE artifact write/delete paths.
- `worker` - implement policy integration and cleanup behavior.
- `qa` - add Notepad/SMUGGLE quota and listing tests.

## Risks and rollback
- Risk: Existing clients may expect unlimited note count or all-notes list responses.
- Rollback: Keep pagination/limits documented and configurable; preserve default response shape where possible.

## Completion notes
Closed 2026-05-25 14:12:26 MSK.

- Added configured aggregate Notepad encrypted-blob byte/count limits and bounded list responses with stable HTTP/WebSocket `507` quota errors.
- Added configured SMUGGLE temp artifact age/count/byte retention, startup cleanup reuse, and admission rejection without publishing partial temp pages.
- Added CLI/server constructor wiring, quota/retention regression tests, stale-doc/API mirror checks, and docs for upload, notes, and SMUGGLE storage limits.
- Verification report: `stage-reports/STAGE-002-20260525-141226.md`.
