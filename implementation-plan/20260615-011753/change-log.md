# Change Log

## 2026-06-15 17:30:16 +0300 - STAGE-011
- Status: CLOSED
- Files changed: `src/handlers/notepad.py`, `src/server.py`, `tests/test_websocket_handlers.py`, `API.md`, `docs/api.md`, `implementation-plan/20260615-011753/stages/STAGE-011-websocket-notepad-safety.md`, `implementation-plan/20260615-011753/stage-status.md`, `implementation-plan/20260615-011753/change-log.md`, `implementation-plan/20260615-011753/stage-reports/STAGE-011-20260615-170742.md`
- Verification: Targeted WebSocket/security lane passed (`91 passed`); live server tests passed (`13 passed`); docs sync/stale checks, ruff check/format, mypy, `git diff --check`, explorer mapping, and reviewer diff review passed. `uv run --extra lint ...` was blocked by a pre-existing broken ignored `.venv` `acme` install, which was repaired before direct `.venv` lint/type verification.
- Report: `stage-reports/STAGE-011-20260615-170742.md`

## 2026-06-15 17:02:55 +0300 - STAGE-010
- Status: CLOSED
- Files changed: `API.md`, `docs/api.md`, `README.md`, `implementation-plan/20260615-011753/stages/STAGE-010-api-contract-stability.md`, `implementation-plan/20260615-011753/stage-status.md`, `implementation-plan/20260615-011753/change-log.md`, `implementation-plan/20260615-011753/stage-reports/STAGE-010-20260615-165022.md`
- Verification: `python tools/sync_docs.py --check`, `python tools/check_stale_docs.py`, and `python -m pytest tests/test_server_methods.py tests/test_websocket_handlers.py tests/test_handlers/test_notepad.py` passed.
- Report: `stage-reports/STAGE-010-20260615-165022.md`

## 2026-06-15 16:40:18 +0300 - STAGE-009
- Status: CLOSED
- Files changed: `src/storage.py`, `tests/test_handlers/test_files.py`, `tests/benchmarks/test_workspace_hot_paths.py`, `implementation-plan/20260615-011753/stages/STAGE-009-workspace-performance-baseline.md`, `implementation-plan/20260615-011753/stage-status.md`, `implementation-plan/20260615-011753/change-log.md`, `implementation-plan/20260615-011753/stage-reports/STAGE-009-20260615-161853.md`
- Verification: Benchmark-only lane passed in a temporary environment with `pytest-benchmark 5.2.3`; base interpreter benchmark collection skips cleanly without the optional plugin; upload/storage/INFO tests, metrics/live tests, ruff, and `git diff --check` passed.
- Report: `stage-reports/STAGE-009-20260615-161853.md`

## 2026-06-15 16:08:11 +0300 - STAGE-008
- Status: CLOSED
- Files changed: `.github/workflows/ci.yml`, `.github/workflows/release.yml`, `Dockerfile`, `examples/docker/docker-compose.yml`, `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `docs/contributing.md`, `docs/security.md`, `implementation-plan/20260615-011753/stages/STAGE-008-docker-rollback-boundary.md`, `implementation-plan/20260615-011753/stage-status.md`, `implementation-plan/20260615-011753/change-log.md`, `implementation-plan/20260615-011753/stage-reports/STAGE-008-20260615-154500.md`
- Verification: Compose config for default/auth-tls/acme passed; docs sync and stale-doc checks passed; workflow YAML parse, Docker smoke shell syntax check, `git diff --check`, and local Docker build/run/PING smoke passed. The first optional Docker smoke exposed the Dockerfile's missing `exphttp/` package copy, which was fixed before closure.
- Report: `stage-reports/STAGE-008-20260615-154500.md`

## 2026-06-15 15:39:55 +0300 - STAGE-007
- Status: CLOSED
- Files changed: `.github/workflows/ci.yml`, `.github/workflows/security.yml`, `pyproject.toml`, `constraints/ci.txt`, `README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `docs/index.md`, `docs/changelog.md`, `docs/contributing.md`, `src/cli.py`, `src/handlers/__init__.py`, `implementation-plan/20260615-011753/stages/STAGE-007-python-314-readiness.md`, `implementation-plan/20260615-011753/stage-status.md`, `implementation-plan/20260615-011753/change-log.md`, `implementation-plan/20260615-011753/stage-reports/STAGE-007-20260615-150708.md`
- Verification: Python 3.14 constrained install, `pip check`, import smoke, full pytest (`851 passed`), dependency constraint check, `pip-audit`, package build, and installed-wheel smoke passed; clean Python 3.12 full pytest passed; docs sync/stale checks, ruff, mypy, workflow YAML parse, targeted post-ruff tests, and `git diff --check` passed.
- Report: `stage-reports/STAGE-007-20260615-150708.md`

## 2026-06-15 15:00:26 +0300 - STAGE-006
- Status: CLOSED
- Files changed: `.github/workflows/ci.yml`, `tools/browser_smoke.py`, `tools/browser_smoke.playwright.js`, `implementation-plan/20260615-011753/stages/STAGE-006-profile-aware-smoke-risk-test-gates.md`, `implementation-plan/20260615-011753/stage-status.md`, `implementation-plan/20260615-011753/change-log.md`, `implementation-plan/20260615-011753/stage-reports/STAGE-006-20260615-144027.md`
- Verification: Browser smoke help, static UI check, JavaScript syntax check, ruff check/format check, lab full smoke, workspace disabled-state smoke, serve disabled-state smoke, and all named pytest risk lanes passed. The property lane needed a temporary `/tmp` Hypothesis install because the system Python is externally managed.
- Report: `stage-reports/STAGE-006-20260615-144027.md`

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
