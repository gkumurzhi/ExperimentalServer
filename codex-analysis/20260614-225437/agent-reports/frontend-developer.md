# frontend-developer Report
_Generated: 2026-06-15 00:46:31 Europe/Moscow_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/analysis-plan.md_

## Summary
I could not invoke a separate `frontend-developer` subagent from this session, so I completed the same read-only frontend audit directly.

The bundled static UI is directionally coherent for the current lab-first product, and most capability-driven affordances are already wired to `PING`. The main frontend risks are profile coverage gaps for a future `workspace` default, under-surfaced Notepad recoverability/quota failures, and Notepad UI using only coarse `note_http` availability instead of the full `note_delete` / `note_clear` capability contract.

## Documentation Checks
Read first: the requested analysis plan and six completed reports under `codex-analysis/20260614-225437`.

Non-mutating checks run:
- `python tools/sync_docs.py --check` failed: `API.md -> docs/api.md` and `CONTRIBUTING.md -> docs/contributing.md` are out of sync.
- `python tools/check_static_ui_assets.py --repo-root .` passed.

No browser/server run was needed for this read-only pass.

## Detailed Findings
UI boundaries are clear:
- `src/data/index.html` owns static DOM and script order.
- [core.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/core.js:815) owns `PING` capability ingestion, supported methods, tab state, i18n, and live-region helper.
- [requests.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/requests.js:1810) owns the request console and `sendCustomRequest`.
- [upload.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/upload.js:43), [files.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/files.js:26), [opsec.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/opsec.js:32), and [notepad.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/notepad.js:61) own their feature surfaces.
- [inspector.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/inspector.js:4) owns raw/summary exchange rendering and redaction.

Capability exposure is mostly accurate:
- Server profiles expose fixed booleans via [features.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/features.py:47), and `PING` returns `profile`, `supported_methods`, and `capabilities` in [info.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/info.py:101).
- Request method buttons disable from `supported_methods` in [core.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/core.js:784) and [requests.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/requests.js:272).
- Ordinary upload, file delete, clear uploads, SMUGGLE, and advanced upload all use capability checks.

Destructive operations are visible:
- File delete, selected delete, clear uploads, note delete, selected note delete, and note clear use confirmation dialogs.
- Failure notices exist for delete/clear paths, for example [files.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/files.js:519) and [notepad.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/notepad.js:1379).

WebSocket state is visible but still lab-grade:
- The UI shows connection status via `#notepadConnStatus`, reconnects on close, and falls back pending saves to HTTP after lost ack paths in [notepad.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/notepad.js:680) and [notepad.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/notepad.js:877).
- Existing smoke covers lost-ack retry and stale-load protection in [browser_smoke.playwright.js](/home/user/PycharmProjects/ExperimentalHTTPServer/tools/browser_smoke.playwright.js:2343).

No-build static UI is still reasonable now:
- Package data explicitly includes `data/*.html`, `data/static/*`, and `data/static/ui/*` in [pyproject.toml](/home/user/PycharmProjects/ExperimentalHTTPServer/pyproject.toml:86).
- CI/release validate static assets, JS syntax, wheel packaging, and installed-wheel browser smoke in [.github/workflows/ci.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/.github/workflows/ci.yml:173) and [.github/workflows/release.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/.github/workflows/release.yml:97).

## Issues Found
1. Medium: Notepad UI does not honor `note_delete` and `note_clear` independently. It enables delete/clear from `notepadAvailable`, not those capability booleans, in [notepad.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/notepad.js:212). Server enforces them separately in [notepad.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/notepad.py:94).

2. Medium: Notepad non-durable recovery risk is not visibly surfaced. API says reload/restart/session expiry can leave note bodies undecryptable in [API.md](/home/user/PycharmProjects/ExperimentalHTTPServer/API.md:467). The warning string exists only as translation text in [core.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/core.js:580) and is not rendered.

3. Medium: quota errors are visible as raw errors but not recoverable guidance. Upload/Notepad/SMUGGLE return `413`/`507` contracts, but Notepad save failures collapse to `Save error` in [notepad.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/notepad.js:1004) and [notepad.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/notepad.js:955).

4. Medium: browser smoke is lab-only. The smoke server hardcodes `profile="lab"` in [browser_smoke.py](/home/user/PycharmProjects/ExperimentalHTTPServer/tools/browser_smoke.py:78), so `serve`/`workspace` disabled states are not release-protected.

5. Low: ordinary upload disabled drag/drop is weaker than advanced upload. `handleFiles()` returns early when disabled, but dragover/drop still run in [upload.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/upload.js:178); advanced upload explicitly blocks those paths.

## Concrete Recommendations
Immediate:
- Fix docs mirror drift.
- Gate Notepad delete/clear controls with `note_delete` and `note_clear`.
- Render a clear Notepad ephemeral-key warning in the Notepad panel.
- Add quota-specific UI copy for `413` and `507` in upload, advanced upload, Notepad save, and SMUGGLE flows.

Short term:
- Add `--profile` support to `tools/browser_smoke.py`.
- Keep full lab smoke, then add minimal `serve` and `workspace` smoke assertions for disabled methods, upload availability, clear upload disabled, advanced upload notice, and Notepad unavailable state.
- Normalize disabled drag/drop behavior between ordinary upload and advanced upload.

Medium term:
- Introduce a small frontend capability/action manifest consumed by tabs, controls, request panel, and smoke assertions.
- Keep no-build static UI until product scope requires richer routing/state tooling; do not add a build pipeline just for the planned `workspace` migration.

## Quick Wins
- Use `note_delete` / `note_clear` in `refreshNotepadCapability()`.
- Add visible `notepadEphemeralWarning` near the metadata hint.
- Parse error bodies on Notepad save failures and display the server message.
- Add one smoke path for `profile="workspace"`.

## Deeper Improvements
- Define a stable frontend capability schema aligned with future API v1.
- Add recovery-oriented Notepad UX only after a crypto/product ADR.
- If Notepad becomes a durable workspace, move from ad hoc globals toward explicit state transitions for session, editor, save, load, and socket state.

## Open Questions
- Should unavailable tabs be hidden, disabled, or reachable with an explanatory notice?
- Is Notepad an ephemeral lab scratchpad or a durable secure workspace?
- Should `workspace` become the default in the next compatibility release?
- At what UI size or product scope should the project adopt a build pipeline?
