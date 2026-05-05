# STAGE-001 - Restore release-smoke stale-doc guard

## Status
OPEN

## Priority
HIGH

## Source findings
- `codex-analysis/20260505-193249/project-analysis-report.md` - Critical & High Issues #2: release smoke exits before browser/Docker validation.
- `codex-analysis/20260505-193249/agent-reports/devops-engineer.md` - finding 1: `.github/workflows/ci.yml:164-167` matches valid changelog text.
- `codex-analysis/20260505-193249/agent-reports/reviewer.md` - HIGH blocker: grep matches `docs/changelog.md:38`.

## Goal
Make the release-smoke stale-reference guard reject only genuinely stale active contract text while allowing valid changelog/history entries, so browser and Docker smoke can run.

## Non-goals
- Do not change browser smoke or Docker smoke behavior in this stage.
- Do not rewrite changelog history just to satisfy a broad grep.
- Do not update dependency/UI copy; that is STAGE-006.

## Scope
### Likely files to inspect
- `.github/workflows/ci.yml` - current release-smoke grep and smoke sequence.
- `README.md` - active docs text checked by stale guard.
- `API.md` - active API text checked by stale guard.
- `docs/changelog.md` - known false-positive historical text.
- `CHANGELOG.md` - root changelog mirror/source.
- `CLAUDE.md` - current stale guard input.
- `examples/` - current stale guard input.

### Likely files to change
- `.github/workflows/ci.yml` - replace inline broad grep or narrow patterns/allowlists.
- `tools/check_stale_docs.py` - optional small checked script if inline shell becomes too brittle.
- `tests/` or `tools/` tests - optional regression for stale-doc checker if a script is added.

### Files that must not be changed
- `src/**` - no runtime behavior change is needed.
- `docs/changelog.md` / `CHANGELOG.md` - do not delete valid historical release notes just to satisfy CI.
- `.env*`, credentials, keys, certificates - never read or edit secrets.

## Dependencies
- Depends on: `None`
- Blocks: STAGE-002, STAGE-003, STAGE-004, STAGE-005, STAGE-006, STAGE-007, STAGE-008, STAGE-009, STAGE-010, STAGE-011, STAGE-012, STAGE-013

## Implementation steps
1. Reproduce the current false positive with the same pattern used by `.github/workflows/ci.yml`.
2. Replace the guard with either a narrow inline check or a small `tools/check_stale_docs.py` script that separates active docs from historical/changelog/ADR context.
3. Keep the known stale-contract patterns that still matter, but allow intentionally historical mentions with explicit comments or an allowlist.
4. Add a minimal regression check if a script is introduced.
5. Run the release-smoke sanity command block far enough to prove the stale guard passes and would continue to browser/Docker smoke.

## Acceptance criteria
- [ ] The known `advanced upload is enabled by default` changelog/history entry no longer fails release smoke.
- [ ] Active stale references are still detected in active docs or examples.
- [ ] The workflow remains readable and fails with an actionable message.
- [ ] Browser and Docker smoke steps are no longer blocked by the stale-doc guard.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Current false-positive reproduction | Run the old grep command from `.github/workflows/ci.yml` before changing, if still present | Confirms the baseline blocker |
| Targeted stale guard | Run the new inline command or `python tools/check_stale_docs.py` | Exits 0 on current intended docs |
| CLI sanity | `python -m src --dir /tmp --version && python -m src --help > /dev/null && python examples/notepad_client.py --help > /dev/null` | Exits 0 in a dependency-complete environment |
| Static check | `bash -n .github/workflows/ci.yml` is not valid for YAML; inspect workflow syntax or run relevant script tests | No syntax/tooling regression |

## Suggested subagents
- `explorer` - confirm all current stale-reference matches and identify which are historical vs active.
- `worker` - implement the smallest workflow/script change and targeted regression.
- `devops-engineer` - review CI behavior and failure message clarity.

## Risks and rollback
- Risk: Over-narrowing the guard can miss real stale docs.
- Rollback: Revert this stage's workflow/script changes and restore the previous grep while preserving any captured false-positive evidence.

## Completion notes
Filled by `close-plan-stage`.
