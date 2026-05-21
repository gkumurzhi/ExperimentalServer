# Change Log

## 2026-05-21T22:35:20+03:00 - STAGE-001
- Status: CLOSED
- Files changed: `src/__init__.py`, `src/security/__init__.py`, `src/security/tls.py`, `pyproject.toml`, `tests/test_import_boundaries.py`, active plan status/report artifacts.
- Verification: import boundary probes passed; `pytest -q tests/test_import_boundaries.py tests/test_http/test_io.py tests/test_http/test_request.py` passed; HTTP parser collect-only passed; ruff and py_compile passed; targeted dependency declaration/pin audit passed; verifier subagent found no blockers.
- Report: `stage-reports/STAGE-001-20260521-222446.md`

## 2026-05-21T22:52:57+03:00 - STAGE-002
- Status: CLOSED
- Files changed: `src/http/io.py`, `src/server.py`, `src/metrics.py`, `src/cli.py`, `tests/test_http/test_io.py`, `tests/test_metrics.py`, `tests/test_server_methods.py`, `tests/test_cli.py`, `README.md`, `docs/api.md`, `docs/threat-model.md`, active plan status/report artifacts.
- Verification: parser tests, server helper selector, metrics/CLI/docs/integration tests, reviewer subagent re-check, ruff, compileall, and diff whitespace checks passed. Full suite/typecheck had unrelated local dependency gaps documented in the report.
- Report: `stage-reports/STAGE-002-20260521-223742.md`

## 2026-05-21T23:13:56+03:00 - STAGE-003
- Status: CLOSED
- Files changed: `src/server.py`, `src/metrics.py`, `tests/test_server_methods.py`, `tests/test_server_live.py`, `tests/test_metrics.py`, active plan status/report artifacts.
- Verification: targeted admission/keep-alive/WebSocket tests, metrics tests, broader touched tests, compile check, static submit review, and `git diff --check` passed.
- Report: `stage-reports/STAGE-003-20260521-230426.md`

## 2026-05-21T23:27:27+03:00 - STAGE-004
- Status: CLOSED
- Files changed: `src/notepad_service.py`, `tests/test_handlers/test_notepad.py`, `tests/test_websocket_handlers.py`, `API.md`, `docs/api.md`, active plan status/report artifacts.
- Verification: Notepad HTTP/WS targeted tests, docs sync, compile check, Ruff, and `git diff --check` passed. `mypy` was unavailable in the local environment; `compileall` covered syntax/compiler verification.
- Report: `stage-reports/STAGE-004-20260521-231952.md`

## 2026-05-21T23:41:11+03:00 - STAGE-005
- Status: CLOSED
- Files changed: `src/request_pipeline.py`, `src/server.py`, `tests/test_request_pipeline.py`, `tests/test_server_methods.py`, `README.md`, `API.md`, `docs/api.md`, active plan status/report artifacts.
- Verification: targeted Origin/CORS/mutation tests, broader touched request/server tests, handler smoke, WebSocket origin regression, stale-doc guard, Ruff, compileall, browser smoke with `PYTHONPATH=.`, security-auditor review, and `git diff --check` passed. `mypy` was unavailable in the local environment; `compileall` covered syntax/compiler verification.
- Report: `stage-reports/STAGE-005-20260521-233008.md`
