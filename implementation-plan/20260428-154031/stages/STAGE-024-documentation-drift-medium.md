# STAGE-024 — Clean Remaining Documentation Drift

## Status
OPEN

## Priority
MEDIUM

## Source findings
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/documentation-engineer.md` — MEDIUM docs drift: changelog default, threat model, HMAC coverage, generated filename workflow
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/api-documenter.md` — MEDIUM docs drift: INFO, CORS, advanced upload, WebSocket docs

## Goal
Canonical docs and generated mirrors match current implementation for medium-priority documented behavior.

## Non-goals
- Do not fix high docs already covered by STAGE-009/STAGE-011.
- Do not change implementation behavior unless a docs-only fix would be misleading.

## Scope
### Likely files to inspect
- `README.md`, `API.md`, `SECURITY.md`, `CHANGELOG.md`, `CONTRIBUTING.md` — canonical docs
- `docs/**/*.md` — generated/manual docs
- `tools/sync_docs.py` — mirror behavior
- `src/cli.py`, `src/http/io.py`, `src/handlers/info.py`, `src/handlers/notepad.py`, `src/handlers/advanced_upload.py` — implementation evidence

### Likely files to change
- Canonical root docs — update advanced-upload default, Transfer-Encoding status, HMAC coverage, generated filename workflow, INFO/CORS/WS details
- `docs/**/*.md` generated mirrors — regenerate where required
- `CONTRIBUTING.md` — fix `--check` wording
- Possibly CI stale-doc grep patterns

### Files that must not be changed
- `uploads/**` — runtime user data; do not inspect contents unless an explicit disposable test fixture is created
- `notes/**` — encrypted runtime note data; do not inspect contents
- `.env*`, `*.key`, `*.pem`, `*.p12`, `*.pfx`, credential JSON — secret-heavy files
- `codex-analysis/**` — source analysis artifacts; read-only evidence only
- `implementation-plan/**` — planning artifacts; close-plan-stage may update status/report files only

## Dependencies
- Depends on: STAGE-009, STAGE-010, STAGE-011, STAGE-013, STAGE-015, STAGE-016
- Blocks: None

## Implementation steps
1. Update `CHANGELOG.md` advanced-upload default to opt-in.
2. Update threat model to reflect current Transfer-Encoding rejection.
3. Narrow ADR/security HMAC language to payload bytes unless implementation was expanded.
4. Document generated filename collision suffix behavior and missing filename/path response caveat.
5. Update INFO, CORS/OPTIONS, WebSocket `clear`/failure semantics, and CONTRIBUTING mirror instructions.
6. Regenerate/check docs mirrors.

## Acceptance criteria
- [ ] No known medium-priority docs drift from the analysis remains unaddressed or intentionally deferred.
- [ ] `tools/sync_docs.py --check` passes.
- [ ] Docs do not overstate security properties or runtime defaults.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `python3 tools/sync_docs.py --check` | Documentation mirrors are in sync |
| Type/lint/build | `git diff --check README.md API.md SECURITY.md CHANGELOG.md CONTRIBUTING.md docs tools/sync_docs.py` | No whitespace errors |
| Manual/static review | Map docs claims to source evidence listed in stage | Claims match implementation |

## Suggested subagents
- `documentation-engineer` — root/mirror docs.
- `api-documenter` — API details.
- `security-auditor` — security-claim wording.

## Risks and rollback
- Risk: Docs-only updates may document undesirable behavior rather than improving it.
- Rollback: Revert documentation/mirror changes for this stage.

## Completion notes
Filled by `close-plan-stage`.
