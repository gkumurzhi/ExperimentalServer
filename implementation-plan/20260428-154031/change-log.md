# Change Log

## 2026-04-28 16:10:40 MSK — STAGE-001
- Status: CLOSED
- Files changed: `src/handlers/base.py`, `tests/test_handlers/test_path_traversal.py`, `tests/test_server_routing.py`, `implementation-plan/20260428-154031/stages/STAGE-001-static-resource-containment.md`, `implementation-plan/20260428-154031/stage-status.md`, `implementation-plan/20260428-154031/stage-reports/STAGE-001-20260428-155734.md`
- Verification: `uv run --extra dev pytest tests/test_handlers/test_path_traversal.py tests/test_http/test_path_traversal_prefix.py tests/test_server_routing.py -q` (`52 passed`); `uv run python -m compileall src tests`; `uv run --extra lint ruff check src/handlers/base.py tests/test_handlers/test_path_traversal.py tests/test_server_routing.py`; security, Python, and final verifier subagents passed after fixing an intermediate `importlib.resources.as_file()` lifetime finding.
- Report: `stage-reports/STAGE-001-20260428-155734.md`

## 2026-04-28 18:32:48 MSK — STAGE-002
- Status: CLOSED
- Files changed: `src/server.py`, `tests/test_server_methods.py`, `tests/test_server_live.py`, `implementation-plan/20260428-154031/stages/STAGE-002-streamed-gzip-memory-safety.md`, `implementation-plan/20260428-154031/stage-status.md`, `implementation-plan/20260428-154031/stage-reports/STAGE-002-20260428-182050.md`
- Verification: `uv run --extra dev pytest tests/test_server_methods.py tests/test_server_live.py -q` (`41 passed`); targeted gzip/live tests passed; `uv run --extra dev python -m compileall src tests`; `uv run --extra lint ruff check src/server.py tests/test_server_methods.py tests/test_server_live.py`; static search found no `read_bytes()` in the response gzip implementation; performance, QA, and final verifier subagents passed.
- Report: `stage-reports/STAGE-002-20260428-182050.md`

## 2026-04-28 20:46:27 MSK — STAGE-003
- Status: CLOSED
- Files changed: `src/handlers/smuggle.py`, `src/handlers/files.py`, `src/http/response.py`, `src/server.py`, `tests/test_server_methods.py`, `implementation-plan/20260428-154031/stages/STAGE-003-smuggle-memory-ceiling.md`, `implementation-plan/20260428-154031/stage-status.md`, `implementation-plan/20260428-154031/stage-reports/STAGE-003-20260428-203152.md`
- Verification: `uv run pytest tests/test_server_methods.py -q -k smuggle` (`8 passed`); `uv run pytest tests/test_server_methods.py -q` (`42 passed`); `uv run pytest tests/test_server_routing.py::TestSmuggleHandler -q` (`3 passed`); `uv run pytest tests/test_http/test_response.py -q` (`16 passed`); `python -m compileall src tests`; `uv run ruff check src/handlers/smuggle.py src/handlers/files.py src/http/response.py src/server.py tests/test_server_methods.py`; `git diff --check` scoped files; explorer, performance, and final reviewer subagents passed after fixing an intermediate HEAD cleanup finding.
- Report: `stage-reports/STAGE-003-20260428-203152.md`

## 2026-04-28 21:08:00 MSK — STAGE-004
- Status: CLOSED
- Files changed: `src/websocket.py`, `src/server.py`, `tests/test_websocket.py`, `tests/test_websocket_handlers.py`, `implementation-plan/20260428-154031/stages/STAGE-004-websocket-client-mask-enforcement.md`, `implementation-plan/20260428-154031/stage-status.md`, `implementation-plan/20260428-154031/stage-reports/STAGE-004-20260428-205905.md`
- Verification: `.venv/bin/pytest tests/test_websocket.py tests/test_websocket_handlers.py tests/test_security/test_websocket_frame_limit.py -q` (`64 passed`); `python -m compileall src tests`; `.venv/bin/ruff check src/websocket.py src/server.py tests/test_websocket.py tests/test_websocket_handlers.py tests/test_security/test_websocket_frame_limit.py`; `.venv/bin/pytest tests/test_server_methods.py -q -k handle_notepad_ws` (`3 passed`); `.venv/bin/pytest tests/test_server_live.py -q -k websocket` (`1 passed`); `.venv/bin/pytest tests/test_property/test_ws_frame_parser.py -q` (`3 passed`); websocket-engineer and QA verifier subagents passed. Global `pytest` remained unavailable in the host Python and was treated as an environment issue because the project `.venv` checks passed.
- Report: `stage-reports/STAGE-004-20260428-205905.md`

## 2026-04-28 21:26:57 MSK — STAGE-005
- Status: CLOSED
- Files changed: `tests/test_server_routing.py`, `tools/browser_smoke.playwright.js`, `implementation-plan/20260428-154031/stages/STAGE-005-inspector-asset-packaging.md`, `implementation-plan/20260428-154031/stage-status.md`, `implementation-plan/20260428-154031/stage-reports/STAGE-005-20260428-211543.md`
- Verification: `.venv/bin/python -m pytest tests/test_server_routing.py -q -k "static_asset or script_references"` (`5 passed, 18 deselected`); `.venv/bin/python -m pytest tests/test_server_routing.py tests/test_server_methods.py -q` (`65 passed`); `.venv/bin/python -m compileall src tests`; `.venv/bin/ruff check tests/test_server_routing.py`; `node --check tools/browser_smoke.playwright.js`; `.venv/bin/python tools/browser_smoke.py`; temporary wheel asset inspection; explorer, Python, and UI verifier subagents passed. Global `pytest` remained unavailable in host Python and was treated as an environment issue because project `.venv` checks passed.
- Report: `stage-reports/STAGE-005-20260428-211543.md`

## 2026-04-28 21:46:30 MSK — STAGE-006
- Status: CLOSED
- Files changed: `src/data/static/ui/inspector.js`, `tests/test_ui_inspector_redaction.py`, `implementation-plan/20260428-154031/stages/STAGE-006-inspector-redaction.md`, `implementation-plan/20260428-154031/stage-status.md`, `implementation-plan/20260428-154031/change-log.md`, `implementation-plan/20260428-154031/stage-reports/STAGE-006-20260428-213004.md`
- Verification: `.venv/bin/pytest tests/test_ui_inspector_redaction.py -q` (`2 passed`); `.venv/bin/pytest tests -q -k "browser_smoke or ui or inspector"` (`28 passed, 521 deselected`); `python -m compileall src tests`; `.venv/bin/ruff check tests/test_ui_inspector_redaction.py`; UI `node --check` commands; `.venv/bin/python tools/browser_smoke.py`; static raw/copy path review; explorer, test, and security verifier subagents passed. Global host `pytest` remained unavailable and was treated as an environment issue because project `.venv` checks passed.
- Report: `stage-reports/STAGE-006-20260428-213004.md`

## 2026-04-28 22:40:57 MSK — STAGE-007
- Status: CLOSED
- Files changed: `.dockerignore`, `implementation-plan/20260428-154031/stages/STAGE-007-docker-context-hygiene.md`, `implementation-plan/20260428-154031/stage-status.md`, `implementation-plan/20260428-154031/change-log.md`, `implementation-plan/20260428-154031/stage-reports/STAGE-007-20260428-223152.md`
- Verification: `docker buildx build --help >/dev/null`; `docker version --format '{{.Server.Version}}'`; `docker build --no-cache --target runtime .`; disposable Docker context checks for dummy runtime/secret paths including `notes/`, `.env*`, nested certs, credential JSON, `secret/`, and `examples/docker/data`; `git diff --check`; Docker verifier passed; security verifier findings were fixed and rechecked.
- Report: `stage-reports/STAGE-007-20260428-223152.md`

## 2026-04-28 23:07:45 MSK — STAGE-008
- Status: CLOSED
- Files changed: `.github/workflows/security.yml`, `implementation-plan/20260428-154031/stages/STAGE-008-pip-audit-workflow.md`, `implementation-plan/20260428-154031/stage-status.md`, `implementation-plan/20260428-154031/change-log.md`, `implementation-plan/20260428-154031/stage-reports/STAGE-008-20260428-225430.md`
- Verification: `python -m pip_audit --help` in a disposable constrained venv; `python -m pip_audit --strict -r constraints/ci.txt` reached real vulnerability findings in existing pins; `python -m compileall src tests`; workflow YAML parse; scoped `git diff --check`; static workflow review; verifier subagents passed or were superseded by the final constraints-input mode.
- Report: `stage-reports/STAGE-008-20260428-225430.md`

## 2026-04-28 23:42:50 MSK — STAGE-009
- Status: CLOSED
- Files changed: `API.md`, `docs/api.md`, `README.md`, `implementation-plan/20260428-154031/stages/STAGE-009-api-smuggle-contract-docs.md`, `implementation-plan/20260428-154031/stage-status.md`, `implementation-plan/20260428-154031/change-log.md`, `implementation-plan/20260428-154031/stage-reports/STAGE-009-20260428-233531.md`
- Verification: `python3 tools/sync_docs.py --check`; `git diff --check -- API.md docs/api.md README.md implementation-plan/20260428-154031/stage-reports/STAGE-009-20260428-233531.md`; `uv run pytest tests/test_server_methods.py -q -k smuggle` (`8 passed`); static contract review against `src/handlers/smuggle.py` and temp-file serving paths; API and documentation verifier subagents passed.
- Report: `stage-reports/STAGE-009-20260428-233531.md`

## 2026-04-29 16:42:43 MSK — STAGE-010
- Status: CLOSED
- Files changed: `API.md`, `docs/api.md`, `implementation-plan/20260428-154031/backlog.md`, `implementation-plan/20260428-154031/stages/STAGE-010-api-error-contract-docs.md`, `implementation-plan/20260428-154031/stage-status.md`, `implementation-plan/20260428-154031/change-log.md`, `implementation-plan/20260428-154031/stage-reports/STAGE-010-20260429-162933.md`
- Verification: `python3 tools/sync_docs.py --check`; scoped `git diff --check`; `diff -u API.md <(tail -n +3 docs/api.md)`; static source-to-doc review across handler and request-pipeline error paths; api-documenter, reviewer, and qa-expert verifier subagents passed after fixing an intermediate request-framing wording gap.
- Report: `stage-reports/STAGE-010-20260429-162933.md`

## 2026-04-29 16:59:26 MSK — STAGE-011
- Status: CLOSED
- Files changed: `CLAUDE.md`, `implementation-plan/20260428-154031/stages/STAGE-011-claude-stale-guidance.md`, `implementation-plan/20260428-154031/stage-status.md`, `implementation-plan/20260428-154031/change-log.md`, `implementation-plan/20260428-154031/stage-reports/STAGE-011-20260429-164957.md`
- Verification: `.venv/bin/pytest tests/test_cli.py -q` (`31 passed`); `PATH=.venv/bin:$PATH pytest tests/test_cli.py -q` (`31 passed`); `git diff --check CLAUDE.md`; stale-guidance grep for removed flags, OPSEC wording, sandbox wording, and unsafe `startswith` path advice; canonical-doc anchor grep; documentation-engineer and security-auditor verifier subagents passed. Host `pytest tests/test_cli.py -q` failed before running tests because global Python lacks `pytest`, treated as an environment issue because the project `.venv` checks passed.
- Report: `stage-reports/STAGE-011-20260429-164957.md`

## 2026-04-29 17:35:16 MSK — STAGE-012
- Status: CLOSED
- Files changed: `src/http/request.py`, `src/request_pipeline.py`, `src/handlers/__init__.py`, `tests/test_http/test_request.py`, `tests/test_request_pipeline.py`, `tests/test_handlers/test_handler_integration.py`, `implementation-plan/20260428-154031/stages/STAGE-012-malformed-request-rejection.md`, `implementation-plan/20260428-154031/stage-status.md`, `implementation-plan/20260428-154031/change-log.md`, `implementation-plan/20260428-154031/stage-reports/STAGE-012-20260429-171354.md`
- Verification: `.venv/bin/python -m pytest tests/test_http tests/test_handlers/test_handler_integration.py tests/test_request_pipeline.py -q` (`147 passed`); `.venv/bin/python -m pytest tests/test_property/test_request_parser.py -q` (`2 passed`); `python -m compileall src tests`; scoped `ruff check`; `git diff --check`; explorer, QA, security, and repeat correctness verifier subagents passed after fixing an intermediate request-target whitespace bypass. Host/global `pytest` failed before running tests because global Python lacks `pytest`, treated as an environment issue because project `.venv` checks passed.
- Report: `stage-reports/STAGE-012-20260429-171354.md`

## 2026-04-29 19:15:28 MSK — STAGE-013
- Status: CLOSED
- Files changed: `src/handlers/advanced_upload.py`, `src/security/crypto.py`, `tests/test_handlers/test_handler_integration.py`, `tests/test_security/test_crypto.py`, `implementation-plan/20260428-154031/stages/STAGE-013-advanced-upload-fail-closed.md`, `implementation-plan/20260428-154031/stage-status.md`, `implementation-plan/20260428-154031/change-log.md`, `implementation-plan/20260428-154031/stage-reports/STAGE-013-20260429-185539.md`
- Verification: `.venv/bin/python -m pytest tests/test_handlers/test_handler_integration.py tests/test_security/test_crypto.py -q` (`109 passed`); `.venv/bin/python -m compileall src tests`; scoped `ruff check`; `git diff --check`; static decrypt call-site review; explorer, security, and QA verifier subagents passed. Host/global `pytest` failed before running tests because global Python lacks `pytest`, treated as an environment issue because project `.venv` checks passed.
- Report: `stage-reports/STAGE-013-20260429-185539.md`

## 2026-04-29 19:58:30 MSK — STAGE-014
- Status: CLOSED
- Files changed: `src/config.py`, `src/handlers/files.py`, `src/handlers/info.py`, `src/handlers/smuggle.py`, `tests/test_handlers/test_handler_integration.py`, `implementation-plan/20260428-154031/stages/STAGE-014-hidden-upload-policy.md`, `implementation-plan/20260428-154031/stage-status.md`, `implementation-plan/20260428-154031/change-log.md`, `implementation-plan/20260428-154031/stage-reports/STAGE-014-20260429-194717.md`
- Verification: `.venv/bin/python -m pytest tests/test_server_methods.py tests/test_handlers -q -k "hidden or smuggle or fetch or delete"` (`40 passed, 176 deselected`); `.venv/bin/python -m compileall src tests`; scoped `ruff check`; `git diff --check`; `.venv/bin/python -m pytest tests/test_handlers/test_handler_integration.py tests/test_server_methods.py -q` (`132 passed`); explorer, QA, security, and final reviewer subagents passed. Host/global `pytest` failed before running tests because global Python lacks `pytest`, treated as an environment issue because project `.venv` checks passed.
- Report: `stage-reports/STAGE-014-20260429-194717.md`

## 2026-04-29 20:54:06 MSK — STAGE-015
- Status: CLOSED
- Files changed: `src/http/cors.py`, `src/http/response.py`, `src/server.py`, `src/request_pipeline.py`, `src/handlers/files.py`, `tests/test_http/test_response.py`, `tests/test_server_methods.py`, `tests/test_request_pipeline.py`, `implementation-plan/20260428-154031/stages/STAGE-015-cors-contract.md`, `implementation-plan/20260428-154031/stage-status.md`, `implementation-plan/20260428-154031/change-log.md`, `implementation-plan/20260428-154031/stage-reports/STAGE-015-20260429-203343.md`
- Verification: `.venv/bin/python -m pytest tests/test_server_methods.py tests/test_http/test_response.py -q -k "cors or options"` (`15 passed, 56 deselected`); `.venv/bin/python -m pytest tests/test_server_methods.py tests/test_http/test_response.py tests/test_request_pipeline.py tests/test_handlers/test_handler_integration.py -q` (`173 passed`); `.venv/bin/python -m compileall src tests`; scoped `ruff check`; `git diff --check`; security, API/header, and correctness verifier subagents passed after fixing mixed wildcard and missing preflight/exposed header findings. Host/global `pytest` failed before running tests because global Python lacks `pytest`, treated as an environment issue because project `.venv` checks passed.
- Report: `stage-reports/STAGE-015-20260429-203343.md`

## 2026-04-30 12:48:36 MSK — STAGE-016
- Status: CLOSED
- Files changed: `src/websocket.py`, `src/server.py`, `tests/test_websocket.py`, `tests/test_websocket_handlers.py`, `tests/test_security/test_websocket_upgrade.py`, `tests/test_server_methods.py`, `tests/test_property/test_ws_frame_parser.py`, `implementation-plan/20260428-154031/stages/STAGE-016-websocket-frame-validation.md`, `implementation-plan/20260428-154031/stage-status.md`, `implementation-plan/20260428-154031/change-log.md`, `implementation-plan/20260428-154031/stage-reports/STAGE-016-20260430-122243.md`
- Verification: `.venv/bin/python -m pytest tests/test_websocket.py tests/test_websocket_handlers.py tests/test_security/test_websocket_upgrade.py tests/test_security/test_websocket_frame_limit.py -q` (`79 passed`); `.venv/bin/python -m pytest tests/test_websocket.py tests/test_websocket_handlers.py tests/test_security/test_websocket_upgrade.py tests/test_security/test_websocket_frame_limit.py tests/test_server_methods.py tests/test_property/test_ws_frame_parser.py -q` (`133 passed`); `.venv/bin/python -m pytest tests/test_server_methods.py tests/test_property/test_ws_frame_parser.py tests/test_request_pipeline.py -q -k "websocket or notepad_ws or ws_frame_parser"` (`18 passed, 48 deselected`); `.venv/bin/python -m compileall src tests`; scoped `ruff check`; `git diff --check`; full suite `.venv/bin/python -m pytest -q` (`600 passed`); websocket-engineer and QA verifier subagents passed after fixing an intermediate handshake-test isolation gap. Host/global `pytest` failed before running tests because global Python lacks `pytest`, treated as an environment issue because project `.venv` checks passed.
- Report: `stage-reports/STAGE-016-20260430-122243.md`

## 2026-04-30 13:25:36 MSK — STAGE-017
- Status: CLOSED
- Files changed: `src/server.py`, `src/request_pipeline.py`, `src/websocket.py`, `src/metrics.py`, `tests/test_server_live.py`, `tests/test_server_methods.py`, `tests/test_request_pipeline.py`, `tests/test_websocket.py`, `tests/test_websocket_handlers.py`, `tests/test_metrics.py`, `implementation-plan/20260428-154031/stages/STAGE-017-websocket-resource-limits.md`, `implementation-plan/20260428-154031/stage-status.md`, `implementation-plan/20260428-154031/change-log.md`, `implementation-plan/20260428-154031/stage-reports/STAGE-017-20260430-125548.md`
- Verification: `.venv/bin/pytest tests/test_websocket.py tests/test_server_live.py tests/test_security/test_websocket_frame_limit.py -q` (`60 passed`); `.venv/bin/pytest tests/test_server_methods.py tests/test_request_pipeline.py tests/test_websocket.py tests/test_server_live.py tests/test_security/test_websocket_frame_limit.py tests/test_websocket_handlers.py tests/test_metrics.py -q` (`160 passed`); `.venv/bin/python -m compileall src tests`; scoped `ruff check`; `.venv/bin/mypy src`; `git diff --check`; full suite `timeout 120 .venv/bin/pytest -q` (`607 passed`); explorer and reviewer verifier subagents passed after fixing the single-worker residual budget risk.
- Report: `stage-reports/STAGE-017-20260430-125548.md`

## 2026-04-30 15:48:17 MSK — STAGE-018
- Status: CLOSED
- Files changed: `src/metrics.py`, `src/request_pipeline.py`, `tests/test_metrics.py`, `tests/test_request_pipeline.py`, `tests/test_handlers/test_handler_integration.py`, `tests/test_server_methods.py`, `tests/test_server_routing.py`, `tests/test_websocket_handlers.py`, `API.md`, `docs/api.md`, `implementation-plan/20260428-154031/stages/STAGE-018-metrics-observability-contract.md`, `implementation-plan/20260428-154031/stage-status.md`, `implementation-plan/20260428-154031/change-log.md`, `implementation-plan/20260428-154031/stage-reports/STAGE-018-20260430-153607.md`
- Verification: `.venv/bin/python -m pytest tests/test_request_pipeline.py tests/test_server_methods.py -q -k "metrics or error"` (`6 passed, 61 deselected`); `.venv/bin/python -m pytest tests/test_metrics.py tests/test_handlers/test_handler_integration.py -q -k "metrics"` (`14 passed, 88 deselected`); `.venv/bin/python -m pytest tests/test_request_pipeline.py tests/test_server_methods.py tests/test_server_routing.py tests/test_websocket_handlers.py -q -k "metrics or error"` (`16 passed, 97 deselected`); `.venv/bin/python -m compileall src tests`; scoped `ruff check`; `.venv/bin/python tools/sync_docs.py --check`; `git diff --check`; full suite `.venv/bin/python -m pytest tests -q` (`629 passed`); static metric call-site review; python-pro and performance-engineer verifier subagents passed. Host/global `pytest` failed before running tests because global Python lacks `pytest`, treated as an environment issue because project `.venv` checks passed.
- Report: `stage-reports/STAGE-018-20260430-153607.md`
