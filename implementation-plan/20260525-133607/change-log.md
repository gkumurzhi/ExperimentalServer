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
