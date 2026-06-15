# STAGE-007 - Python 3.14 readiness

## Status
OPEN

## Priority
MEDIUM

## Source findings
- `codex-analysis/20260614-225437/agent-reports/dependency-manager.md` - P1: Python 3.14 is blocked by metadata and CI policy, not by an evidenced dependency failure.
- `codex-analysis/20260614-225437/agent-reports/devops-engineer.md` - Python policy: CI and metadata cap support at 3.10-3.13.
- `codex-analysis/20260614-225437/project-analysis-report.md` - DevOps & Infrastructure: add 3.14 CI first, then update metadata if clean.

## Goal
Add Python 3.14 readiness as a constrained CI/package-smoke path before widening package metadata or documentation.

## Non-goals
- Do not refresh dependency constraints in the same stage.
- Do not drop Python 3.10 or 3.11 support.
- Do not change Docker base images unless a separate Docker policy stage requires it.

## Scope
### Likely files to inspect
- `pyproject.toml` - `requires-python`, classifiers, pytest/mypy target.
- `.github/workflows/ci.yml` - current Python matrix and smoke jobs.
- `.github/workflows/security.yml` - audit constraints and Python setup.
- `.github/workflows/release.yml` - package smoke and release compatibility.
- `constraints/ci.txt` - constrained dependency authority.
- `README.md` and `CONTRIBUTING.md` - Python support policy text.

### Likely files to change
- `.github/workflows/ci.yml` - add Python 3.14 to constrained CI matrix or as a readiness job.
- `pyproject.toml` - update `requires-python` to `<3.15` and add classifier only after the 3.14 job is clean.
- `README.md`, `CONTRIBUTING.md`, and mirrors under `docs/` - update support table and readiness status.
- `.github/workflows/release.yml` - update package smoke only if release policy requires 3.14 after CI passes.

### Files that must not be changed
- `constraints/ci.txt` - no dependency refresh in this stage unless 3.14 cannot install and the failure is directly caused by an incompatible pinned package.
- `Dockerfile` - Docker base-image policy is STAGE-008.
- `src/**` - runtime code changes are not expected unless tests reveal a Python 3.14 compatibility bug.
- `.env*`, credentials, keys, certificates - secrets are out of scope.

## Dependencies
- Depends on: STAGE-001
- Blocks: `None`

## Implementation steps
1. Add Python 3.14 to CI under the existing constrained dependency path.
2. Run or rely on CI for install, test, `pip check`, import/package smoke, and security audit.
3. If 3.14 passes, update `requires-python`, classifiers, and docs to include Python 3.14 support.
4. If 3.14 fails, keep metadata unchanged and document the blocking failure in the stage report.
5. Do not combine this work with dependency refresh or Python 3.10/3.11 deprecation.

## Acceptance criteria
- [ ] Python 3.14 runs in CI or a readiness job using `constraints/ci.txt`.
- [ ] `pip check`, import smoke, package smoke, and security audit are clean under the 3.14 path before metadata is widened.
- [ ] `pyproject.toml` and docs are updated only after 3.14 readiness is evidenced.
- [ ] No unrelated dependency refresh or interpreter deprecation is included.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Local current-version tests | `python -m pytest` | Exits 0 under the local interpreter or records unrelated failures. |
| Python 3.14 CI | GitHub Actions matrix/readiness job | 3.14 install, tests, `pip check`, import/package smoke, and security audit pass. |
| Metadata review | Inspect `pyproject.toml` and docs | Metadata is widened only after green 3.14 evidence. |
| Docs checks | `python tools/sync_docs.py --check && python tools/check_stale_docs.py` | Exits 0. |

## Suggested subagents
- `explorer` - inspect CI/release/security Python matrix usage.
- `worker` - update matrix/docs/metadata after readiness evidence.
- `dependency-reviewer` - review any 3.14-specific install/test failures if available.

## Risks and rollback
- Risk: Python 3.14 support fails in CI because of tooling or dependency incompatibility.
- Rollback: revert only the 3.14 matrix/metadata/docs changes; keep findings in the stage report for a follow-up readiness attempt.

## Completion notes
Filled by `close-plan-stage`.
