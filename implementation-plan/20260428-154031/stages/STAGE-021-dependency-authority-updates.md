# STAGE-021 — Set Dependency Authority and Update Coverage

## Status
CLOSED

## Priority
MEDIUM

## Source findings
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/dependency-manager.md` — MEDIUM: constraints vs untracked `uv.lock`, missing Dependabot surfaces, Python 3.14 policy gap
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/devops-engineer.md` — dependency source-of-truth split and unpinned browser smoke

## Goal
The project has one documented dependency authority and automation coverage for active dependency surfaces.

## Non-goals
- Do not upgrade every dependency opportunistically.
- Do not fix Playwright smoke test logic; STAGE-022 owns UI smoke behavior.

## Scope
### Likely files to inspect
- `constraints/ci.txt`, `uv.lock`, `pyproject.toml` — dependency authority signals
- `.github/dependabot.yml` — update surfaces
- `.github/workflows/ci.yml` and `security.yml` — install/cache inputs
- `Dockerfile` — constraints use
- `tools/browser_smoke.py`/CI npx commands — Playwright resolution

### Likely files to change
- `README.md`/`CONTRIBUTING.md` or dedicated docs — document constraints vs uv policy
- `.gitignore` or tracked `uv.lock` decision artifacts — align with chosen policy
- `.github/dependabot.yml` — add pre-commit/docker/uv if applicable
- `.github/workflows/ci.yml` — Python 3.14 matrix or documented exclusion; pin Playwright package version

### Files that must not be changed
- `uploads/**` — runtime user data; do not inspect contents unless an explicit disposable test fixture is created
- `notes/**` — encrypted runtime note data; do not inspect contents
- `.env*`, `*.key`, `*.pem`, `*.p12`, `*.pfx`, credential JSON — secret-heavy files
- `codex-analysis/**` — source analysis artifacts; read-only evidence only
- `implementation-plan/**` — planning artifacts; close-plan-stage may update status/report files only

## Dependencies
- Depends on: STAGE-020
- Blocks: None

## Implementation steps
1. Choose constraints-first as the default unless the team explicitly wants uv adoption; document the decision.
2. If constraints-first, keep `uv.lock` ignored/local or remove it from release workflow; if uv-first, commit it and switch CI to locked uv sync.
3. Add Dependabot entries for pre-commit and Docker; add uv only if `uv.lock` is committed authority.
4. Add Python 3.14 CI coverage as allowed-failure or official support, or narrow classifiers/metadata.
5. Pin browser smoke Playwright resolution through a lockfile or explicit `npx playwright@<version>`.

## Acceptance criteria
- [x] There is one clear dependency authority for CI/Docker/local guidance.
- [x] Dependabot covers the active dependency surfaces selected by the policy.
- [x] Python support metadata and CI matrix no longer disagree silently.
- [x] Browser smoke package resolution is pinned or documented as non-release-gating.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `python -m pip install -c constraints/ci.txt -e .[crypto,lint,test]` or selected locked workflow command in a disposable env | Install uses chosen authority |
| Type/lint/build | `python -m compileall src tests` | Compilation succeeds |
| Manual/static review | Compare docs, CI, Docker, Dependabot, and lockfiles | All point to the same authority |

## Suggested subagents
- `dependency-manager` — authority decision.
- `devops-engineer` — workflow/update automation.

## Risks and rollback
- Risk: Changing dependency authority can disrupt developer workflows.
- Rollback: Revert dependency policy/workflow/dependabot changes for this stage.

## Completion notes
Closed 2026-04-30 17:02:04 MSK. The project now uses `constraints/ci.txt` as the only committed dependency authority for CI, Docker, security, docs, and reproducible local installs; tracked `uv.lock` was removed and future local locks are ignored. Dependabot covers pip, GitHub Actions, Docker, and pre-commit, with Docker base-image pins visible in direct `FROM` lines. Python support metadata is capped to the tested 3.10-3.13 range, and release-gating browser smoke uses the same pinned `@playwright/cli@0.1.9` package in CI and the smoke helper. Constrained install, compile, lint/format, mypy in a constrained disposable venv, docs sync, YAML/TOML checks, Docker build/run, Playwright dry run, diff hygiene, and verifier subagents passed.
