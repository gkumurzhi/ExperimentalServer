# accessibility-tester Report
_Generated: 2026-06-15 00:42:27 Europe/Moscow_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/analysis-plan.md_

## Summary

Scope analyzed: static browser UI under `src/data/index.html` and `src/data/static/ui/*`, browser smoke tooling, `README.md`, `API.md`, and the requested plan/reports. The `frontend-developer.md` report was not present, so I did not wait for it. No files were modified.

Overall: the UI has a meaningful accessibility foundation: ARIA tab patterns, live status regions, labelled icon buttons, keyboard-triggered drop zones, focus-visible styling, and managed dialogs. The main gaps are Notepad-specific labelling/recovery messaging, upload per-file announcements, profile-disabled coverage, and a few focus/error-detail edge cases.

## Documentation Checks

- Read the source plan and completed `product-manager` / `qa-expert` reports. Both point toward a possible `workspace` default and note browser/accessibility coverage risk.
- Confirmed current docs mirror drift with `python tools/sync_docs.py --check`: `API.md -> docs/api.md` and `CONTRIBUTING.md -> docs/contributing.md` are out of sync.
- `python tools/check_static_ui_assets.py` passed.
- API docs clearly warn that Notepad keys are session-bound and not durably recoverable in [API.md](/home/user/PycharmProjects/ExperimentalHTTPServer/API.md:467). The browser UI does not render the existing `notepadEphemeralWarning` translation key; only the docs carry the full recovery warning.

## Detailed Findings

Controls are mostly keyboard-reachable and labelled. Examples: tab buttons use `role="tab"`/`aria-selected` in [index.html](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/index.html:192), arrow-key navigation is implemented in [core.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/core.js:1037), drop zones are keyboard-triggered in [upload.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/upload.js:78), and file action buttons get per-file `aria-label`s in [files.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/files.js:183).

Dynamic state support exists. Shared live regions are declared in [index.html](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/index.html:238) and updated through `announceLiveRegion()` in [core.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/core.js:863). Notepad save and connection state use `role="status"` in [index.html](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/index.html:437) and are updated in [notepad.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/notepad.js:408).

Destructive actions are generally handled well. Confirmation dialogs use `role="alertdialog"`, `aria-modal`, labelled/described content, initial focus, Escape, and Tab trapping in [dialogs.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/dialogs.js:94) and [dialogs.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/dialogs.js:151). File delete/clear flows also refocus the browser path input after completion in [files.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/files.js:398).

Coverage exists but is lab-centric. Browser smoke starts the temporary server with `profile="lab"` in [browser_smoke.py](/home/user/PycharmProjects/ExperimentalHTTPServer/tools/browser_smoke.py:78). It checks live-region contracts, dialog keyboard behavior, file action names, Notepad unavailable state, and WebSocket retry behavior, but it does not cover `serve`/`workspace` profile-disabled UX.

## Issues Found

P1: Notepad textarea lacks an explicit accessible label. The title input has a hidden label, but `notepadTextarea` only has a placeholder in [index.html](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/index.html:459). Add a real hidden label and connect warning text with `aria-describedby`.

P1: Notepad recovery risk is documented but not accessible in the UI. `API.md` warns note bodies may become undecryptable after reload/restart/session expiry, while `notepadEphemeralWarning` exists in translations but is unused. This is a user-impact risk for screen-reader and sighted users alike.

P2: Upload queue progress/failure detail is partly visual-only. Per-file status and progress are rendered in [upload.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/upload.js:245), but the progress bar has no `role="progressbar"` and live output only announces start/final counts in [upload.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/upload.js:310).

P2: WebSocket/Notepad server errors collapse to generic "error" announcements. Failed WS save/error messages call `notepadSetStatus('error')` in [notepad.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/notepad.js:956), but the actual server error text is not announced.

P2 risk hypothesis: focus may be lost after Notepad bulk destructive confirms. The shared dialog restores focus on cancel, not normal confirm, unless requested in [dialogs.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/dialogs.js:21). Notepad selected-delete/clear success paths do not explicitly refocus a stable control in [notepad.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/notepad.js:1295) and [notepad.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/notepad.js:1376). Needs runtime confirmation.

## Concrete Recommendations

Immediate: add an explicit hidden label for `notepadTextarea`, render the Notepad session-loss/recovery warning in the Notepad panel, and attach it via `aria-describedby` to the title and body controls.

Short: add concise live announcements for active upload filename/progress milestones and per-file failures; add actual WebSocket/Notepad error text to a status live region.

Short: extend browser smoke to run minimal `workspace` and `serve` checks: disabled/unavailable Notepad and lab-only actions, keyboard tab order, accessible names, and live-region messages.

Medium: add automated a11y assertions to the Playwright smoke flow, then do one manual pass with NVDA/JAWS or VoiceOver plus keyboard-only navigation. Static review cannot validate real screen-reader announcement timing.

## Quick Wins

- Add `label for="notepadTextarea"` with localized text.
- Render `notepadEphemeralWarning`; the translation already exists.
- Include selected counts in bulk-delete button labels.
- Add focus assertions for Notepad selected-delete and clear flows.
- Add a smoke assertion that upload progress uses `role="progressbar"` or has an equivalent live summary.

## Deeper Improvements

- Define profile-disabled UX before changing default to `workspace`: hide unavailable lab features, or keep reachable explanatory notices consistently.
- Add contrast checks for both dark and light themes; current focus styles look intentional, but computed contrast was not browser-verified.
- Consider `inert`/background hiding for modals beyond the current focus trap and `aria-modal`.
- Add release-gating accessibility smoke for one normal path, one failure path, and one profile-disabled integration edge.

## Open Questions

- If `workspace` becomes default, should Notepad be hidden, disabled with explanation, or moved behind explicit `lab` affordance?
- Is Secure Notepad intended to remain ephemeral, or should UI copy prepare users for durable recovery work?
- Which browser/screen-reader pair should be the acceptance target?
- Should accessibility smoke become required in CI, or only in release validation?
