# STAGE-003 - Capability policy boundary

## Status
OPEN

## Priority
MEDIUM

## Source findings
- `codex-analysis/20260614-225437/agent-reports/architect-reviewer.md` - Medium: profile/capability policy is not yet a single reusable boundary.
- `codex-analysis/20260614-225437/project-analysis-report.md` - Architecture & Design: one profile change should flow through `PING`, handler registry, CORS preflight, browser mutation guard, WebSocket admission, and UI affordances.
- `codex-analysis/20260614-225437/agent-reports/project-manager.md` - STAGE-003: centralize profile-derived policy before default migration.

## Goal
Create a small, tested policy boundary for profile-derived behavior so future default-profile changes do not require scattered edits across server, CORS, handlers, UI, docs, and tests.

## Non-goals
- Do not change the default profile.
- Do not redesign the handler registry or add a general upgrade router.
- Do not create a public Python API unless explicitly needed by existing shims.

## Scope
### Likely files to inspect
- `src/features.py` - profile and capability definitions.
- `src/server.py` - method exposure, browser mutation guard, and WebSocket admission.
- `src/http/cors.py` - CORS method/origin policy.
- `src/handlers/base.py`, `src/handlers/files.py`, `src/handlers/notepad.py` - destructive-operation gates and default feature fallback.
- `src/data/static/ui/core.js` - UI capability ingestion and mapping.
- `tests/test_handler_registry.py`, `tests/test_server_methods.py`, `tests/test_security/test_websocket_upgrade.py` - existing profile/feature coverage.

### Likely files to change
- `src/features.py` - add `FeatureSet` helpers or a small `CapabilityPolicy` boundary.
- `src/server.py` and `src/http/cors.py` - consume shared policy helpers for methods/CORS/mutation/WS route admission.
- `src/handlers/base.py` and selected handlers - remove default-lab masking where tests should pass explicit features.
- `tests/test_handler_registry.py`, `tests/test_server_methods.py`, `tests/test_security/test_websocket_upgrade.py`, `tests/test_request_pipeline.py` - assert profile behavior flows through all surfaces.
- `docs/architecture.md` - document `features.py`, `storage.py`, and capability flow if not already covered.

### Files that must not be changed
- `src/data/static/ui/**` - unless a minimal capability mapping test fixture requires it; UI behavior changes are STAGE-005/006.
- `README.md`, `API.md`, `SECURITY.md` - docs migration belongs to dependent stages unless architecture docs need a small update.
- `.github/workflows/**` - CI lane changes are STAGE-006.
- `.env*`, credentials, keys, certificates - secrets are out of scope.

## Dependencies
- Depends on: STAGE-002
- Blocks: STAGE-004, STAGE-005, STAGE-006, STAGE-009, STAGE-011

## Implementation steps
1. Identify all current profile-derived decisions in server, CORS, handler, WebSocket, and UI capability mapping.
2. Add focused helpers on `FeatureSet` or a small `CapabilityPolicy` class for allowed methods, CORS exposure, browser mutation classification, WebSocket route enablement, and destructive operation capability checks.
3. Replace duplicated ad hoc checks with the shared helpers while preserving current behavior.
4. Update handler test stubs so they pass explicit features instead of relying on default `lab`.
5. Add one focused regression test proving a profile change flows through `PING`, registry, CORS preflight, browser mutation guard, and WebSocket admission.
6. Run targeted tests and update architecture docs only if the new boundary changes the documented module map.

## Acceptance criteria
- [ ] Profile-derived method exposure, CORS exposure, browser mutation policy, and WebSocket route admission use shared policy helpers.
- [ ] Destructive operation checks remain capability-specific and preserve existing `lab` behavior.
- [ ] Tests fail if a profile/capability change reaches `PING` but not CORS, registry, mutation guard, or WebSocket admission.
- [ ] Handler tests no longer hide missing setup by relying on an implicit default-lab fallback where explicit features are needed.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `python -m pytest tests/test_handler_registry.py tests/test_server_methods.py tests/test_security/test_websocket_upgrade.py` | Exits 0. |
| Pipeline/profile tests | `python -m pytest tests/test_request_pipeline.py tests/test_server_live.py` | Exits 0 or documents unrelated pre-existing failures. |
| Type/lint/build | `python -m compileall src tests` | Exits 0. |
| Manual/static review | Trace one capability through `PING`, registry, CORS, mutation guard, and WS admission | Shared policy is used consistently. |

## Suggested subagents
- `explorer` - map all existing profile/capability checks before implementation.
- `worker` - implement the shared policy boundary and tests.
- `reviewer` - check compatibility and avoid broad refactors.

## Risks and rollback
- Risk: centralization can accidentally change CORS/method behavior for existing profiles.
- Rollback: revert the policy-boundary commit and rerun the pre-stage targeted profile tests to confirm old behavior returns.

## Completion notes
Filled by `close-plan-stage`.
