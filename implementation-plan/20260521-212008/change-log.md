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
