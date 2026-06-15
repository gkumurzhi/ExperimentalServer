# STAGE-006 - Profile-aware smoke and risk test gates

## Status
CLOSED

## Priority
MEDIUM

## Source findings
- `codex-analysis/20260614-225437/agent-reports/qa-expert.md` - P2/P3: browser smoke is lab-only and critical test coverage is not explicitly gated.
- `codex-analysis/20260614-225437/agent-reports/frontend-developer.md` - Issue 4: `serve`/`workspace` disabled states are not release-protected.
- `codex-analysis/20260614-225437/agent-reports/accessibility-tester.md` - Coverage: profile-disabled UX lacks smoke/a11y coverage.
- `codex-analysis/20260614-225437/agent-reports/project-manager.md` - STAGE-006 acceptance criteria.

## Goal
Add profile-aware browser smoke and named risk-specific test lanes so default-profile and high-risk module regressions are caught directly.

## Non-goals
- Do not broaden this into a full test-suite rewrite.
- Do not change product behavior except what is required to expose profile smoke options.
- Do not raise coverage thresholds blindly without a recorded baseline.

## Scope
### Likely files to inspect
- `tools/browser_smoke.py` - currently hardcodes `profile="lab"`.
- `tools/browser_smoke.playwright.js` - current lab happy-path and UI assertions.
- `.github/workflows/ci.yml` - current pytest, browser, Docker, and docs jobs.
- `pyproject.toml` - pytest configuration and markers.
- `tests/test_property/test_request_parser.py`, `tests/test_security/test_auth.py`, `tests/test_security/test_websocket_upgrade.py`, `tests/test_handlers/test_files.py`, `tests/test_handlers/test_notepad.py`, `tests/test_websocket_handlers.py` - candidate risk lanes.

### Likely files to change
- `tools/browser_smoke.py` - add `--profile` support and keep lab default/full smoke behavior.
- `tools/browser_smoke.playwright.js` - add minimal `serve`/`workspace` disabled-state assertions.
- `.github/workflows/ci.yml` - add named deterministic risk lanes or clear job steps.
- `pyproject.toml` - add markers only if needed for named lanes.
- `README.md` or `CONTRIBUTING.md` - document risk-lane commands if contributor docs require it.

### Files that must not be changed
- `src/features.py` and `src/cli.py` - default behavior changes are STAGE-004.
- `src/data/static/ui/**` - UI behavior fixes are STAGE-005 unless smoke reveals a small missing hook.
- `.github/workflows/release.yml` - release lane changes are out of scope unless CI naming must be mirrored.
- `.env*`, credentials, keys, certificates - secrets are out of scope.

## Dependencies
- Depends on: STAGE-004, STAGE-005
- Blocks: `None`

## Implementation steps
1. Add a `--profile` option to `tools/browser_smoke.py` while preserving full lab smoke as the default or named mode.
2. Add short `serve` and `workspace` smoke paths that assert disabled/unavailable Notepad and lab-only controls, accessible names, keyboard basics, and live/status messages.
3. Define named risk-specific pytest commands for parser/framing, auth, CORS/profile, storage/quota, WebSocket/Notepad, and docs/static UI checks.
4. Add CI steps or documented commands for those lanes without replacing the full suite.
5. Record initial lane outputs or coverage baselines before enforcing stricter no-regression behavior.
6. Run targeted lanes locally where feasible and leave CI as source of truth for browser/environment-dependent checks.

## Acceptance criteria
- [x] Browser smoke can run full lab behavior and minimal `serve`/`workspace` disabled-state behavior.
- [x] CI or contributor docs expose named risk lanes for parser/framing, auth, CORS/profile, storage/quota, and WebSocket/Notepad.
- [x] Profile-disabled UI expectations are asserted for the chosen default path.
- [x] Any new coverage threshold or no-regression rule has a recorded baseline.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Browser smoke help | `python tools/browser_smoke.py --help` | Shows profile/mode options. |
| Static UI check | `python tools/check_static_ui_assets.py --repo-root .` | Exits 0. |
| Risk lanes | `python -m pytest tests/test_property/test_request_parser.py tests/test_property/test_ws_frame_parser.py tests/test_security/test_auth.py tests/test_security/test_websocket_upgrade.py tests/test_handlers/test_files.py tests/test_handlers/test_notepad.py tests/test_websocket_handlers.py` | Exits 0 or records pre-existing unrelated failures. |
| CI workflow review | Inspect `.github/workflows/ci.yml` | Named lanes are deterministic and do not remove existing full-suite coverage. |

## Suggested subagents
- `explorer` - map current smoke script assumptions and CI jobs.
- `worker` - implement profile smoke options and named lanes.
- `qa-reviewer` - review lane naming and baseline strategy if available.

## Risks and rollback
- Risk: profile smoke can become flaky if it duplicates too much of the full lab happy path.
- Rollback: keep full lab smoke unchanged, revert only new profile-mode assertions, and keep named pytest lanes as local commands until stable.

## Completion notes
Closed 2026-06-15 15:00:26 +0300. `tools/browser_smoke.py` now accepts
`--profile {lab,workspace,serve}` and `--mode {auto,full,disabled-state}`;
`lab` remains the default full smoke path, while `workspace` and `serve`
assert profile-disabled UI capability states. CI now exposes named risk-lane
steps for parser/framing, auth, CORS/profile policy, storage/quota, and
WebSocket/Notepad, and the release smoke job runs lab plus workspace/serve
browser profile gates. No stricter coverage threshold or no-regression rule was
added, so no new coverage baseline is required; initial lane pass counts are
recorded in `stage-reports/STAGE-006-20260615-144027.md`.
