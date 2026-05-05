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
