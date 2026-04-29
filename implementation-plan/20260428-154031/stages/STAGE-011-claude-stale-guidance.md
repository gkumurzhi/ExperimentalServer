# STAGE-011 — Remove Stale CLAUDE Guidance

## Status
CLOSED

## Priority
HIGH

## Source findings
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/documentation-engineer.md` — HIGH: `CLAUDE.md` documents removed OPSEC/sandbox flags and unsafe path checks
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/architect-reviewer.md` — stale AI-facing guidance can reintroduce removed concepts

## Goal
`CLAUDE.md` either accurately reflects current project behavior or redirects to canonical docs without unsafe advice.

## Non-goals
- Do not rewrite canonical user docs beyond what this file needs.
- Do not change CLI behavior.

## Scope
### Likely files to inspect
- `CLAUDE.md` — stale guidance
- `src/cli.py` — current flags
- `tests/test_cli.py` — removed flag expectations
- `docs/ADR/ADR-004-uploads-relative-to.md` — safe path guidance

### Likely files to change
- `CLAUDE.md` — remove `--opsec`, `--sandbox`, OPSEC mixin references, and `startswith()` path advice

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
1. Replace removed OPSEC/sandbox instructions with current `--advanced-upload` references or a compact pointer to canonical docs.
2. Remove `startswith()` path containment advice and point to `Path.resolve().relative_to()`/ADR-004 style containment.
3. Add or extend stale-doc grep coverage if appropriate in STAGE-020 or this stage.

## Acceptance criteria
- [ ] `CLAUDE.md` contains no removed `--opsec`, `--sandbox`, `OpsecHandlersMixin`, or unsafe string-prefix path guidance.
- [ ] The file directs contributors to current README/API/CONTRIBUTING/ADR docs.
- [ ] CLI tests still confirm removed flags are rejected.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `pytest tests/test_cli.py -q` | CLI flag behavior tests pass |
| Type/lint/build | `git diff --check CLAUDE.md` | No whitespace errors |
| Manual/static review | `rg "--opsec|--sandbox|Opsec|startswith" CLAUDE.md` | No stale unsafe guidance remains except intentional historical references |

## Suggested subagents
- `documentation-engineer` — keep AI guide aligned.
- `security-auditor` — review path guidance wording.

## Risks and rollback
- Risk: If external automation depends on `CLAUDE.md`, wording changes may affect it.
- Rollback: Revert `CLAUDE.md` changes for this stage.

## Completion notes
Closed 2026-04-29 16:59:26 MSK. `CLAUDE.md` no longer documents removed `--opsec`, `--sandbox`, `OpsecHandlersMixin`, OPSEC upload/header flow, or unsafe string-prefix path containment. It now points contributors to `README.md`, `API.md`, `CONTRIBUTING.md`, and ADR-004, describes current `--advanced-upload` unknown-method handling, and directs path checks to `Path.resolve().relative_to()` via `resolve_descendant_path()` / `BaseHandler._resolve_safe_path()`. Verification passed: project-venv CLI tests (`31 passed`), scoped `git diff --check`, stale-guidance grep, canonical-doc anchor grep, and documentation/security verifier subagents.
