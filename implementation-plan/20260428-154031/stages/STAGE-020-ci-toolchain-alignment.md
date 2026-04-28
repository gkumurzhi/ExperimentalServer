# STAGE-020 — Align CI and Local Toolchain Pins

## Status
OPEN

## Priority
MEDIUM

## Source findings
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/dependency-manager.md` — MEDIUM: pre-commit hooks lag CI pins and `pre-commit` is unpinned in constraints
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/devops-engineer.md` — MEDIUM: local pre-commit hooks drift from CI

## Goal
Local pre-commit and CI lint/type tooling use compatible pinned versions, and CI install extras do not accidentally pull unpinned pre-commit tooling.

## Non-goals
- Do not decide whether uv replaces constraints; STAGE-021 owns dependency authority.
- Do not fix unrelated lint errors unless they are caused by version alignment and required for verification.

## Scope
### Likely files to inspect
- `.pre-commit-config.yaml` — hook revisions
- `constraints/ci.txt` — pinned tool versions
- `pyproject.toml` — extras grouping
- `.github/workflows/ci.yml` — installed extras and commands

### Likely files to change
- `.pre-commit-config.yaml` — update Ruff/mypy hook revisions or document convenience-only policy
- `constraints/ci.txt` — pin `pre-commit` and required transitives if CI installs dev extra
- `pyproject.toml` — optionally split `precommit`/`dev` extras
- `.github/workflows/ci.yml` — install only needed extras if extras are split

### Files that must not be changed
- `uploads/**` — runtime user data; do not inspect contents unless an explicit disposable test fixture is created
- `notes/**` — encrypted runtime note data; do not inspect contents
- `.env*`, `*.key`, `*.pem`, `*.p12`, `*.pfx`, credential JSON — secret-heavy files
- `codex-analysis/**` — source analysis artifacts; read-only evidence only
- `implementation-plan/**` — planning artifacts; close-plan-stage may update status/report files only

## Dependencies
- Depends on: STAGE-008
- Blocks: STAGE-021

## Implementation steps
1. Choose constraints-first local/CI alignment for this stage.
2. Update pre-commit Ruff/mypy revisions to match the constrained generation or explicitly mark pre-commit convenience-only.
3. Pin `pre-commit` if it remains installed by CI through a dev extra, or split extras so CI does not install it.
4. Run pre-commit or equivalent CI commands if tools are available.

## Acceptance criteria
- [ ] Ruff/mypy versions used locally do not materially lag CI constraints.
- [ ] `pre-commit` dependency status is explicit and pinned or excluded from CI install.
- [ ] CI docs/commands reflect the intended local verification path.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `pre-commit run --all-files` if installed, otherwise `ruff check . && mypy src tests` using constrained env | Local gate matches CI intent |
| Type/lint/build | `python -m compileall src tests` | Compilation succeeds |
| Manual/static review | Compare `.pre-commit-config.yaml` to `constraints/ci.txt` | No unexplained major version drift remains |

## Suggested subagents
- `dependency-manager` — version policy.
- `devops-engineer` — CI workflow alignment.

## Risks and rollback
- Risk: Newer hooks may surface existing lint/type issues.
- Rollback: Revert tool pin/extras/workflow changes for this stage.

## Completion notes
Filled by `close-plan-stage`.
