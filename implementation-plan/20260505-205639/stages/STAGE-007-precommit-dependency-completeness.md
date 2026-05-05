# STAGE-007 - Align pre-commit and dependency completeness checks

## Status
CLOSED

## Priority
MEDIUM

## Source findings
- `codex-analysis/20260505-193249/project-analysis-report.md` - DevOps: pre-commit mypy env lacks `acme`/`josepy` and pins old `cryptography`.
- `codex-analysis/20260505-193249/agent-reports/dependency-manager.md` - MEDIUM: isolated pre-commit mypy dependency graph diverges from runtime.
- `codex-analysis/20260505-193249/agent-reports/python-pro.md` - MEDIUM: current import boundary reaches ACME deps; active local interpreter lacks them.
- `codex-analysis/20260505-193249/agent-reports/devops-engineer.md` - MEDIUM: `pip-audit` audits constraints but not installed-environment completeness.

## Goal
Make developer and CI dependency checks prove the installed runtime graph is present, pinned/audited, and compatible with the import/type-check boundary.

## Non-goals
- Do not refresh or upgrade dependency versions beyond aligning to current constraints unless necessary.
- Do not redesign package import boundaries; that is backlog.
- Do not remove the compatibility `[crypto]` extra.

## Scope
### Likely files to inspect
- `.pre-commit-config.yaml` - mypy isolated hook dependencies.
- `constraints/ci.txt` - pinned runtime/import graph.
- `pyproject.toml` - declared direct dependencies and optional deps.
- `.github/workflows/ci.yml` - install and smoke commands.
- `.github/workflows/security.yml` - pip-audit workflow.
- `.github/dependabot.yml` - dependency update coverage.

### Likely files to change
- `.pre-commit-config.yaml` - align mypy `additional_dependencies` with `constraints/ci.txt` for imported ACME/crypto stack.
- `.github/workflows/ci.yml` - add clean installed-env smoke such as `python -m pip check` and import checks if not already present.
- `.github/workflows/security.yml` - add installed-env completeness/audit check or constraints-vs-installed check.
- `tools/` - optional helper for dependency completeness if workflow shell becomes brittle.
- `docs/contributing.md` or `CONTRIBUTING.md` - optional updated local dependency refresh guidance.

### Files that must not be changed
- `src/**` - runtime code is not the purpose of this stage.
- `constraints/ci.txt` - do not repin unless a required current pin is missing or inconsistent.
- `.env*`, credentials, keys, certificates - never read or edit secrets.

## Dependencies
- Depends on: STAGE-006
- Blocks: `None`

## Implementation steps
1. Compare `.pre-commit-config.yaml` mypy deps to `constraints/ci.txt` pins for `acme`, `cryptography`, `josepy`, and any required TLS transitive imports such as `PyOpenSSL`.
2. Update the mypy hook dependencies to match current pinned versions.
3. Add a CI install smoke that runs `python -m pip check`, `python -m src --help`, and a minimal `import acme, cryptography, josepy` check after constrained install.
4. Add an installed-environment completeness check or document why `pip-audit -r constraints/ci.txt` remains the only audit gate.
5. Update contributor docs if local setup commands should change after STAGE-006.

## Acceptance criteria
- [x] Pre-commit mypy installs the packages imported by `src/security/tls.py`.
- [x] The pinned `cryptography` version used by the mypy hook matches the declared lower-bound policy and current constraint.
- [x] CI catches missing runtime dependencies after package install.
- [x] Security/audit workflow either audits installed completeness or documents a clear constraints completeness check.
- [x] Local setup guidance does not ask developers to rely on stale optional extras for required runtime dependencies.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Pre-commit mypy | `pre-commit run mypy --all-files` | Passes in a refreshed hook environment |
| Installed env smoke | `python -m pip check && python -m src --help > /dev/null && python -c "import acme, cryptography, josepy"` | Exits 0 in constrained env |
| Security workflow review | Inspect `.github/workflows/security.yml` and helper output | Completeness/audit behavior is explicit |
| Constraint consistency | `python -m pip install -e ".[dev,lint,test]"` under `PIP_CONSTRAINT=constraints/ci.txt` if feasible | Install succeeds |

## Suggested subagents
- `explorer` - identify exact imported third-party modules and matching constraint pins.
- `worker` - update pre-commit/workflows and optional helper.
- `dependency-manager` - review dependency-policy consistency.

## Risks and rollback
- Risk: Duplicated pins in pre-commit can drift again.
- Rollback: Revert hook dependency changes and document using a local/system mypy hook as a future alternative.

## Completion notes
Closed 2026-05-05 23:29:51 MSK. Aligned the pre-commit mypy hook with the
constrained ACME/crypto import graph, added CI installed dependency smoke
checks, added a security workflow constraints-vs-installed completeness check
before strict pinned `pip-audit`, and documented the local checks in
`CONTRIBUTING.md` plus the generated docs mirror.
