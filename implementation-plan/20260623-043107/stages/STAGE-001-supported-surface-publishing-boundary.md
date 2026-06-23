# STAGE-001 - Supported surface and publishing boundary

## Status
CLOSED

## Priority
MEDIUM

## Source findings
- `implementation-plan/20260615-011753/findings.md` - F-009: release artifacts, Docker examples, and rollback language need one explicit support boundary.
- `implementation-plan/20260615-011753/findings.md` - F-014: publishing and public support need maintainer commitment before implementation.
- `implementation-plan/20260615-011753/backlog.md` - PyPI/GHCR publishing lane is explicitly deferred pending support and ownership choices.

## Goal
Record one authoritative supported-surface decision covering local workspace use, Docker example status, release artifact retention, and whether public registry publishing is supported, deferred, or out of scope.

## Non-goals
- Implementing PyPI or GHCR publishing.
- Changing runtime defaults or handler behavior.
- Adding new CI release automation beyond documentation/guardrail adjustments.

## Scope
### Likely files to inspect
- `README.md` - current support and publishing language.
- `SECURITY.md` - operator/support boundary wording.
- `CONTRIBUTING.md` - contributor expectations around release artifacts.
- `.github/workflows/release.yml` - current artifact-only release lane and retention assumptions.
- `docs/ADR/` - place to record the support-surface decision.

### Likely files to change
- `docs/ADR/` - new or updated decision record for supported surfaces and publishing stance.
- `README.md` - align public-facing support and artifact language.
- `SECURITY.md` - align operational boundary wording.
- `CONTRIBUTING.md` - clarify maintainer/release expectations if needed.

### Files that must not be changed
- `src/**` - this stage should not change runtime code.
- `tests/**` - no implementation-level test rewrites are needed for a support-boundary ADR.

## Dependencies
- Depends on: `None`
- Blocks: STAGE-002, STAGE-003, STAGE-004

## Implementation steps
1. Audit the current support-surface and publishing wording across README, SECURITY, CONTRIBUTING, release workflow comments, and existing ADRs.
2. Write or update an ADR that states the maintained artifact surfaces, rollback ownership, and whether registry publishing is supported, deferred, or out of scope.
3. Align top-level docs with that decision and add or refine wording guards if the current stale-doc checks do not cover the new boundary.

## Acceptance criteria
- [ ] The repository has one explicit ADR or equivalent decision record for supported surfaces and publishing status.
- [ ] README/SECURITY/related release docs no longer imply unsupported public artifact commitments.
- [ ] `python tools/check_stale_docs.py` passes after the wording changes.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `python tools/check_stale_docs.py` | Safety/support wording checks pass. |
| Type/lint/build | `python tools/sync_docs.py --check` | Mirrored docs remain in sync if touched. |
| Manual/static review | Review the ADR, README, SECURITY, CONTRIBUTING, and release workflow comments together | Supported surfaces and publishing stance are unambiguous and internally consistent. |

## Suggested subagents
- `explorer` - scan current docs/workflows for support-surface and publishing wording drift.
- `worker` - draft the ADR and aligned docs updates.
- `reviewer` - verify the final wording does not accidentally promise unsupported public artifacts.

## Risks and rollback
- Risk: The project may intentionally choose a narrow “artifact-only/local-only” stance, leaving some backlog items deferred.
- Rollback: Revert the ADR/docs commit if the chosen support boundary is rejected and restage with a revised decision statement.

## Completion notes
- Added `ADR-007` to record the supported artifact surfaces and the operator-owned deployment boundary.
- Aligned `README.md`, `SECURITY.md`, `CONTRIBUTING.md`, and `docs/index.md` with the real release workflow: tagged releases publish PyPI/GHCR artifacts, while manual release runs stay verification-only.
- Tightened `tools/check_stale_docs.py` so the old global “artifact-only” wording is now rejected while the narrower manual-run wording remains valid.
