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
