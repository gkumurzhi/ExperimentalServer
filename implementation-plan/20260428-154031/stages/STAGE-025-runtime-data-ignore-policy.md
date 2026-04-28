# STAGE-025 — Protect Runtime Note Data from Accidental Commit

## Status
OPEN

## Priority
MEDIUM

## Source findings
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/architect-reviewer.md` — MEDIUM: `notes/` runtime data is not ignored
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/docker-expert.md` — `.dockerignore` also missed `notes/`

## Goal
Runtime note data receives the same accidental-commit protection as uploads.

## Non-goals
- Do not read or delete existing `notes/` contents.
- Do not change note storage format.

## Scope
### Likely files to inspect
- `.gitignore` — runtime data patterns
- `src/server.py` — notes directory creation
- `src/notepad_service.py` — note data/metadata writes
- `.dockerignore` — already handled by STAGE-007

### Likely files to change
- `.gitignore` — ignore `notes/` or `notes/*` with optional `.gitkeep` policy
- Optional docs note in STAGE-024 if runtime data policy is documented

### Files that must not be changed
- `uploads/**` — runtime user data; do not inspect contents unless an explicit disposable test fixture is created
- `notes/**` — encrypted runtime note data; do not inspect contents
- `.env*`, `*.key`, `*.pem`, `*.p12`, `*.pfx`, credential JSON — secret-heavy files
- `codex-analysis/**` — source analysis artifacts; read-only evidence only
- `implementation-plan/**` — planning artifacts; close-plan-stage may update status/report files only

## Dependencies
- Depends on: None
- Blocks: None

## Implementation steps
1. Choose whether to ignore `notes/` entirely or keep an empty `.gitkeep` while ignoring contents.
2. Update `.gitignore` accordingly without touching current runtime contents.
3. Validate `git status --short notes/` no longer lists user data once ignore policy applies.

## Acceptance criteria
- [ ] `notes/` runtime contents are ignored by Git by default.
- [ ] No existing note data is read, deleted, or modified.
- [ ] The ignore pattern does not hide source fixtures unintentionally.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `git check-ignore -v notes/example.enc notes/example.meta.json` using dummy paths only | Dummy note-data paths are ignored |
| Type/lint/build | `python -m compileall src tests` | Compilation succeeds |
| Manual/static review | Review `.gitignore` runtime data section | `uploads/` and `notes/` policies are consistent |

## Suggested subagents
- `architect-reviewer` — storage boundary review.
- `security-auditor` — accidental data exposure review.

## Risks and rollback
- Risk: Over-broad ignore could hide intentional note fixtures if they are added later.
- Rollback: Revert `.gitignore` changes for this stage.

## Completion notes
Filled by `close-plan-stage`.
