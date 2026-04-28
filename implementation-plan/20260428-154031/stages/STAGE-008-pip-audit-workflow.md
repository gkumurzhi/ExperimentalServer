# STAGE-008 — Repair pip-audit Security Workflow

## Status
CLOSED

## Priority
HIGH

## Source findings
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/devops-engineer.md` — HIGH: `pip-audit --disable-pip` likely wrong for installed-environment audit

## Goal
The security workflow runs `pip-audit` in a documented mode that actually audits dependencies.

## Non-goals
- Do not choose full dependency authority policy here; STAGE-019/STAGE-020 own that.
- Do not suppress real audit findings without explicit risk acceptance.

## Scope
### Likely files to inspect
- `.github/workflows/security.yml` — install and audit commands
- `constraints/ci.txt` — pinned dependencies
- `pyproject.toml` — extras installed by audit job

### Likely files to change
- `.github/workflows/security.yml` — remove or replace `--disable-pip` according to chosen audit mode
- Possibly `constraints/ci.txt` if a requirements-based audit is chosen and needs pinned transitive input

### Files that must not be changed
- `uploads/**` — runtime user data; do not inspect contents unless an explicit disposable test fixture is created
- `notes/**` — encrypted runtime note data; do not inspect contents
- `.env*`, `*.key`, `*.pem`, `*.p12`, `*.pfx`, credential JSON — secret-heavy files
- `codex-analysis/**` — source analysis artifacts; read-only evidence only
- `implementation-plan/**` — planning artifacts; close-plan-stage may update status/report files only

## Dependencies
- Depends on: None
- Blocks: STAGE-019, STAGE-020

## Implementation steps
1. Pick the smallest valid mode: installed-environment audit without `--disable-pip`, or requirements/constraints audit with a compatible locked input.
2. Update the workflow command and comments to match the chosen mode.
3. Run or dry-run the audit command locally if dependencies are available; otherwise document the CI verification path.

## Acceptance criteria
- [ ] Workflow no longer invokes an invalid or mismatched `pip-audit` mode.
- [ ] The audit command has a clear dependency input.
- [ ] Failure mode is a real vulnerability/configuration failure, not pre-audit command misuse.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `python -m pip_audit --help` and the updated audit command if `pip-audit` is installed | Command parses and runs in intended mode |
| Type/lint/build | `python -m compileall src tests` | No Python compile regressions from workflow-only change |
| Manual/static review | Review `security.yml` install/audit sequence | Audit mode matches installed env or requirements input |

## Suggested subagents
- `devops-engineer` — validate workflow semantics.
- `dependency-manager` — ensure dependency input matches policy.

## Risks and rollback
- Risk: A repaired audit may start failing because it now surfaces real vulnerabilities.
- Rollback: Revert the workflow command change for this stage.

## Completion notes
Closed 2026-04-28 23:07:45 MSK by `close-plan-stage`.

- `.github/workflows/security.yml` now installs the constrained `pip-audit` tool and runs `python -m pip_audit --strict -r constraints/ci.txt`.
- The workflow no longer uses `--disable-pip`; `constraints/ci.txt` is the explicit audit input for this stage.
- Local verification confirmed the updated command reaches real audit findings in existing pins instead of failing before audit. Existing vulnerability findings were not suppressed or accepted here.
- Verification also passed `python -m compileall src tests`, workflow YAML parsing, scoped `git diff --check`, and verifier subagent review.
