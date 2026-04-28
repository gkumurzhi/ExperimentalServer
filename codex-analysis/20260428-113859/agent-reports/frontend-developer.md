# frontend-developer Report
_Generated: 2026-04-28 12:46:14 MSK_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/analysis-plan.md_

## Summary

Read-only UI/server contract audit completed. I did not modify files and did not inspect `uploads/`, `notes/`, `.env*`, keys, certs, or credentials. I did inspect a few server/package lines needed to validate UI contract and packaging risk.

Highest-risk findings: `index.html` now depends on untracked `inspector.js`, and the raw/copy inspector path can expose advanced-upload passwords, payloads, notepad session IDs, note metadata, and ciphertext.

## Documentation Checks

Context7 was checked for Playwright docs and was quota-limited: “Monthly quota reached.” Fallback used only official Playwright docs:

- Playwright auto-waiting/actionability and auto-retrying assertions: https://playwright.dev/docs/actionability
- Playwright web-first assertions: https://playwright.dev/docs/api/class-playwrightassertions
- Playwright locators guidance: https://playwright.dev/docs/locators
- Playwright `waitForTimeout` and `networkidle` discouragement: https://playwright.dev/docs/next/api/class-page

`crypto-js.min.js` was treated only as an asset signal: tracked package asset loaded by `index.html`; no behavior findings depend on its minified contents.

## Issues Found

| Severity | Issue | Evidence | Confidence |
|---|---|---|---|
| HIGH | Required inspector asset is untracked, so a clean checkout/package can ship an `index.html` that loads a missing script. | [index.html](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/index.html:494) loads `/static/ui/inspector.js`; `git status` shows `?? src/data/static/ui/inspector.js`; package data only includes files present in the tree via [pyproject.toml](/home/user/PycharmProjects/ExperimentalHTTPServer/pyproject.toml:79). Feature flows call inspector APIs such as [upload.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/upload.js:249) and [opsec.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/opsec.js:47). | High |
| HIGH | Advanced-upload raw inspector/copy can expose password/key and file payload fields. | Redaction exists for exact header/body keys in [inspector.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/inspector.js:4), but raw JSON/text paths bypass it at [inspector.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/inspector.js:141) and [inspector.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/inspector.js:163). `opsec.js` places passwords into `k` at [opsec.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/opsec.js:287), headers/body-preview text at [opsec.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/opsec.js:320), URL query at [opsec.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/opsec.js:351), and JSON body at [opsec.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/opsec.js:382). Copied raw text is also stored on `window.__exphttpClipboardState` in [requests.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/requests.js:1357). | High |
| MEDIUM | Notepad inspector exposes audit/session and note data in default raw mode. | HTTP trace bodies are raw text in [notepad.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/notepad.js:56). Session exchange includes `clientPublicKey` and response `sessionId` around [notepad.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/notepad.js:457). WS save traces include `sessionId`, `title`, and `data` at [notepad.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/notepad.js:686). Server says session IDs are audit-only, not auth tokens, in [notepad.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/notepad.py:43), so severity is below the advanced-upload password leak. | High |
| MEDIUM | Advanced upload UI does not honor the server capability flag. | Server `PING` reports `advanced_upload` in [info.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/info.py:100), but `checkServerMode()` only handles `access_scope` in [core.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/core.js:773). The advanced tab is always rendered at [index.html](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/index.html:194), while unknown advanced-upload methods only dispatch when enabled in [handlers/__init__.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/__init__.py:61). | High |
| MEDIUM | Notepad save/connection statuses are visual, not live announcements. | `notepadConnStatus` and `notepadSaveIndicator` are plain spans in [index.html](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/index.html:433) and [index.html](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/index.html:454); state updates only mutate class/text/aria-label in [notepad.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/notepad.js:299). | Medium |
| MEDIUM | Smoke coverage misses the sensitive inspector cases and has one assertion that can pass while checking the opposite state. | Opsec smoke only checks transport auto-switch, not actual upload/redaction, in [browser_smoke.playwright.js](/home/user/PycharmProjects/ExperimentalHTTPServer/tools/browser_smoke.playwright.js:2286). `assertRequestPreviewToggleState(expectedChecked, expectedVisible)` ignores its parameters and always expects the section visible in [browser_smoke.playwright.js](/home/user/PycharmProjects/ExperimentalHTTPServer/tools/browser_smoke.playwright.js:370). | High |
| LOW | Smoke has fixed sleeps. | [browser_smoke.playwright.js](/home/user/PycharmProjects/ExperimentalHTTPServer/tools/browser_smoke.playwright.js:2544) and [browser_smoke.playwright.js](/home/user/PycharmProjects/ExperimentalHTTPServer/tools/browser_smoke.playwright.js:2553). Official Playwright docs discourage `waitForTimeout` outside debugging. | High |

## Recommendations

- Track `src/data/static/ui/inspector.js` or remove the `index.html` dependency before release.
- Centralize redaction before both render and copy. Sanitize headers, JSON bodies, preview text, `rawText`, and URL query params.
- For advanced upload, display payload fields as size/hash summaries; redact `k`, `x-k`, `d`, `x-d-*`, URL `d`, and URL `k`.
- For notepad, redact `sessionId`, `clientPublicKey`, `serverPublicKey`, and `data` in raw/copy views unless an explicit unsafe “show exact wire payload” mode is intended.
- Remove or test-gate `window.__exphttpClipboardState`; production code should not retain copied raw payloads.
- Use `PING.advanced_upload` to disable or explain the advanced-upload tab when unsupported.
- Add `role="status" aria-live="polite" aria-atomic="true"` to notepad save/connection state.

## Quick Wins

- Fix `assertRequestPreviewToggleState` to actually assert its `expectedChecked` and `expectedVisible` arguments.
- Add a smoke assertion that all loaded `/static/ui/*.js` responses are `200`, including `inspector.js`.
- Add one smoke path for advanced upload with encryption + send key, then assert raw/copy does not contain the password or raw base64 payload.
- Replace the two `waitForTimeout(100)` calls with a concrete app-ready condition.

## Open Questions

- Should raw inspector be exact wire payload, or safe shareable output by default?
- Is notepad title metadata considered sensitive?
- Should advanced upload be hidden, disabled, or left visible with an unavailable state when server support is off?
- Is `window.__exphttpClipboardState` intended only for smoke tests?
