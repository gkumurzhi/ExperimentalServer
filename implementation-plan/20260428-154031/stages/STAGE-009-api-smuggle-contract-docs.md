# STAGE-009 — Correct SMUGGLE API Contract Docs

## Status
OPEN

## Priority
HIGH

## Source findings
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/api-documenter.md` — HIGH: API says SMUGGLE returns HTML, implementation returns JSON and `X-Smuggle-URL`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/performance-engineer.md` — SMUGGLE behavior and memory caveats

## Goal
Public API docs accurately describe SMUGGLE response shape and usage.

## Non-goals
- Do not change SMUGGLE implementation in this stage; STAGE-003 owns behavior.
- Do not normalize all API errors; STAGE-010 owns error contract docs.

## Scope
### Likely files to inspect
- `API.md` — canonical API reference
- `docs/api.md` — generated mirror
- `README.md` — existing SMUGGLE example
- `src/handlers/smuggle.py` — actual response body/headers

### Likely files to change
- `API.md` — replace inaccurate SMUGGLE response docs
- `docs/api.md` — regenerate mirror via `tools/sync_docs.py --write`
- Possibly `README.md` if examples need consistency

### Files that must not be changed
- `uploads/**` — runtime user data; do not inspect contents unless an explicit disposable test fixture is created
- `notes/**` — encrypted runtime note data; do not inspect contents
- `.env*`, `*.key`, `*.pem`, `*.p12`, `*.pfx`, credential JSON — secret-heavy files
- `codex-analysis/**` — source analysis artifacts; read-only evidence only
- `implementation-plan/**` — planning artifacts; close-plan-stage may update status/report files only

## Dependencies
- Depends on: STAGE-003
- Blocks: None

## Implementation steps
1. Document the actual JSON body, `X-Smuggle-URL`, follow-up GET flow, and temporary artifact behavior.
2. Mention any size cap or memory behavior introduced in STAGE-003.
3. Regenerate docs mirrors with the project sync tool.
4. Run docs mirror check.

## Acceptance criteria
- [ ] `API.md` no longer says SMUGGLE directly returns an HTML page when implementation returns JSON.
- [ ] `docs/api.md` is synchronized from `API.md`.
- [ ] SMUGGLE docs include headers, response body, and follow-up GET behavior.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `python3 tools/sync_docs.py --check` | Documentation mirrors are in sync |
| Type/lint/build | `git diff --check API.md docs/api.md README.md` | No whitespace errors |
| Manual/static review | Compare docs against `src/handlers/smuggle.py` | Documented status/body/headers match implementation |

## Suggested subagents
- `api-documenter` — verify API contract.
- `documentation-engineer` — keep mirrors/canonical docs correct.

## Risks and rollback
- Risk: Docs may encode current behavior that later implementation changes invalidate.
- Rollback: Revert docs/mirror changes for this stage.

## Completion notes
Filled by `close-plan-stage`.
