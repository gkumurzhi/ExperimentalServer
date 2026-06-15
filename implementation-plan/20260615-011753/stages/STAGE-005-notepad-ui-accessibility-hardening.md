# STAGE-005 - Notepad UI and accessibility hardening

## Status
OPEN

## Priority
MEDIUM

## Source findings
- `codex-analysis/20260614-225437/agent-reports/frontend-developer.md` - Issues 1-4: Notepad UI ignores `note_delete`/`note_clear`, warning text is not rendered, quota errors need better guidance, browser smoke is lab-only.
- `codex-analysis/20260614-225437/agent-reports/accessibility-tester.md` - P1/P2: Notepad textarea lacks explicit label, recovery warning is not accessible, upload/progress and WS errors need better live feedback.
- `codex-analysis/20260614-225437/project-analysis-report.md` - Frontend & UX: fix Notepad controls before workspace default migration.

## Goal
Make the bundled static UI honor fine-grained Notepad capabilities and surface Notepad recovery/error state accessibly without adding a frontend build pipeline.

## Non-goals
- Do not add durable Notepad recovery.
- Do not redesign the UI or introduce a frontend framework/build step.
- Do not change the default profile.

## Scope
### Likely files to inspect
- `src/data/index.html` - Notepad controls, textarea, status regions, labels.
- `src/data/static/ui/notepad.js` - capability checks, save/delete/clear behavior, error handling.
- `src/data/static/ui/core.js` - translations, capability ingestion, live-region helper.
- `src/data/static/ui/dialogs.js` - focus restore behavior for destructive confirmations.
- `tools/browser_smoke.playwright.js` - existing Notepad and a11y smoke assertions.
- `tests/test_websocket_handlers.py`, `tests/test_handlers/test_notepad.py` - server capability contracts if UI changes expose missing behavior.

### Likely files to change
- `src/data/index.html` - add hidden textarea label and visible Notepad ephemeral warning tied with `aria-describedby`.
- `src/data/static/ui/notepad.js` - gate delete/clear controls with `note_delete`/`note_clear`, improve server/quota error display, maintain focus after bulk destructive flows.
- `src/data/static/ui/core.js` - add or reuse localized text for labels/status messages.
- `tools/browser_smoke.playwright.js` - add assertions for warning, label, destructive capability states, and relevant live/status messages.

### Files that must not be changed
- `src/notepad_service.py` - storage/durability is out of scope unless tests reveal a server contract bug.
- `src/features.py` - capability definitions/defaults are STAGE-003/004.
- `.github/workflows/**` - CI lane changes are STAGE-006.
- `.env*`, credentials, keys, certificates - secrets are out of scope.

## Dependencies
- Depends on: STAGE-003
- Blocks: STAGE-006

## Implementation steps
1. Map current UI Notepad affordances to `note_http`, `note_delete`, `note_clear`, and `websocket_notes`.
2. Render the existing Notepad ephemeral/recovery warning in the Notepad panel and connect it to title/body controls with accessible descriptions.
3. Add an explicit hidden label for the Notepad textarea.
4. Gate delete and clear controls on `note_delete` and `note_clear`, not just coarse Notepad availability.
5. Improve Notepad save/error status so quota/server error text is visible and announced.
6. Add smoke assertions for warning text, labels, destructive capability states, and focus recovery where practical.

## Acceptance criteria
- [ ] Notepad delete and clear controls obey `note_delete` and `note_clear` independently.
- [ ] The Notepad ephemeral/recovery warning is visible and accessible.
- [ ] `notepadTextarea` has an explicit accessible label.
- [ ] Notepad quota/server errors surface useful text through visible/status UI.
- [ ] Destructive confirm success paths leave focus on a stable control or have a tested focus behavior.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Static UI asset check | `python tools/check_static_ui_assets.py --repo-root .` | Exits 0. |
| Targeted tests | `python -m pytest tests/test_handlers/test_notepad.py tests/test_websocket_handlers.py` | Exits 0 if server contracts are touched; otherwise no unrelated failures. |
| Browser smoke | `python tools/browser_smoke.py` | Exits 0 where Playwright/browser dependencies are available. |
| Manual/static review | Inspect Notepad labels, warning, capability gates, and live/status output | UI remains static/no-build and capability-driven. |

## Suggested subagents
- `explorer` - map UI capability/state flow before edits.
- `worker` - implement UI/a11y changes and smoke assertions.
- `accessibility-reviewer` - review label, warning, focus, and status behavior if available.

## Risks and rollback
- Risk: UI changes can break lab Notepad happy path or smoke expectations.
- Rollback: revert static UI and smoke changes from this stage and rerun `python tools/check_static_ui_assets.py --repo-root .`.

## Completion notes
Filled by `close-plan-stage`.
