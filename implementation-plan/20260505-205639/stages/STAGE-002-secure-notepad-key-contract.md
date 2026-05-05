# STAGE-002 - Fix Secure Notepad key contract and example interoperability

## Status
OPEN

## Priority
HIGH

## Source findings
- `codex-analysis/20260505-193249/project-analysis-report.md` - Critical & High Issues #1: Notepad key/API/example contract is inconsistent and recoverability is undefined.
- `codex-analysis/20260505-193249/agent-reports/websocket-engineer.md` - HIGH: example HKDF mismatch and session-key recoverability limits.
- `codex-analysis/20260505-193249/agent-reports/api-documenter.md` - HIGH: API omits exact HKDF parameters and recovery semantics.
- `codex-analysis/20260505-193249/agent-reports/qa-expert.md` - test gap: example only checked with `--help`.
- `codex-analysis/20260505-193249/agent-reports/reviewer.md` - HIGH blocker: example remains cryptographically incompatible.

## Goal
Make the Secure Notepad public contract explicit and interoperable: example, server/browser constants, API docs, and regression tests agree on HKDF parameters and current recoverability limits.

## Non-goals
- Do not implement durable key recovery across reload/restart in this stage.
- Do not encrypt note titles in this stage.
- Do not redesign the WebSocket save protocol; that is STAGE-010.

## Scope
### Likely files to inspect
- `src/security/keys.py` - canonical HKDF salt/info and server key exchange behavior.
- `src/data/static/ui/notepad.js` - browser-side HKDF constants and key lifetime.
- `src/notepad_service.py` - persisted ciphertext and plaintext metadata shape.
- `examples/notepad_client.py` - public client example with mismatched HKDF parameters.
- `API.md` and `docs/api.md` - public Secure Notepad contract.
- `tests/test_security/test_keys.py`, `tests/test_websocket_handlers.py`, `tests/test_handlers/test_notepad.py` - existing Notepad/key tests.

### Likely files to change
- `examples/notepad_client.py` - use the same HKDF salt/info as server/browser.
- `API.md` - document exact salt, info, AES-GCM body field, plaintext metadata, `sessionId` audit-only semantics, and current key-loss limits.
- `docs/api.md` - regenerate/sync from `API.md`.
- `tests/test_security/test_keys.py` or a new focused test - prove example/server-compatible derivation.
- `tests/test_cli.py` or smoke tests - keep `examples/notepad_client.py --help` passing if touched.

### Files that must not be changed
- `uploads/**`, `notes/**` - runtime/user data.
- `src/security/crypto.py` - no general crypto primitive rewrite is needed.
- `.env*`, credentials, keys, certificates - never read or edit secrets.

## Dependencies
- Depends on: STAGE-001
- Blocks: STAGE-009, STAGE-010

## Implementation steps
1. Identify canonical constants in `src/security/keys.py` and browser `notepad.js`.
2. Update `examples/notepad_client.py` to use exactly the canonical HKDF salt and info.
3. Add a regression test that derives a key using the example-compatible path and server constants, ideally with fixed key material or a controlled ECDH flow.
4. Add an API subsection near Notepad key exchange that states exact HKDF parameters, key lifetime/recoverability limits, encrypted vs plaintext fields, and server inability to decrypt/re-key notes.
5. Run docs sync so `API.md` and `docs/api.md` stay consistent.

## Acceptance criteria
- [ ] `examples/notepad_client.py` uses the same HKDF salt/info as server and browser.
- [ ] A regression test fails on the old example constants and passes with the fixed constants.
- [ ] `API.md` documents the current session-key-bound recoverability limitation without promising durable decryptability.
- [ ] `API.md` states that note body `data` is encrypted and title metadata is plaintext/server-visible.
- [ ] `docs/api.md` is synchronized with `API.md`.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `pytest -q tests/test_security/test_keys.py tests/test_handlers/test_notepad.py tests/test_websocket_handlers.py` | Passes, including new interoperability coverage |
| Example sanity | `python examples/notepad_client.py --help > /dev/null` | Exits 0 |
| Docs sync | `python tools/sync_docs.py --check` | Reports mirrors in sync |
| Static docs review | Inspect Notepad section in `API.md` | Exact HKDF salt/info and recovery limits are visible |

## Suggested subagents
- `explorer` - map all Notepad key constants and docs mentions before edits.
- `worker` - update example, docs, and tests in one bounded patch.
- `api-documenter` - review public API wording for consumer clarity.

## Risks and rollback
- Risk: Tests using real ECDH can become flaky if they rely on random values without stable assertions.
- Rollback: Revert example/docs/test changes and restore previous docs sync output.

## Completion notes
Filled by `close-plan-stage`.
