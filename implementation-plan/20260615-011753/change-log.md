# Change Log

## 2026-06-15 14:34:39 +0300 - STAGE-005
- Status: CLOSED
- Files changed: `src/data/index.html`, `src/data/static/ui/core.js`, `src/data/static/ui/features.css`, `src/data/static/ui/notepad.js`, `tools/browser_smoke.playwright.js`, `implementation-plan/20260615-011753/stages/STAGE-005-notepad-ui-accessibility-hardening.md`, `implementation-plan/20260615-011753/stage-status.md`, `implementation-plan/20260615-011753/change-log.md`, `implementation-plan/20260615-011753/stage-reports/STAGE-005-20260615-140638.md`
- Verification: Static UI asset check passed; targeted Notepad/WebSocket handler lane passed (`90 passed`); browser smoke passed with warning, label, capability, error-detail, and focus assertions; `node --check` on touched JavaScript and `git diff --check` passed.
- Report: `stage-reports/STAGE-005-20260615-140638.md`

## 2026-06-15 13:59:42 +0300 - STAGE-004
- Status: CLOSED
- Files changed: `src/features.py`, `src/cli.py`, `tests/test_cli.py`, `tests/test_server_methods.py`, `tests/test_server_live.py`, `tests/test_security/test_websocket_upgrade.py`, `README.md`, `API.md`, `SECURITY.md`, `CHANGELOG.md`, `docs/api.md`, `docs/security.md`, `docs/changelog.md`, `docs/ADR/ADR-006-profile-default-and-exposure.md`, `implementation-plan/20260615-011753/stages/STAGE-004-safe-default-workspace-migration.md`, `implementation-plan/20260615-011753/stage-status.md`, `implementation-plan/20260615-011753/change-log.md`, `implementation-plan/20260615-011753/stage-reports/STAGE-004-20260615-133030.md`
- Verification: Baseline implicit-lab behavior recorded before migration; targeted STAGE-004 pytest lane passed (`250 passed`); docs mirror/stale checks passed; `python -m compileall src tests` passed; default/lab capability payload check passed; `git diff --check` passed; explorer and reviewer subagents completed, with reviewer gaps fixed before closure.
- Report: `stage-reports/STAGE-004-20260615-133030.md`

## 2026-06-15 13:26:08 +0300 - STAGE-003
- Status: CLOSED
- Files changed: `src/features.py`, `src/http/cors.py`, `src/handlers/__init__.py`, `src/handlers/base.py`, `src/server.py`, `tests/test_handler_registry.py`, `tests/test_server_methods.py`, `tests/test_server_routing.py`, `tests/test_websocket_handlers.py`, `tests/test_handlers/test_files.py`, `tests/test_handlers/test_notepad.py`, `tests/test_handlers/test_handler_integration.py`, `implementation-plan/20260615-011753/stages/STAGE-003-capability-policy-boundary.md`, `implementation-plan/20260615-011753/stage-status.md`, `implementation-plan/20260615-011753/change-log.md`, `implementation-plan/20260615-011753/stage-reports/STAGE-003-20260615-130908.md`
- Verification: Targeted stage pytest lane passed (`120 passed`); optional pipeline/live lane passed (`28 passed`); affected handler/stub suites passed (`228 passed`); `python -m compileall src tests`, targeted `ruff check`, and `git diff --check` passed; reviewer subagent found no blocking issues and ran an extra focused slice (`9 passed`).
- Report: `stage-reports/STAGE-003-20260615-130908.md`

## 2026-06-15 13:04:45 +0300 - STAGE-002
- Status: CLOSED
- Files changed: `README.md`, `SECURITY.md`, `docs/ADR/ADR-006-profile-default-and-exposure.md`, `docs/ADR/README.md`, `docs/security.md`, `docs/threat-model.md`, `implementation-plan/20260615-011753/stages/STAGE-002-profile-exposure-decision-gate.md`, `implementation-plan/20260615-011753/stage-status.md`, `implementation-plan/20260615-011753/change-log.md`, `implementation-plan/20260615-011753/stage-reports/STAGE-002-20260615-125438.md`
- Verification: `python tools/sync_docs.py --check` passed; `python tools/check_stale_docs.py` passed; manual/static diff review confirmed runtime defaults, Docker files, workflows, and code were unchanged. Optional `mkdocs build --strict` could not run because `mkdocs` is unavailable locally.
- Report: `stage-reports/STAGE-002-20260615-125438.md`

## 2026-06-15 12:50:25 +0300 - STAGE-001
- Status: CLOSED
- Files changed: `.pre-commit-config.yaml`, `CHANGELOG.md`, `docs/api.md`, `docs/changelog.md`, `docs/contributing.md`, `docs/index.md`, `implementation-plan/20260615-011753/stages/STAGE-001-docs-mirror-release-hygiene.md`, `implementation-plan/20260615-011753/stage-status.md`, `implementation-plan/20260615-011753/change-log.md`, `implementation-plan/20260615-011753/stage-reports/STAGE-001-20260615-124223.md`
- Verification: `python tools/sync_docs.py --check` passed; `python tools/check_stale_docs.py` passed; `.pre-commit-config.yaml` parsed; `pre-commit` and `mkdocs` executables were unavailable locally.
- Report: `stage-reports/STAGE-001-20260615-124223.md`
