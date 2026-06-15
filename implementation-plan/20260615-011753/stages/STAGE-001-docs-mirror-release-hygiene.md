# STAGE-001 - Docs mirror and release hygiene

## Status
CLOSED

## Priority
MEDIUM

## Source findings
- `codex-analysis/20260614-225437/project-analysis-report.md` - Key Medium Issues: docs mirrors are out of sync for `API.md` and `CONTRIBUTING.md`.
- `codex-analysis/20260614-225437/agent-reports/documentation-engineer.md` - P0/P1/P2: generated mirror drift blocks docs CI; changelog and install/publish docs need a dated release boundary.
- `codex-analysis/20260614-225437/agent-reports/qa-expert.md` - P1/P3: CI catches docs drift, but local guardrails do not catch it early.

## Goal
Make root-canonical docs and `docs/` mirrors consistent, then add a local guardrail so the same drift is caught before CI.

## Non-goals
- Do not change runtime behavior or profile defaults.
- Do not implement API v1, Docker publishing, or durable Notepad.
- Do not rewrite documentation outside the release/docs-sync scope.

## Scope
### Likely files to inspect
- `tools/sync_docs.py` - mirror mapping and expected generated files.
- `tools/check_stale_docs.py` - stale-doc guard behavior.
- `.github/workflows/ci.yml` - current docs CI gate.
- `.pre-commit-config.yaml` - local hooks that currently omit docs sync checks.
- `API.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `README.md`, `docs/index.md` - drifted or release-boundary docs.

### Likely files to change
- `docs/api.md` - regenerate from `API.md`.
- `docs/contributing.md` - regenerate from `CONTRIBUTING.md`.
- `.pre-commit-config.yaml` - add docs sync/stale-doc local hooks or equivalent local enforcement.
- `CHANGELOG.md` and `docs/changelog.md` - add a dated boundary for the closed remediation work.
- `README.md` and `docs/index.md` - clarify artifact-only release status if install/publish wording conflicts.

### Files that must not be changed
- `src/**` - this stage is docs/process only.
- `tests/**` - do not add behavior tests in the docs hygiene stage.
- `.env*`, credentials, keys, certificates - secrets are out of scope.
- `site/**` - generated MkDocs output should not be edited manually.

## Dependencies
- Depends on: `None`
- Blocks: STAGE-002

## Implementation steps
1. Run `python tools/sync_docs.py --write` to regenerate docs mirrors.
2. Review the mirror diff and keep it limited to expected generated docs.
3. Add a local pre-commit or equivalent PR guard for `python tools/sync_docs.py --check` and `python tools/check_stale_docs.py`.
4. Convert the completed remediation content in `CHANGELOG.md` into a dated release/migration boundary and mirror it if required.
5. Clarify install/publish wording so docs do not imply durable PyPI/GHCR artifacts unless the release lane actually publishes them.
6. Run docs checks and update `stage-status.md` plus a stage report when complete.

## Acceptance criteria
- [ ] `python tools/sync_docs.py --check` passes.
- [ ] `python tools/check_stale_docs.py` passes.
- [ ] Docs sync/stale-doc checks are available as a local guardrail or explicitly required by PR process.
- [ ] `CHANGELOG.md` has a dated boundary for the closed remediation work.
- [ ] Install/publish docs no longer conflict with the artifact-only release lane.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Docs mirror check | `python tools/sync_docs.py --check` | Exits 0 with no mirror drift. |
| Stale-doc check | `python tools/check_stale_docs.py` | Exits 0. |
| Optional docs build | `mkdocs build --strict` | Exits 0 if MkDocs dependencies are installed. |
| Manual/static review | Review docs diffs and pre-commit/PR guard changes | Only docs/process files changed; no runtime behavior changed. |

## Suggested subagents
- `explorer` - inspect current docs drift and release wording before edits.
- `worker` - apply mirror regeneration and local guardrail changes.
- `docs-reviewer` - review changelog/release wording if available.

## Risks and rollback
- Risk: regenerated mirrors include unrelated doc changes from prior uncommitted work.
- Rollback: revert only the docs/pre-commit changes from this stage and rerun `python tools/sync_docs.py --check` to confirm the previous state.

## Completion notes
- Closed 2026-06-15 12:50:25 +0300.
- Regenerated root-canonical docs mirrors with `python tools/sync_docs.py --write`.
- Added local pre-commit guardrails for `python tools/sync_docs.py --check` and `python tools/check_stale_docs.py`.
- Added a dated 2026-06-15 changelog boundary for docs/release remediation.
- Clarified docs-site install wording so releases are described as verified GitHub Actions artifacts, not PyPI/GHCR/registry publication.
- Required checks passed: `python tools/sync_docs.py --check`; `python tools/check_stale_docs.py`.
- Local `pre-commit` and `mkdocs` executables were unavailable, so hook execution and optional strict docs build were recorded as skipped environment checks.
