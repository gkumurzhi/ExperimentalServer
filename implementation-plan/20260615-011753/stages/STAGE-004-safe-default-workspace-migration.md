# STAGE-004 - Safe default workspace migration

## Status
CLOSED

## Priority
MEDIUM

## Source findings
- `codex-analysis/20260614-225437/project-analysis-report.md` - Executive Summary: make `workspace` the new-user direction and preserve `lab` as explicit opt-in.
- `codex-analysis/20260614-225437/agent-reports/product-manager.md` - Concrete Recommendations: default should report `workspace`; lab-only capabilities should be false by default; `--profile lab` preserves old behavior.
- `codex-analysis/20260614-225437/agent-reports/security-auditor.md` - F1: broad `lab` default is risky for packaged/container exposure.
- `codex-analysis/20260614-225437/agent-reports/project-manager.md` - STAGE-004 acceptance criteria.

## Goal
If STAGE-002 approves the recommended path, migrate the new-user default profile to `workspace` while keeping explicit `--profile lab` compatibility and clear migration docs.

## Non-goals
- Do not remove `lab` or lab-only features.
- Do not change Docker defaults unless STAGE-008 is being closed.
- Do not implement API v1 or durable Notepad.

## Scope
### Likely files to inspect
- `src/features.py` - `DEFAULT_PROFILE`, profile capabilities, methods.
- `src/cli.py` - CLI help/default behavior.
- `README.md`, `API.md`, `SECURITY.md`, `CHANGELOG.md` - default-profile and migration docs.
- `tests/test_cli.py`, `tests/test_server_methods.py`, `tests/test_server_live.py`, `tests/test_handler_registry.py` - default and explicit-profile behavior.
- `tools/browser_smoke.py` - profile argument support may belong to STAGE-006.

### Likely files to change
- `src/features.py` - set new default to `workspace` if approved.
- `src/cli.py` - help text and default profile display.
- `README.md`, `API.md`, `SECURITY.md`, `CHANGELOG.md`, `docs/**` mirrors - document migration and explicit `--profile lab`.
- `tests/test_cli.py`, `tests/test_server_methods.py`, `tests/test_server_live.py`, `tests/test_handler_registry.py` - update default-profile expectations and add explicit lab compatibility assertions.

### Files that must not be changed
- `examples/docker/docker-compose.yml` and `Dockerfile` - Docker posture changes are STAGE-008.
- `src/data/static/ui/**` - UI disabled-state hardening is STAGE-005/006 unless a tiny label update is unavoidable.
- `.github/workflows/**` - risk lanes are STAGE-006 and Python 3.14 is STAGE-007.
- `.env*`, credentials, keys, certificates - secrets are out of scope.

## Dependencies
- Depends on: STAGE-002, STAGE-003
- Blocks: STAGE-006, STAGE-008

## Implementation steps
1. Re-read the STAGE-002 ADR and confirm the approved path is `workspace` default; if it is not, update this stage scope before implementation.
2. Change the new-user default profile to `workspace` in the single source of truth.
3. Update CLI help and docs so old lab behavior is reached by explicit `--profile lab`.
4. Update default-profile tests to expect `workspace` capabilities: ordinary file operations enabled, lab-only capabilities disabled.
5. Add or preserve explicit `--profile lab` tests for advanced upload, SMUGGLE, NOTE, WebSocket notes, and clears.
6. Run targeted tests and docs checks.

## Acceptance criteria
- [ ] Default `exphttp` startup reports profile `workspace`.
- [ ] Ordinary upload, browse, download, and delete file workflows still work by default.
- [ ] `advanced_upload`, `smuggle`, `note_http`, `websocket_notes`, destructive clears, and lab-only behavior are disabled by default according to capabilities.
- [ ] `--profile lab` preserves previous lab behavior.
- [ ] README/API/SECURITY/CHANGELOG describe the migration and compatibility path.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `python -m pytest tests/test_cli.py tests/test_server_methods.py tests/test_server_live.py tests/test_handler_registry.py` | Exits 0 with updated default/profile assertions. |
| Docs checks | `python tools/sync_docs.py --check && python tools/check_stale_docs.py` | Exits 0. |
| Type/lint/build | `python -m compileall src tests` | Exits 0. |
| Manual/static review | Compare default and `--profile lab` capability payloads | Default is `workspace`; explicit `lab` is compatible. |

## Suggested subagents
- `explorer` - enumerate all default-profile assumptions before edits.
- `worker` - implement default migration and tests.
- `reviewer` - check compatibility for explicit `--profile lab`.

## Risks and rollback
- Risk: scripts relying on implicit `lab` behavior can break.
- Rollback: restore the previous default value and docs, leaving explicit-profile tests in place where useful.

## Completion notes
Closed 2026-06-15 13:59:42 +0300.

- `DEFAULT_PROFILE` now resolves to `workspace`; default CLI/server startup and
  `PING` report workspace capabilities.
- Deprecated `--advanced-upload` now maps to `--profile lab` so old advanced
  upload invocations keep the compatibility path after the default migration.
- Default tests now prove ordinary upload/delete workflows continue while
  advanced upload, SMUGGLE, NOTE, WebSocket notes, destructive clears, and
  lab-only unknown-method behavior are disabled by default.
- Explicit lab-profile tests cover advanced upload fallback, CORS unknown
  methods, SMUGGLE/NOTE/WebSocket surface, upload clear, and note clear.
- README/API/SECURITY/CHANGELOG and generated docs mirrors describe the
  workspace default and explicit lab compatibility path.
- Verification passed: targeted pytest lane (`250 passed`), docs checks,
  compileall, default/lab capability payload check, `git diff --check`, and
  subagent review after follow-up fixes.
