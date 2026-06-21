# STAGE-003 - Safe operator framing and docs guardrails

## Status
OPEN

## Priority
HIGH

## Source findings
- `codex-analysis/20260621-150449/project-analysis-report.md` - README and CLI/help copy still normalize unsafe usage or unsafe exposure patterns
- `codex-analysis/20260621-150449/agent-reports/documentation-engineer.md` - README frames `SMUGGLE` as bypass/delivery workflow and top-level feature lists overstate default capabilities
- `codex-analysis/20260621-150449/agent-reports/cli-developer.md` - `--help` still offers `Public HTTPS` with `--tls`
- `codex-analysis/20260621-150449/agent-reports/security-auditor.md` - operator-facing copy should add more friction for lab-only use

## Goal
Align README, mirrored security/docs pages, CLI help, and stale-doc tooling with the actual safe posture: `SMUGGLE` is lab-only and public exposure requires the stricter operator path.

## Non-goals
- Renaming protocol methods or changing the wire/API surface
- Making `lab` easier to expose publicly
- Rebuilding the docs site navigation beyond what is needed for safety wording

## Scope
### Likely files to inspect
- `README.md` - current feature lists, quick start, and `SMUGGLE` section
- `SECURITY.md` and `docs/security.md` - security posture wording
- `docs/architecture.md` - advanced-upload and capability-gating descriptions
- `src/cli.py` - help epilog and profile/method wording
- `tools/check_stale_docs.py` and `tests/test_check_stale_docs.py` - existing stale-doc safeguards

### Likely files to change
- `README.md` - lab-only framing, top-level feature annotations, safer `SMUGGLE` wording
- `SECURITY.md` and `docs/security.md` - concise lab-only caveat if the README rewrite needs mirrored wording
- `docs/architecture.md` - make advanced-upload profile gating explicit
- `src/cli.py` - safer help epilog and method footer wording
- `tools/check_stale_docs.py` and `tests/test_check_stale_docs.py` - add phrase-level guardrails for the worst unsafe framing

### Files that must not be changed
- `src/features.py` - behavior is already correct and should stay the source of truth
- `src/settings.py` - runtime policy changes belong elsewhere
- `src/data/static/ui/files.js` - UI flow changes belong to STAGE-004

## Dependencies
- Depends on: `STAGE-001`
- Blocks: `STAGE-006`

## Implementation steps
1. Rewrite the README and mirrored/operator docs so lab-only features and public-direct requirements match the actual runtime model.
2. Replace the unsafe CLI shortcut examples and footer wording with safer operator guidance that points to auth/config-based public exposure.
3. Extend stale-doc tooling so the most harmful phrases cannot be reintroduced quietly.

## Acceptance criteria
- [ ] README no longer describes `SMUGGLE` as a DLP/proxy bypass or email/messenger delivery workflow
- [ ] `python -m exphttp --help` no longer presents `--tls` on `0.0.0.0` as a public-safe default and clearly distinguishes lab-only methods
- [ ] Stale-doc tooling fails when the banned unsafe phrases return

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `./.venv/bin/pytest -q tests/test_cli.py tests/test_check_stale_docs.py` | PASS with updated copy expectations |
| Type/lint/build | `python tools/check_stale_docs.py` and `python tools/sync_docs.py --check` | PASS with mirrored docs still in sync |
| Manual/static review | `python -m exphttp --help` and a diff review of the README/SECURITY wording | Help and docs reflect the safer operator path |

## Suggested subagents
- `explorer` - map every place where lab-only or public-exposure copy appears today
- `worker` - implement the wording and stale-doc guardrail updates with the minimum doc/code surface

## Risks and rollback
- Risk: doc rewrites can drift from mirrored docs or remove accurate capability detail
- Rollback: revert the copy changes and keep only any safe stale-doc test improvements that remain valid

## Completion notes
Filled by `close-plan-stage`.
