# STAGE-006 - Feature profiles and capability gates

## Status
OPEN

## Priority
HIGH

## Source findings
- `codex-analysis/20260525-121051/project-analysis-report.md` - Critical & High Issues #5: risky demo/destructive features are all exposed behind one Basic Auth decision.
- `codex-analysis/20260525-121051/agent-reports/architect-reviewer.md` - HIGH capability boundary issue and recommendation for `serve`, `workspace`, and `lab` profiles.
- `codex-analysis/20260525-121051/agent-reports/security-auditor.md` - MEDIUM always-on high-risk methods.
- `codex-analysis/20260525-121051/agent-reports/qa-expert.md` - tests currently lock in always-on risky capabilities instead of validating profiles.

## Goal
Introduce a `FeatureSet` or `ServerProfile` single source of truth and gate risky/destructive features consistently across handler registry, CORS methods, PING/capability reporting, WebSocket availability, and UI affordances.

## Non-goals
- Fine-grained per-user roles.
- Wildcard CORS trust policy; covered by STAGE-007.
- Package rename.

## Scope
### Likely files to inspect
- `src/server.py` - feature flags, PING, WebSocket admission, server state.
- `src/cli.py` - deprecated `--advanced-upload` and new profile flags.
- `src/handlers/__init__.py` - registry construction and advanced fallback.
- `src/handlers/files.py` - destructive `DELETE` and clear behavior.
- `src/handlers/notepad.py` - `NOTE` and clear behavior.
- `src/http/cors.py` - method list.
- `src/data/static/ui/*` - UI capability display and affordances.
- `tests/test_handler_registry.py`, `tests/test_server_methods.py`, `tests/test_server_live.py` - behavior tests.

### Likely files to change
- `src/server.py` - construct and expose profile/capabilities.
- `src/cli.py` - add `--profile` or equivalent explicit feature flags.
- `src/handlers/__init__.py` - register handlers/fallbacks from capabilities.
- `src/http/cors.py` - derive allowed methods from capabilities.
- `src/data/static/ui/*` - hide or disable unavailable capabilities if capability data is exposed.
- `tests/` - add safe/workspace/lab positive and negative tests.
- `README.md`, `API.md`, `SECURITY.md` - profile capability table and migration guidance.

### Files that must not be changed
- Auth secret handling beyond consuming STAGE-005 behavior.
- Real secrets or deployment credentials.

## Dependencies
- Depends on: STAGE-001, STAGE-005
- Blocks: STAGE-007, STAGE-008, STAGE-011

## Implementation steps
1. Define explicit profiles such as `serve`, `workspace`, and `lab`, with a documented compatibility decision for the default.
2. Replace `advanced_upload_enabled = True` and deprecated no-op semantics with profile-derived capability checks.
3. Build handler registry and unknown-method advanced upload fallback from capabilities.
4. Gate destructive operations such as upload clear and note clear according to profile.
5. Derive PING/capability reporting, CORS methods, WebSocket availability, and UI state from the same profile object.
6. Add regression tests for safe profile negative paths and lab profile compatibility.
7. Update docs and browser/API smoke expectations.

## Acceptance criteria
- [ ] A safe profile can serve read/static paths without enabling advanced upload, SMUGGLE, NOTE, or destructive clear operations.
- [ ] A workspace profile can enable ordinary upload/delete only where explicitly intended.
- [ ] A lab profile preserves experimental methods intentionally and visibly.
- [ ] Handler registry, PING/capabilities, CORS method list, WebSocket availability, and UI affordances use the same capability source.
- [ ] Tests cover positive and negative paths for each profile.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `python -m pytest tests/test_handler_registry.py tests/test_server_methods.py tests/test_server_live.py tests/test_request_pipeline.py` | Registry, method, live, and pipeline tests pass with profile cases |
| Browser/UI smoke | `python tools/browser_smoke.py` | Browser smoke passes or is updated to run the intended lab profile explicitly |
| Type/lint/build | `ruff check src tests tools && ruff format --check src tests tools && mypy src` | No lint, format, or type regressions |

## Suggested subagents
- `explorer` - map all capability/reporting/UI references.
- `worker` - implement profile model and registry/server wiring.
- `qa` - add profile matrix tests and update smoke expectations.

## Risks and rollback
- Risk: Changing the default profile could break existing users.
- Rollback: Keep backward-compatible `lab` default for one release if required, but make Docker/docs use safer explicit profiles.

## Completion notes
Filled by `close-plan-stage`.

