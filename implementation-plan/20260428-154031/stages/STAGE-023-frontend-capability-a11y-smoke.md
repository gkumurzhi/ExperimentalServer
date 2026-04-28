# STAGE-023 — Align UI Capabilities, A11y, and Smoke Checks

## Status
OPEN

## Priority
MEDIUM

## Source findings
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/frontend-developer.md` — MEDIUM: advanced upload UI ignores server capability flag; notepad statuses lack live announcements; smoke assertion can pass incorrectly

## Goal
The UI reflects server advanced-upload capability, announces key notepad states accessibly, and smoke tests catch the relevant regressions.

## Non-goals
- Do not fix inspector redaction; STAGE-006 owns that.
- Do not change server capability payload except if a missing field is found.

## Scope
### Likely files to inspect
- `src/data/index.html` — advanced tab and status elements
- `src/data/static/ui/core.js` — `PING` handling
- `src/data/static/ui/opsec.js` — advanced upload flow
- `src/data/static/ui/notepad.js` — status updates
- `tools/browser_smoke.playwright.js` — smoke helpers and waits

### Likely files to change
- `src/data/index.html` and UI JS — disable/hide/explain advanced upload based on `PING.advanced_upload`
- `src/data/index.html`/`notepad.js` — `role="status"`, `aria-live`, `aria-atomic` for state updates
- `tools/browser_smoke.playwright.js` — fix `assertRequestPreviewToggleState`, asset checks, remove fixed sleeps

### Files that must not be changed
- `uploads/**` — runtime user data; do not inspect contents unless an explicit disposable test fixture is created
- `notes/**` — encrypted runtime note data; do not inspect contents
- `.env*`, `*.key`, `*.pem`, `*.p12`, `*.pfx`, credential JSON — secret-heavy files
- `codex-analysis/**` — source analysis artifacts; read-only evidence only
- `implementation-plan/**` — planning artifacts; close-plan-stage may update status/report files only

## Dependencies
- Depends on: STAGE-005, STAGE-006
- Blocks: None

## Implementation steps
1. Read `PING.advanced_upload` and set the advanced upload UI state accordingly.
2. Add live-region semantics to notepad connection/save indicators without noisy announcements.
3. Fix smoke helper arguments so checked/visible expectations are actually asserted.
4. Add smoke checks for loaded static UI scripts and redaction/capability states; replace fixed sleeps with concrete readiness conditions.

## Acceptance criteria
- [ ] Advanced upload UI is unavailable or explanatory when server support is off.
- [ ] Notepad status changes are exposed to assistive technology.
- [ ] Smoke helper fails when the expected checked/visible state is wrong.
- [ ] Smoke checks include referenced static UI assets.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `node tools/browser_smoke.playwright.js` or project browser smoke wrapper if available | Browser smoke passes and covers new states |
| Type/lint/build | `python -m compileall src tests` | Python compilation succeeds |
| Manual/static review | Inspect ARIA/status and capability handling | UI state derives from `PING.advanced_upload` |

## Suggested subagents
- `frontend-developer` — UI behavior.
- `accessibility-tester` — status/live-region audit.
- `qa-expert` — smoke reliability.

## Risks and rollback
- Risk: Changing visibility of advanced tab may surprise users who expect it always visible.
- Rollback: Revert UI/smoke changes for this stage.

## Completion notes
Filled by `close-plan-stage`.
