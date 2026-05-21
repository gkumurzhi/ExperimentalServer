# Change Log

## 2026-05-05 21:25:59 MSK — STAGE-001
- Status: CLOSED
- Files changed: `.github/workflows/ci.yml`, `tools/check_stale_docs.py`, `tests/test_check_stale_docs.py`, `implementation-plan/20260505-205639/stages/STAGE-001-release-smoke-stale-doc-guard.md`, `implementation-plan/20260505-205639/stage-status.md`, `implementation-plan/20260505-205639/stage-reports/STAGE-001-20260505-212559.md`
- Verification: stale-doc checker, targeted tests, ruff, CLI/example sanity, release-smoke sanity block, explorer review, and devops-engineer review passed.
- Report: `stage-reports/STAGE-001-20260505-212559.md`

## 2026-05-05 21:43:24 MSK — STAGE-002
- Status: CLOSED
- Files changed: `examples/notepad_client.py`, `tests/test_security/test_keys.py`, `API.md`, `docs/api.md`, `implementation-plan/20260505-205639/stages/STAGE-002-secure-notepad-key-contract.md`, `implementation-plan/20260505-205639/stage-status.md`, `implementation-plan/20260505-205639/stage-reports/STAGE-002-20260505-213422.md`
- Verification: focused Notepad example interoperability regression, targeted key/NOTE/WebSocket tests, example sanity, docs sync, ruff, static docs review, diff/compile checks, explorer review, reviewer review, and security-auditor review passed.
- Report: `stage-reports/STAGE-002-20260505-213422.md`

## 2026-05-05 22:08:12 MSK — STAGE-003
- Status: CLOSED
- Files changed: `src/security/tls.py`, `src/security/tls_manager.py`, `tests/test_security/test_tls.py`, `tests/test_security/test_tls_manager.py`, `implementation-plan/20260505-205639/stages/STAGE-003-acme-cache-pair-validation.md`, `implementation-plan/20260505-205639/stage-status.md`, `implementation-plan/20260505-205639/stage-reports/STAGE-003-20260505-214641.md`
- Verification: targeted TLS tests, mypy, ruff, compileall, CLI smoke, static secret review, Context7 cryptography docs check, explorer review, correctness review, and security-auditor re-review passed.
- Report: `stage-reports/STAGE-003-20260505-214641.md`

## 2026-05-05 22:22:27 MSK — STAGE-004
- Status: CLOSED
- Files changed: `src/cli.py`, `src/server.py`, `tests/test_cli.py`, `implementation-plan/20260505-205639/stages/STAGE-004-cli-tls-and-limit-validation.md`, `implementation-plan/20260505-205639/stage-status.md`, `implementation-plan/20260505-205639/stage-reports/STAGE-004-20260505-221247.md`
- Verification: targeted CLI and TLS manager tests, CLI help, safe invalid-argument subprocess checks, ruff, mypy, diff checks, explorer review, correctness review, and final CLI verification review passed.
- Report: `stage-reports/STAGE-004-20260505-221247.md`

## 2026-05-05 22:41:47 MSK — STAGE-005
- Status: CLOSED
- Files changed: `Dockerfile`, `examples/docker/docker-compose.yml`, `README.md`, `docs/architecture.md`, `implementation-plan/20260505-205639/stages/STAGE-005-container-acme-sslip-guidance.md`, `implementation-plan/20260505-205639/stage-status.md`, `implementation-plan/20260505-205639/stage-reports/STAGE-005-20260505-223234.md`
- Verification: Docker Compose default/profile config, `.venv/bin/mkdocs build --strict`, docs sync, Dockerfile check, static ops review, diff hygiene, explorer review, docker-expert review, and reviewer review passed.
- Report: `stage-reports/STAGE-005-20260505-223234.md`

## 2026-05-05 23:06:14 MSK — STAGE-006
- Status: CLOSED
- Files changed: `.github/PULL_REQUEST_TEMPLATE.md`, `.github/workflows/ci.yml`, `CLAUDE.md`, `CONTRIBUTING.md`, `README.md`, `docs/ADR/ADR-003-cryptography-optional.md`, `docs/contributing.md`, `docs/index.md`, `mkdocs.yml`, `src/data/static/ui/core.js`, `src/handlers/notepad.py`, `src/request_pipeline.py`, `tests/test_check_stale_docs.py`, `tools/browser_smoke.py`, `tools/browser_smoke.playwright.js`, `tools/check_stale_docs.py`, `implementation-plan/20260505-205639/stages/STAGE-006-dependency-copy-drift.md`, `implementation-plan/20260505-205639/stage-status.md`, `implementation-plan/20260505-205639/stage-reports/STAGE-006-20260505-224442.md`
- Verification: stale-reference checker, targeted stale-check tests, docs sync, MkDocs strict build, ruff, JS syntax check, full browser smoke, explorer review, correctness review, and docs/copy re-review passed.
- Report: `stage-reports/STAGE-006-20260505-224442.md`

## 2026-05-05 23:29:51 MSK — STAGE-007
- Status: CLOSED
- Files changed: `.pre-commit-config.yaml`, `.github/workflows/ci.yml`, `.github/workflows/security.yml`, `tools/check_dependency_constraints.py`, `CONTRIBUTING.md`, `docs/contributing.md`, `implementation-plan/20260505-205639/stages/STAGE-007-precommit-dependency-completeness.md`, `implementation-plan/20260505-205639/stage-status.md`, `implementation-plan/20260505-205639/stage-reports/STAGE-007-20260505-231228.md`
- Verification: refreshed pre-commit mypy hook, installed dependency smoke, constraints-vs-installed checker, strict pinned `pip-audit`, clean constrained install smoke, clean security-job simulation, YAML/docs/stale-doc checks, ruff, diff hygiene, dependency-manager review, reviewer rework, and QA review passed.
- Report: `stage-reports/STAGE-007-20260505-231228.md`

## 2026-05-05 23:44:54 MSK — STAGE-008
- Status: CLOSED
- Files changed: `.github/workflows/ci.yml`, `implementation-plan/20260505-205639/stages/STAGE-008-docker-tls-runtime-smoke.md`, `implementation-plan/20260505-205639/stage-status.md`, `implementation-plan/20260505-205639/change-log.md`, `implementation-plan/20260505-205639/stage-reports/STAGE-008-20260505-233412.md`
- Verification: workflow Docker smoke syntax, whitespace diff check, full built-image Docker smoke with runtime imports plus HTTP and self-signed TLS PING, cleanup check, explorer review, reviewer review, and docker-expert re-review passed.
- Report: `stage-reports/STAGE-008-20260505-233412.md`

## 2026-05-06 00:24:27 MSK — STAGE-009
- Status: CLOSED
- Files changed: `src/data/static/ui/notepad.js`, `src/data/static/ui/core.js`, `src/data/index.html`, `src/data/static/ui/features.css`, `tools/browser_smoke.playwright.js`, `tests/test_ui_inspector_redaction.py`, `implementation-plan/20260505-205639/stages/STAGE-009-notepad-title-dirty-guard.md`, `implementation-plan/20260505-205639/stage-status.md`, `implementation-plan/20260505-205639/stage-reports/STAGE-009-20260505-234732.md`
- Verification: JS syntax, diff whitespace, targeted Notepad/redaction tests, full pytest suite, focused Notepad browser probe, full browser smoke with dirty-transition and stale-load coverage, scoped ruff, explorer review, QA review, frontend review, and correctness review passed.
- Report: `stage-reports/STAGE-009-20260505-234732.md`

## 2026-05-21 20:14:58 MSK — STAGE-010
- Status: CLOSED
- Files changed: `src/data/static/ui/notepad.js`, `src/handlers/notepad.py`, `src/notepad_service.py`, `tests/test_handlers/test_notepad.py`, `tests/test_websocket_handlers.py`, `tools/browser_smoke.playwright.js`, `API.md`, `docs/api.md`, `implementation-plan/20260505-205639/stages/STAGE-010-notepad-ws-idempotent-save.md`, `implementation-plan/20260505-205639/stage-status.md`, `implementation-plan/20260505-205639/stage-reports/STAGE-010-20260521-200343.md`
- Verification: targeted WebSocket/NOTE tests, browser smoke with dropped first-save ack retry, docs sync, ruff, Python compile, JS syntax, diff whitespace, and explorer review passed.
- Report: `stage-reports/STAGE-010-20260521-200343.md`

## 2026-05-21 20:24:32 MSK — STAGE-011
- Status: CLOSED
- Files changed: `src/handlers/advanced_upload.py`, `tests/test_handlers/test_handler_integration.py`, `API.md`, `docs/api.md`, `implementation-plan/20260505-205639/stages/STAGE-011-advanced-upload-json-guardrails.md`, `implementation-plan/20260505-205639/stage-status.md`, `implementation-plan/20260505-205639/stage-reports/STAGE-011-20260521-201720.md`
- Verification: focused advanced-upload limit tests, handler/server regression suite, docs sync, Python compile, ruff, HMAC/decrypt static order check, diff whitespace check, and explorer review passed.
- Report: `stage-reports/STAGE-011-20260521-201720.md`

## 2026-05-21 20:39:40 MSK — STAGE-012
- Status: CLOSED
- Files changed: `src/http/utils.py`, `src/http/__init__.py`, `src/handlers/files.py`, `src/handlers/advanced_upload.py`, `src/notepad_service.py`, `tests/test_handlers/test_files.py`, `tests/test_handlers/test_notepad.py`, `implementation-plan/20260505-205639/stages/STAGE-012-atomic-user-data-writes.md`, `implementation-plan/20260505-205639/stage-status.md`, `implementation-plan/20260505-205639/stage-reports/STAGE-012-20260521-202814.md`
- Verification: concurrent upload regressions, Notepad failure-injection regressions, required upload/live and Notepad/WebSocket suites, ruff, compileall, focused mypy, static same-directory temp review, and explorer review passed.
- Report: `stage-reports/STAGE-012-20260521-202814.md`

## 2026-05-21 20:52:31 MSK — STAGE-013
- Status: CLOSED
- Files changed: `.github/workflows/ci.yml`, `.gitignore`, `tests/conftest.py`, `tools/check_pytest_collection_policy.py`, `tests/test_pytest_collection_policy.py`, `implementation-plan/20260505-205639/stages/STAGE-013-ci-local-collection-drift.md`, `implementation-plan/20260505-205639/stage-status.md`, `implementation-plan/20260505-205639/change-log.md`, `implementation-plan/20260505-205639/stage-reports/STAGE-013-20260521-204722.md`
- Verification: collect-only in project `.venv`, ignored-test absence check, ignored pytest file inventory, policy helper, guard tests, `tests/test_cli.py`, ruff, diff whitespace, Context7 pytest docs check, and explorer review passed.
- Report: `stage-reports/STAGE-013-20260521-204722.md`
