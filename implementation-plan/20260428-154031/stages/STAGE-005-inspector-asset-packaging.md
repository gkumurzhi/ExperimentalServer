# STAGE-005 — Make Inspector Asset Intentional

## Status
CLOSED

## Priority
HIGH

## Source findings
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/frontend-developer.md` — HIGH: `index.html` depends on untracked `inspector.js`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/python-pro.md` — MEDIUM: referenced UI runtime asset is untracked

## Goal
Clean checkouts and built packages either include `inspector.js` or no longer reference it.

## Non-goals
- Do not fix inspector redaction leaks; STAGE-006 owns that.
- Do not redesign the UI module graph.

## Scope
### Likely files to inspect
- `src/data/index.html` — script reference
- `src/data/static/ui/inspector.js` — current untracked asset
- `src/data/static/ui/*.js` — inspector call sites
- `pyproject.toml` — package data patterns
- `tools/browser_smoke.playwright.js` — static asset smoke coverage

### Likely files to change
- `src/data/static/ui/inspector.js` — commit/keep intentionally or remove safely
- `src/data/index.html` and UI call sites — align with decision
- `tests/` or `tools/browser_smoke.playwright.js` — add static asset presence check

### Files that must not be changed
- `uploads/**` — runtime user data; do not inspect contents unless an explicit disposable test fixture is created
- `notes/**` — encrypted runtime note data; do not inspect contents
- `.env*`, `*.key`, `*.pem`, `*.p12`, `*.pfx`, credential JSON — secret-heavy files
- `codex-analysis/**` — source analysis artifacts; read-only evidence only
- `implementation-plan/**` — planning artifacts; close-plan-stage may update status/report files only

## Dependencies
- Depends on: None
- Blocks: STAGE-006, STAGE-022

## Implementation steps
1. Decide whether `inspector.js` is a first-class UI module or should be removed.
2. If keeping it, ensure it is tracked and included by package-data patterns; if removing it, remove script tags and call sites safely.
3. Add a package/static asset verification that referenced local scripts resolve.
4. Add a browser smoke assertion for `/static/ui/inspector.js` if kept.

## Acceptance criteria
- [ ] No tracked HTML references an absent static UI script.
- [ ] Clean checkout/package asset validation catches missing referenced scripts.
- [ ] Existing UI flows that call inspector APIs still work or degrade intentionally.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `pytest tests/test_server_routing.py tests/test_server_methods.py -q` plus relevant browser smoke if available | Static serving and UI asset checks pass |
| Type/lint/build | `python -m compileall src tests` | Compilation succeeds |
| Manual/static review | Compare `index.html` script tags to tracked/package data files | Every local script reference has a tracked asset |

## Suggested subagents
- `frontend-developer` — UI dependency review.
- `python-pro` — package-data verification.

## Risks and rollback
- Risk: Removing the asset may break request inspector features; keeping it exposes current redaction risks until STAGE-006.
- Rollback: Revert asset/script/call-site changes for this stage.

## Completion notes
Closed on 2026-04-28 21:26:57 MSK.

- Kept `src/data/static/ui/inspector.js` as an intentional bundled UI asset; it is tracked and covered by existing `pyproject.toml` package-data patterns.
- Added routing/static tests that parse bundled `index.html` script references and verify each local script resolves through `get_package_resource()`, is covered by package-data, and is tracked by Git.
- Added browser smoke coverage that fetches `/static/ui/inspector.js` and verifies the inspector API and initialized exchange scopes are available after SPA load.
- Verification passed: `.venv/bin/python -m pytest tests/test_server_routing.py tests/test_server_methods.py -q` (`65 passed`), `.venv/bin/python -m compileall src tests`, `.venv/bin/ruff check tests/test_server_routing.py`, `node --check tools/browser_smoke.playwright.js`, `.venv/bin/python tools/browser_smoke.py`, temporary wheel asset inspection, and read-only verifier subagents.
