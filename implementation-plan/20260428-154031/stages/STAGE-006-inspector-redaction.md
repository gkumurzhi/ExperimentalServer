# STAGE-006 — Redact Inspector Raw and Copy Output

## Status
CLOSED

## Priority
HIGH

## Source findings
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/frontend-developer.md` — HIGH: advanced-upload raw inspector/copy exposes passwords and payload fields
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/project-analysis-report.md` — Security & Compliance: frontend inspector retains/copies raw secrets

## Goal
Inspector display and copy paths redact advanced-upload secrets, payloads, and sensitive notepad fields by default.

## Non-goals
- Do not make a new UI design system.
- Do not change server-side cryptographic behavior.
- Do not expose runtime user data contents during testing.

## Scope
### Likely files to inspect
- `src/data/static/ui/inspector.js` — redaction and raw rendering paths
- `src/data/static/ui/opsec.js` — advanced-upload payload/key construction
- `src/data/static/ui/notepad.js` — note/session trace payloads
- `src/data/static/ui/requests.js` — copy/clipboard state
- `tools/browser_smoke.playwright.js` — smoke coverage

### Likely files to change
- `src/data/static/ui/inspector.js` — central redaction for render and copy
- `src/data/static/ui/requests.js` — remove or gate raw clipboard state
- `src/data/static/ui/opsec.js` and `notepad.js` — pass structured fields safely if needed
- `tools/browser_smoke.playwright.js` — add redaction regression

### Files that must not be changed
- `uploads/**` — runtime user data; do not inspect contents unless an explicit disposable test fixture is created
- `notes/**` — encrypted runtime note data; do not inspect contents
- `.env*`, `*.key`, `*.pem`, `*.p12`, `*.pfx`, credential JSON — secret-heavy files
- `codex-analysis/**` — source analysis artifacts; read-only evidence only
- `implementation-plan/**` — planning artifacts; close-plan-stage may update status/report files only

## Dependencies
- Depends on: STAGE-005
- Blocks: None

## Implementation steps
1. Create one redaction function used before both raw display and copy/clipboard test state.
2. Redact advanced-upload `k`, `x-k`, `d`, `x-d-*`, URL `k`, URL `d`, and body/header preview payload equivalents.
3. Redact notepad `sessionId`, key-exchange material, and note `data` in default raw/copy views.
4. Add smoke/unit coverage that raw/copy output does not contain a test password or raw base64 payload.

## Acceptance criteria
- [x] Advanced-upload passwords and file payloads do not appear in rendered inspector raw view.
- [x] Copied/recorded inspector state is redacted by the same policy.
- [x] Notepad session/key/data fields are redacted unless an explicit unsafe mode is added and documented.
- [x] Smoke or unit tests cover the redaction path.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `pytest tests -q -k "browser_smoke or ui or inspector"` or run the browser smoke target if available | Inspector redaction coverage passes |
| Type/lint/build | `python -m compileall src tests` | Compilation succeeds |
| Manual/static review | Search for raw assignment/copy paths in UI files | No bypass of centralized redaction remains |

## Suggested subagents
- `frontend-developer` — implement UI redaction.
- `security-auditor` — review sensitive-field list.

## Risks and rollback
- Risk: Tests that expect exact wire payloads may need explicit unsafe/test-only mode.
- Rollback: Revert inspector/redaction and smoke-test changes for this stage.

## Completion notes
Closed 2026-04-28 21:46:30 MSK. `src/data/static/ui/inspector.js` now centralizes redaction for rendered raw output, copy source text, and stored inspector state. The policy covers advanced-upload URL/header/body payload fields (`d`, `k`, `x-d`, `x-d-*`, `x-k`) and notepad `sessionId`, key material, and `data` fields by default. Added `tests/test_ui_inspector_redaction.py` to execute the real inspector JS in a Node VM and assert advanced-upload/notepad render, copy, raw transcript, and stored-state redaction without reading runtime `notes/` or `uploads/` data. Verification passed: `.venv/bin/pytest tests -q -k "browser_smoke or ui or inspector"` (`28 passed, 521 deselected`), `.venv/bin/pytest tests/test_ui_inspector_redaction.py -q` (`2 passed`), `python -m compileall src tests`, `.venv/bin/ruff check tests/test_ui_inspector_redaction.py`, UI `node --check` commands, `.venv/bin/python tools/browser_smoke.py`, static raw/copy path review, and verifier subagents.
