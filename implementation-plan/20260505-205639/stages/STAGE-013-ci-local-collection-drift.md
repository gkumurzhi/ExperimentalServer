# STAGE-013 - Resolve local-only pytest collection drift

## Status
OPEN

## Priority
MEDIUM

## Source findings
- `codex-analysis/20260505-193249/project-analysis-report.md` - DevOps: ignored local files `tools/close_plan_stages.py` and `tests/test_close_plan_stages.py` are collected locally but absent in CI checkout.
- `codex-analysis/20260505-193249/agent-reports/qa-expert.md` - MEDIUM: collect-only included ignored `tests/test_close_plan_stages.py`.
- `codex-analysis/20260505-193249/agent-reports/devops-engineer.md` - LOW: ignored local test/tool artifacts can skew local confidence.

## Goal
Make local pytest collection match tracked CI checkout behavior by either tracking supported tool/tests, moving local-only artifacts outside pytest collection, or explicitly ignoring them.

## Non-goals
- Do not implement or modify the close-plan-stage runner itself unless the project decides it is supported code.
- Do not delete user/local tooling without explicit owner intent.
- Do not change unrelated pytest coverage thresholds.

## Scope
### Likely files to inspect
- `.gitignore` - local Codex stage runner ignore rules.
- `pyproject.toml` - pytest `testpaths` and `python_files` patterns.
- `tools/close_plan_stages.py` - local ignored tool, if present and safe to inspect as non-secret source.
- `tests/test_close_plan_stages.py` - local ignored test collected by pytest.
- `.github/workflows/ci.yml` - CI pytest invocation.

### Likely files to change
- `.gitignore` - adjust ignore rules if files become tracked or moved.
- `pyproject.toml` - add explicit `norecursedirs`/ignore behavior only if appropriate.
- `.github/workflows/ci.yml` - optional guard that fails when ignored `tests/test_*.py` files exist.
- `tools/` and `tests/` - track, move, or document close-plan runner files only after ownership decision.

### Files that must not be changed
- Source runtime `src/**` - no product behavior change.
- Any `.codex/`, `.agents/`, or local secret/session state - do not inspect or alter agent home data beyond repo files.
- `.env*`, credentials, keys, certificates - never read or edit secrets.

## Dependencies
- Depends on: STAGE-001
- Blocks: `None`

## Implementation steps
1. Confirm whether ignored `tools/close_plan_stages.py` and `tests/test_close_plan_stages.py` still exist locally and are collected.
2. Decide with repository evidence whether these are project-supported files or local agent tooling.
3. If project-supported, track them and include them in CI.
4. If local-only, move them out of `tests/test_*.py` collection or add explicit pytest/CI guard to prevent ignored collected tests.
5. Add a lightweight guard that detects ignored `tests/test_*.py` files under the repo.

## Acceptance criteria
- [ ] `pytest --collect-only` no longer collects tests that are ignored and absent from CI checkout.
- [ ] The repo has an explicit policy for local Codex runner files.
- [ ] CI/local confidence drift from ignored test collection is prevented.
- [ ] No local-only files are deleted or moved without a clear decision.
- [ ] Full project test collection still includes all intended tracked tests.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Collect-only | `pytest --collect-only -q -p no:cacheprovider` | No ignored local-only test modules are collected |
| Git ignored check | `git ls-files --others --ignored --exclude-standard tests 'tools/*.py'` | No ignored `tests/test_*.py` that pytest would collect, unless explicitly allowed |
| CI guard | Run any new helper or workflow command locally | Fails on a synthetic ignored collected test or passes current repo |
| Test suite sanity | `pytest -q tests/test_cli.py` or a small subset | Existing collection remains healthy |

## Suggested subagents
- `explorer` - inspect the ignored files and determine whether they look project-supported or agent-local.
- `worker` - implement tracking/move/ignore guard after the decision.
- `qa-expert` - review collection behavior and CI parity.

## Risks and rollback
- Risk: Tracking local agent tooling can pull non-product workflow into the project.
- Rollback: Move files outside repo-level pytest collection and keep `.gitignore` policy explicit.

## Completion notes
Filled by `close-plan-stage`.
