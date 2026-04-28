# STAGE-010 — Correct API Error Contract Docs

## Status
OPEN

## Priority
HIGH

## Source findings
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/api-documenter.md` — HIGH: global JSON error model is false for several endpoints

## Goal
API documentation no longer promises a uniform JSON error body unless implementation actually provides it.

## Non-goals
- Do not normalize handler error implementations in this stage unless explicitly chosen as the minimal fix.
- Do not alter request IDs; STAGE-018/STAGE-023 may document metrics/request-id behavior.

## Scope
### Likely files to inspect
- `API.md` — global error statement and endpoint errors
- `docs/api.md` — generated mirror
- `src/handlers/files.py`, `src/handlers/info.py`, `src/handlers/advanced_upload.py` — actual error bodies
- `src/request_pipeline.py` — direct auth/size/upgrade errors

### Likely files to change
- `API.md` — document endpoint-specific error shapes or revise global claim
- `docs/api.md` — regenerate mirror
- Optional tests only if implementation normalization is chosen instead of docs-first

### Files that must not be changed
- `uploads/**` — runtime user data; do not inspect contents unless an explicit disposable test fixture is created
- `notes/**` — encrypted runtime note data; do not inspect contents
- `.env*`, `*.key`, `*.pem`, `*.p12`, `*.pfx`, credential JSON — secret-heavy files
- `codex-analysis/**` — source analysis artifacts; read-only evidence only
- `implementation-plan/**` — planning artifacts; close-plan-stage may update status/report files only

## Dependencies
- Depends on: None
- Blocks: STAGE-023

## Implementation steps
1. Inventory current error bodies for GET/FETCH/INFO/advanced upload/NOTE/WebSocket upgrade from the source evidence.
2. Replace the global JSON error guarantee with endpoint-specific error contract text, or explicitly scope it to endpoints that implement it.
3. Regenerate docs mirrors and run sync check.
4. Add a backlog note for implementation normalization if docs preserve mixed behavior.

## Acceptance criteria
- [ ] API docs do not claim all errors are `{"error","status"}` JSON unless that is implemented.
- [ ] Known text/plain and empty-body errors are documented or explicitly marked legacy.
- [ ] Generated docs mirror is in sync.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `python3 tools/sync_docs.py --check` | Documentation mirrors are in sync |
| Type/lint/build | `git diff --check API.md docs/api.md` | No whitespace errors |
| Manual/static review | Compare documented error shapes to handler code | No known mismatch remains for cited endpoints |

## Suggested subagents
- `api-documenter` — endpoint contract review.
- `qa-expert` — identify test implications if implementation is normalized later.

## Risks and rollback
- Risk: Documenting mixed errors may make a poor API contract more explicit.
- Rollback: Revert docs/mirror changes for this stage.

## Completion notes
Filled by `close-plan-stage`.
