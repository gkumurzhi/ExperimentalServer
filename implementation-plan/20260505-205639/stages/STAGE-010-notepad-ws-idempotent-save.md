# STAGE-010 - Make Notepad WebSocket saves idempotent

## Status
CLOSED

## Priority
MEDIUM

## Source findings
- `codex-analysis/20260505-193249/project-analysis-report.md` - Frontend & UX: WS save has no operation id, ack tracking, retry, or fallback.
- `codex-analysis/20260505-193249/agent-reports/websocket-engineer.md` - MEDIUM: reconnect can churn sockets and duplicate create side effects.
- `codex-analysis/20260505-193249/agent-reports/frontend-developer.md` - MEDIUM: WebSocket notepad reconnect has no save retry/idempotency.

## Goal
Make WebSocket Notepad save/reconnect behavior robust against stale close events, lost save acknowledgements, and duplicate first-save side effects.

## Non-goals
- Do not change the Notepad HKDF/key contract.
- Do not implement durable notes across reload/restart.
- Do not make WebSocket the only transport for all Notepad operations unless required.

## Scope
### Likely files to inspect
- `src/data/static/ui/notepad.js` - WS connect, close, save, retry, and state handling.
- `src/handlers/notepad.py` - WS message handler and saved response contract.
- `src/notepad_service.py` - behavior when saving without note ID.
- `tests/test_websocket_handlers.py` - current WS save/list/load parity tests.
- `tools/browser_smoke.playwright.js` - browser WS Notepad smoke.

### Likely files to change
- `src/data/static/ui/notepad.js` - connection generation guard, pending operation tracking, retry/fallback.
- `src/handlers/notepad.py` - optional operation ID echo or idempotency support.
- `src/notepad_service.py` - optional client-generated note ID or idempotency semantics for creates.
- `tests/test_websocket_handlers.py` - server contract tests if protocol changes.
- `tools/browser_smoke.playwright.js` - browser-level reconnect/lost-ack smoke if feasible.
- `API.md` and `docs/api.md` - if WS message contract changes.

### Files that must not be changed
- `src/security/keys.py` - cryptographic contract is STAGE-002.
- `src/data/static/ui/core.js` copy-only changes unless needed for status text.
- `notes/**` - runtime/user note data.
- `.env*`, credentials, keys, certificates - never read or edit secrets.

## Dependencies
- Depends on: STAGE-009
- Blocks: `None`

## Implementation steps
1. Add a connection generation/token so stale `onclose` handlers cannot close or reconnect over the active socket.
2. Add client operation IDs or client-generated note IDs for create/save messages.
3. Echo/track acknowledgements so the UI can distinguish saved, pending, retryable, and failed states.
4. On reconnect, retry unacknowledged dirty saves or fall back to HTTP without duplicating first saves.
5. Update API docs if message shape changes.
6. Add targeted WS tests and a browser smoke scenario for lost ack/reconnect if feasible.

## Acceptance criteria
- [ ] Stale close events cannot churn a healthy current socket.
- [ ] A lost first-save acknowledgement does not create duplicate notes on retry.
- [ ] The UI resolves dirty/saving state after reconnect or fallback.
- [ ] Server/client WS contract tests cover operation ID or idempotency behavior.
- [ ] API docs are updated if the WS message contract changes.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| WS handler tests | `pytest -q tests/test_websocket_handlers.py tests/test_websocket.py` | Passes with idempotency/retry contract coverage |
| Browser smoke | `python tools/browser_smoke.py` if available | Passes and covers WS Notepad flow |
| API sync | `python tools/sync_docs.py --check` if API docs changed | Reports mirrors in sync |
| Manual simulation | Drop/close WS after send-before-ack in a controlled test or browser script | No duplicate note and dirty state is resolved |

## Suggested subagents
- `explorer` - trace current WS message flow and note ID creation semantics.
- `worker` - implement client/server protocol changes and tests.
- `websocket-engineer` - review idempotency, reconnect, and protocol compatibility.

## Risks and rollback
- Risk: Changing WS message shape can break custom clients.
- Rollback: Keep backward-compatible handling for old messages or revert protocol changes and use client-generated note IDs only.

## Completion notes
Closed 2026-05-21 20:14:58 MSK. Added idempotent first-save semantics with client-generated note IDs and `createIfMissing`, echoed WS `opId` acknowledgements, generation guards for stale socket handlers, pending-save retry on reconnect, and HTTP fallback for unacknowledged saves. Added WS/HTTP contract tests, browser lost-ack/reconnect smoke coverage, and updated API docs.
