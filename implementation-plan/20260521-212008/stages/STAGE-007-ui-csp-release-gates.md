# STAGE-007 - Harden UI validation and CSP release gates

## Status
OPEN

## Priority
MEDIUM

## Source findings
- `project-analysis-report.md` - F-007: audit called out incomplete browser smoke/pageerror capture, missing fast JS/package-data gates, and CSP that still permits inline script/style.

## Goal
Make UI asset breakage and CSP regressions fail fast before release, then tighten CSP only where tests prove the UI still works.

## Non-goals
- Do not redesign the UI.
- Do not remove every inline style/script in one stage if that would become a broad frontend refactor.

## Scope
### Likely files to inspect
- `src/data/static/ui/*.js`, `src/data/index.html` - packaged UI assets.
- `src/handlers/files.py` - CSP headers.
- `tools/browser_smoke.playwright.js` - pageerror/console coverage.
- `.github/workflows/ci.yml` and pre-commit config if present.

### Likely files to change
- Browser smoke script - capture console/page errors consistently.
- CI/pre-commit release gates - JS syntax and package-data smoke.
- CSP tests and possibly CSP header defaults.

### Files that must not be changed
- Notepad protocol/server behavior - covered by prior stages.

## Dependencies
- Depends on: STAGE-005
- Blocks: STAGE-008

## Implementation steps
1. Add fast `node --check` coverage for static UI JavaScript.
2. Add package-data smoke that verifies packaged UI assets are readable and valid.
3. Make browser smoke fail on page errors and relevant console errors.
4. Add tests documenting current CSP.
5. Tighten CSP only for proven-safe areas; otherwise create explicit follow-up backlog.

## Acceptance criteria
- [ ] Broken bundled JavaScript fails a fast local/CI check.
- [ ] Package-data UI assets are validated outside source-tree-only assumptions.
- [ ] Browser smoke captures page errors and unexpected console errors.
- [ ] CSP behavior is tested and documented; any remaining inline allowance has an explicit reason.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| JS syntax | `node --check src/data/static/ui/*.js` or equivalent loop | Pass. |
| Browser smoke | `node tools/browser_smoke.playwright.js` | Pass with no unexpected page/console errors. |
| Handler tests | `pytest -q tests/test_handlers/test_handler_integration.py -k 'csp or static'` | Pass. |
| CI review | Inspect workflow/pre-commit | UI gates are wired. |

## Suggested subagents
- `frontend-developer` - review smoke coverage and UI constraints.
- `security-auditor` - review CSP tradeoffs.

## Risks and rollback
- Risk: Strict console failure rules can make smoke tests flaky.
- Rollback: Start with an allowlist for known benign console output and shrink it over time.

## Completion notes
Filled by `close-plan-stage`.
