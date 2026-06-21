# STAGE-005 - Plugin core-method reservation

## Status
OPEN

## Priority
MEDIUM

## Source findings
- `codex-analysis/20260621-150449/agent-reports/security-auditor.md` - plugins can reuse disabled built-in method names without explicit override intent
- `codex-analysis/20260621-150449/project-analysis-report.md` - plugin method reservation is incomplete and can blur profile boundaries

## Goal
Reserve built-in method names across profiles so plugins cannot silently claim disabled core names unless an explicit override mode is enabled.

## Non-goals
- Broadening plugin capabilities or adding new plugin discovery behavior
- Changing the `FeatureSet` definition of which methods belong to each profile
- Reworking unrelated extension packaging or loading behavior

## Scope
### Likely files to inspect
- `src/server.py` - current plugin/core-method collision checks
- `src/extensions.py` - plugin method spec defaults and override semantics
- `tests/test_extensions.py` - existing plugin registration coverage
- `README.md` and `docs/architecture.md` - plugin override policy wording

### Likely files to change
- `src/server.py` - reserve the global built-in method namespace, not only currently registered methods
- `src/extensions.py` - make explicit override intent easy to reason about if runtime checks need metadata
- `tests/test_extensions.py` - regression coverage for a workspace plugin attempting `SMUGGLE`
- `README.md` and `docs/architecture.md` - document the sharpened override rule

### Files that must not be changed
- `src/features.py` - profile method membership should not move
- `src/handlers/` - built-in handlers do not need behavioral changes for this policy
- `src/data/` - UI changes are unrelated

## Dependencies
- Depends on: `None`
- Blocks: `None`

## Implementation steps
1. Identify the authoritative set of built-in method names that must remain reserved regardless of the active profile.
2. Tighten plugin registration checks so disabled built-in names still count as reserved unless explicit core override is enabled.
3. Add regression tests and minimal docs that describe the boundary clearly.

## Acceptance criteria
- [ ] A plugin cannot register `SMUGGLE` in `workspace` or `serve` unless the explicit core-override path is enabled
- [ ] Existing legitimate plugin registration paths still work
- [ ] Docs describe the difference between capability gating and core-method override intent

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `./.venv/bin/pytest -q tests/test_extensions.py tests/test_server_methods.py` | PASS with the new reservation regression covered |
| Type/lint/build | `./.venv/bin/pytest -q tests/test_handler_registry.py` | PASS if handler registration paths are touched indirectly |
| Manual/static review | Review plugin override docs/examples | Wording matches runtime behavior and does not imply profile bypass |

## Suggested subagents
- `explorer` - trace current plugin registration and override checks
- `worker` - implement the reservation rule and focused regression tests

## Risks and rollback
- Risk: over-tightening the rule could break legitimate plugin methods unrelated to built-in names
- Rollback: revert the reservation logic and keep only the safe documentation clarifications if they still reflect reality

## Completion notes
Filled by `close-plan-stage`.
