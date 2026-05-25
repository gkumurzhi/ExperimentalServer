# Change Log

## 2026-05-25 14:09:57 MSK - STAGE-001
- Status: CLOSED
- Files changed: `src/storage.py`, `src/http/utils.py`, `src/handlers/base.py`, `src/handlers/files.py`, `src/handlers/advanced_upload.py`, `src/server.py`, `src/cli.py`, `tests/test_handlers/test_files.py`, `tests/test_cli.py`, `README.md`, `API.md`, `docs/api.md`, `docs/threat-model.md`, plan artifacts.
- Verification: `python -m pytest tests/test_handlers/test_files.py tests/test_server_methods.py tests/test_cli.py` passed with 172 tests; `ruff check src tests`, `ruff format --check src tests`, and `git diff --check` passed. `mypy src` and full `pytest` were blocked by local optional dependency/environment issues unrelated to this stage.
- Report: `stage-reports/STAGE-001-20260525-134934.md`

## 2026-05-25 14:12:26 MSK - STAGE-002
- Status: CLOSED
- Files changed: `src/notepad_service.py`, `src/handlers/notepad.py`, `src/handlers/smuggle.py`, `src/server.py`, `src/cli.py`, `tests/test_handlers/test_notepad.py`, `tests/test_websocket_handlers.py`, `tests/test_server_methods.py`, `tests/test_cli.py`, `README.md`, `API.md`, `docs/api.md`, `docs/threat-model.md`, plan artifacts.
- Verification: required Notepad/WebSocket/server-method tests passed with 177 tests; extended CLI/quota tests passed with 260 tests; `ruff check src tests`, `ruff format --check src tests`, stale-doc guard, API mirror check, docs tests, and `git diff --check` passed. `mypy src` and full `pytest` remain blocked by pre-existing local dependency issues (`mypy` launcher missing module, venv missing `acme`, full suite missing `hypothesis`).
- Report: `stage-reports/STAGE-002-20260525-141226.md`

## 2026-05-25 17:56:04 MSK - STAGE-003
- Status: CLOSED
- Files changed: `src/http/io.py`, `src/server.py`, `src/cli.py`, `tests/test_http/test_io.py`, `tests/test_server_live.py`, `tests/test_server_methods.py`, `tests/test_cli.py`, `README.md`, `API.md`, `SECURITY.md`, plan artifacts.
- Verification: receive/pipeline/live/metrics/CLI/server-method tests passed with 244 tests; stale-doc tests passed with 9 tests; `ruff check src tests`, `ruff format --check src tests`, and `git diff --check` passed. `mypy src` remains blocked by the local optional dependency environment (`mypy` module missing; `uv run --extra lint mypy src` timed out while downloading `mypy`).
- Report: `stage-reports/STAGE-003-20260525-172228.md`

## 2026-05-25 18:14:47 MSK - STAGE-004
- Status: CLOSED
- Files changed: `src/http/io.py`, `src/server.py`, `src/metrics.py`, `src/cli.py`, `tests/test_http/test_io.py`, `tests/test_server_live.py`, `tests/test_metrics.py`, `tests/test_cli.py`, `README.md`, `SECURITY.md`, plan artifacts.
- Verification: targeted receive/live/metrics/CLI tests passed with 163 tests; adjacent server-method/request-pipeline tests passed with 105 tests; combined regression command passed with 269 tests; `ruff check src tests`, `ruff format --check src tests`, and `git diff --check` passed. `mypy src` remains blocked by the local optional dependency environment (`No module named mypy`).
- Report: `stage-reports/STAGE-004-20260525-175855.md`

## 2026-05-25 18:41:08 MSK - STAGE-005
- Status: CLOSED
- Files changed: `src/cli.py`, `src/server.py`, `tests/test_cli.py`, `tests/test_security/test_auth.py`, `README.md`, `SECURITY.md`, `examples/docker/docker-compose.yml`, plan artifacts.
- Verification: targeted CLI/auth/request-pipeline tests passed with 158 tests; `python tools/check_stale_docs.py`, `docker compose -f examples/docker/docker-compose.yml config`, `ruff check src tests`, `ruff format --check src tests`, isolated uv `mypy src`, and `git diff --check` passed. Direct `mypy` was unavailable in the active Python environment, so typecheck used `UV_PROJECT_ENVIRONMENT=/tmp/exphttp-stage005-venv uv run --extra lint mypy src`.
- Report: `stage-reports/STAGE-005-20260525-181754.md`

## 2026-05-25 19:24:21 MSK - STAGE-006
- Status: CLOSED
- Files changed: `src/features.py`, `src/server.py`, `src/cli.py`, `src/handlers/__init__.py`, `src/handlers/base.py`, `src/handlers/files.py`, `src/handlers/info.py`, `src/handlers/notepad.py`, `src/handlers/smuggle.py`, `src/http/cors.py`, `src/http/response.py`, `src/request_pipeline.py`, `src/data/static/ui/core.js`, `src/data/static/ui/upload.js`, `src/data/static/ui/files.js`, `src/data/static/ui/requests.js`, `src/data/static/ui/notepad.js`, `tests/test_server_methods.py`, `tests/test_server_live.py`, `tests/test_cli.py`, `tools/browser_smoke.py`, `README.md`, `API.md`, `SECURITY.md`, plan artifacts.
- Verification: targeted + CLI regression suite passed with 245 tests; `python tools/browser_smoke.py`, `ruff check src tests tools`, focused `ruff format --check` for touched files, `python -m compileall -q src`, and `git diff --check` passed. Full format check still reports an unrelated pre-existing issue in `tools/close_plan_stages.py`; direct `mypy` is unavailable and isolated `uvx` mypy timed out while downloading.
- Report: `stage-reports/STAGE-006-20260525-184508.md`
