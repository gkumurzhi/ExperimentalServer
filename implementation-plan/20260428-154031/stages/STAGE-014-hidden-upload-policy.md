# STAGE-014 — Enforce Hidden Upload Policy Consistently

## Status
OPEN

## Priority
MEDIUM

## Source findings
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/security-auditor.md` — MEDIUM: hidden uploads blocked for GET/INFO but exposed through FETCH/SMUGGLE/DELETE

## Goal
Hidden-file access policy under `uploads/` is documented in code and enforced uniformly across all file methods.

## Non-goals
- Do not read real hidden files under `uploads/`.
- Do not alter static package resources.

## Scope
### Likely files to inspect
- `src/handlers/files.py` — GET/FETCH/DELETE and hidden checks
- `src/handlers/info.py` — INFO hidden behavior
- `src/handlers/smuggle.py` — SMUGGLE file reads
- `tests/test_server_methods.py` and traversal/security tests — method coverage

### Likely files to change
- `src/handlers/files.py` — apply hidden policy to FETCH/DELETE as chosen
- `src/handlers/smuggle.py` — apply hidden policy before source read
- `tests/` — method matrix for `.hidden` paths

### Files that must not be changed
- `uploads/**` — runtime user data; do not inspect contents unless an explicit disposable test fixture is created
- `notes/**` — encrypted runtime note data; do not inspect contents
- `.env*`, `*.key`, `*.pem`, `*.p12`, `*.pfx`, credential JSON — secret-heavy files
- `codex-analysis/**` — source analysis artifacts; read-only evidence only
- `implementation-plan/**` — planning artifacts; close-plan-stage may update status/report files only

## Dependencies
- Depends on: STAGE-001
- Blocks: None

## Implementation steps
1. Choose the policy: hidden upload files are inaccessible by all external file methods unless explicitly documented otherwise.
2. Apply the hidden check to FETCH, SMUGGLE, and DELETE consistently.
3. Add tests covering GET, INFO, FETCH, SMUGGLE, and DELETE for hidden paths.
4. Ensure visible files remain unaffected.

## Acceptance criteria
- [ ] Hidden upload files are not readable through FETCH or SMUGGLE if GET/INFO deny them.
- [ ] DELETE behavior follows the documented policy.
- [ ] Tests cover the method matrix for hidden and visible files.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `pytest tests/test_server_methods.py tests/test_handlers -q -k "hidden or smuggle or fetch or delete"` | Hidden policy tests pass |
| Type/lint/build | `python -m compileall src tests` | Compilation succeeds |
| Manual/static review | Inspect all file method handlers | Hidden policy is not method-dependent without documentation |

## Suggested subagents
- `security-auditor` — policy consistency review.
- `qa-expert` — method matrix tests.

## Risks and rollback
- Risk: Existing users may rely on FETCH/SMUGGLE for hidden files.
- Rollback: Revert hidden-policy handler/test changes for this stage.

## Completion notes
Filled by `close-plan-stage`.
