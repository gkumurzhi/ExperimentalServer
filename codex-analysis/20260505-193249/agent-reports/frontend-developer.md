# frontend-developer Report
_Generated: 2026-05-05 20:06:00 Europe/Moscow_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260505-193249/analysis-plan.md_

## Summary

Read-only frontend audit completed. I did not write files or run tests, to respect the "read-only only" instruction.

The bundled UI has good baseline coverage for request runner, upload/files, opsec, inspector redaction, notepad happy path, WebSocket save, localization, and some keyboard/focus behavior. The main risks are not broad XSS in the current `innerHTML` sites, but misleading Secure Notepad/TLS messaging and notepad state integrity around dirty edits, WebSocket reconnects, and plaintext title metadata.

## Documentation Checks

No new Context7/browser documentation check was needed. Findings are based on local code, tests, and the already-confirmed project plan context.

## Detailed Findings

Frontend boundaries:
- `src/data/index.html:496-504` loads `core`, dialogs, inspector, upload, requests, files, opsec, notepad, then bootstrap.
- `src/data/static/ui/core.js:615-834` owns i18n, tabs, live regions, server PING capability detection.
- `src/data/static/ui/inspector.js:4-28`, `57-185`, `445-497` owns redaction and request/response inspector rendering.
- `src/data/static/ui/requests.js:23-58`, `1723-1884` owns request-runner scenarios, expected statuses, and batch state.
- `src/data/static/ui/upload.js:164-385`, `files.js:125-667`, `opsec.js:317-592`, and `notepad.js:431-1055` own the major user workflows.

Positive checks:
- Current app `innerHTML` sinks are mostly escaped or controlled. Dynamic file names, note titles, response text, and inspector body content flow through `esc()` or `textContent` in the reviewed call sites.
- Inspector redaction is deliberate: secret key names include `d`, `data`, `k`, `key`, public keys, session IDs, cookies, auth headers in `inspector.js:4-28`; tests assert opsec/notepad redaction in `tests/test_ui_inspector_redaction.py:192-246`.
- Browser smoke is broad and covers upload, files, request batch, opsec transport warnings, notepad HTTP/WS happy paths, dialogs, live regions, and mobile layout in `tools/browser_smoke.playwright.js:2406-2719`.

## Issues Found

- [MEDIUM] Secure Notepad privacy copy is misleading for titles.
  - File/area: `src/data/static/ui/core.js`, `src/data/static/ui/notepad.js`, `src/notepad_service.py`
  - Evidence: The UI strings describe "End-to-end encrypted notes" in `core.js:551`, but `notepad.js:699` sends `title` as plaintext next to encrypted `data`, and the backend stores it in metadata at `src/notepad_service.py:185-188`. Redaction tests also intentionally keep title visible at `tests/test_ui_inspector_redaction.py:245-246`.
  - Impact: Users may put sensitive content in note titles believing the whole note is end-to-end encrypted.
  - Confidence: high

- [MEDIUM] Dirty notepad edits can be lost on note switching/new note before debounce save finishes.
  - File/area: `src/data/static/ui/notepad.js`
  - Evidence: Inputs mark dirty and schedule delayed save in `notepad.js:278-297`, but `notepadLoadNote()` overwrites title/body and clears dirty in `notepad.js:787-830` without flushing or confirming pending edits. `notepadNewNote()` clears the editor and timer in `notepad.js:842-850` with no dirty guard.
  - Impact: A user can lose recent edits by switching notes or starting a new note before the debounce save completes.
  - Confidence: high

- [MEDIUM] WebSocket notepad reconnect has no save retry/idempotency.
  - File/area: `src/data/static/ui/notepad.js`
  - Evidence: WS save is fire-and-wait in `notepad.js:688-696`; reconnect only reopens the socket in `notepad.js:549-572`. There is no operation id, ack tracking, dirty retry, or HTTP fallback if the socket closes after send but before `saved`.
  - Impact: Network instability can lose saves or duplicate first-save side effects.
  - Confidence: medium

- [MEDIUM] Stale `exphttp[crypto]` UI strings remain.
  - File/area: `src/data/static/ui/core.js`, `tools/browser_smoke.playwright.js`
  - Evidence: `[crypto]` is empty in `pyproject.toml:49-50`, but frontend unavailable strings still say `exphttp[crypto]` in `core.js:257`, `277`, `552`, `572`, and smoke tests lock that wording in `tools/browser_smoke.playwright.js:2677-2680`.
  - Impact: Users get a no-op remediation path, and smoke tests preserve the stale wording.
  - Confidence: high

- [LOW] TLS/sslip/ACME state is not surfaced in the UI.
  - File/area: `src/data/index.html`, `src/data/static/ui/core.js`, `src/server.py`
  - Evidence: The top bar only shows "Local console", host, and uploads scope in `index.html:25-36`; `core.js:728-733` only mirrors `location.host`. There are no UI matches for TLS/ACME/sslip, while server startup has TLS/sslip details in `src/server.py:361-377`.
  - Impact: Public TLS/sslip deployments can still look like a local console, making operator state less obvious.
  - Confidence: high

- [LOW] WS load contract is implemented server-side but unused by the UI.
  - File/area: `src/handlers/notepad.py`, `src/data/static/ui/notepad.js`, `tools/browser_smoke.playwright.js`
  - Evidence: Server supports WS `load` in `src/handlers/notepad.py:286`, `350-360`, but `notepadLoadNote()` always uses HTTP in `notepad.js:787-800`. Smoke switches back to HTTP before loading a WS-saved note at `tools/browser_smoke.playwright.js:2572-2574`.
  - Impact: The UI does not exercise the full advertised WS contract, leaving drift risk.
  - Confidence: high

- [LOW] `innerHTML` remains regression-prone despite current escaping.
  - File/area: `src/data/static/ui/dialogs.js`
  - Evidence: Shared `openManagedDialog()` accepts arbitrary markup and assigns it directly at `dialogs.js:69-72`. Current callers escape dynamic values, but there is no DOM XSS smoke using hostile filenames/note titles.
  - Impact: Future caller mistakes could become DOM XSS, and current smoke coverage would not systematically catch it.
  - Confidence: medium

## Concrete Recommendations

- Update notepad unavailable/requirement copy to "default install includes cryptography; repair/reinstall the server environment" and update smoke expectations.
- Add a visible notepad metadata warning or encrypt titles too. If titles stay plaintext, label the title as server-visible metadata.
- Add a notepad dirty-transition guard before New, Load, Clear, Delete-selected, and transport switches: flush save first or confirm discard.
- Add WS operation IDs and ack/retry behavior; on reconnect, resend dirty/unacked saves or fall back to HTTP.
- Expose transport metadata from PING or infer from `location.protocol`, then show `HTTP`/`HTTPS`, `WS`/`WSS`, and sslip/ACME status without saying "Local" on public hosts.
- Either route note load over WS when WS is selected or document/remove the unused WS load path.

## Quick Wins

- Replace all remaining `exphttp[crypto]` strings.
- Add browser smoke cases for note titles and upload filenames containing `<`, `"`, `'`, and `&`.
- Add a smoke test for dirty edit -> immediate note switch/new note.
- Add a small contract test comparing browser HKDF constants in `notepad.js:501-507` with server constants in `src/security/keys.py:41-42`.
- Fix `examples/notepad_client.py:118-123` HKDF salt/info mismatch; browser UI currently matches the server.

## Deeper Improvements

- Move high-risk generated HTML to DOM-building helpers or typed template helpers that require explicit escaping.
- Introduce a notepad state machine for `clean/dirty/saving/loading/reconnecting/unavailable`.
- Decide on durable Secure Notepad key strategy for server restart/browser reload, or clearly frame notes as session-key-bound.
- Tighten CSP after reducing `innerHTML` and inline allowances.

## Open Questions

- Are note titles intended to be private, or only note bodies?
- Should notes remain decryptable after server restart and browser reload?
- Is the bundled UI expected to be safe for public TLS/sslip deployments, or only a local admin console?
- Should WebSocket be the primary transport for every notepad operation when selected?
