# STAGE-005 - Add browser-origin guardrails for mutating HTTP requests

## Status
OPEN

## Priority
HIGH

## Source findings
- `project-analysis-report.md` - F-005: mutating HTTP handlers dispatch after Basic Auth without same-origin or CSRF checks.

## Goal
Centralize browser-origin guardrails for state-changing HTTP requests so cached browser credentials cannot be abused cross-site by default.

## Non-goals
- Do not remove Basic Auth.
- Do not break documented non-browser API clients without an explicit compatibility path.

## Scope
### Likely files to inspect
- `src/request_pipeline.py` and `src/server.py` - request dispatch/auth pipeline.
- `src/handlers/*` - state-changing method list.
- CORS/origin validation tests in `tests/test_server_methods.py` and `tests/test_request_pipeline.py`.
- README/API docs for CORS and auth behavior.

### Likely files to change
- Request pipeline/server policy helpers.
- CLI/config for opt-in/out if needed.
- Tests for Origin, `Sec-Fetch-Site`, same-origin UI, and API clients.
- Docs for default behavior.

### Files that must not be changed
- WebSocket origin validation logic except for shared helper reuse.

## Dependencies
- Depends on: STAGE-001
- Blocks: STAGE-007, STAGE-008

## Implementation steps
1. Define which methods/paths are mutating and browser-protected.
2. Add tests for cross-site `Origin`, missing origin, same-origin, configured CORS origin, and non-browser clients.
3. Implement centralized policy with clear defaults.
4. Ensure UI requests still work under localhost/trusted-lab defaults.
5. Document the policy and migration knobs.

## Acceptance criteria
- [ ] Cross-site browser-origin mutating requests are rejected by default.
- [ ] Same-origin UI mutations continue to work.
- [ ] Non-browser clients have documented behavior and tests.
- [ ] CORS response policy and mutation protection do not contradict each other.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Pipeline tests | `pytest -q tests/test_request_pipeline.py tests/test_server_methods.py -k 'Origin or cors or mutation or csrf or fetch'` | Pass. |
| Handler smoke | `pytest -q tests/test_handlers/test_handler_integration.py` | Pass. |
| Browser smoke | `node tools/browser_smoke.playwright.js` if available | Same-origin UI paths pass. |

## Suggested subagents
- `security-auditor` - review browser-origin policy and bypass cases.
- `backend-developer` - implement request pipeline changes.

## Risks and rollback
- Risk: Strict default rejects existing scripted clients that send Origin headers.
- Rollback: Add compatibility flag while keeping secure default and docs.

## Completion notes
Filled by `close-plan-stage`.
