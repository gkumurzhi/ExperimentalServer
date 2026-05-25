# python-pro Report
_Generated: 2026-05-25 12:42:22 MSK_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260525-121051/analysis-plan.md_

## Summary

The `python-pro` subagent was started read-only, but its sandbox could not read the repo due a local `bwrap` failure. I completed the same read-only Python/package audit in the parent session.

Execution boundary analyzed: `exphttp` console script in `pyproject.toml` -> `src.cli:main` -> `ExperimentalHTTPServer` -> `receive_request` -> `RequestPipeline` -> handler mixins. Persistent state is under `<root>/uploads`, `<root>/notes`, and ACME state under `~/.exphttp/acme`.

Validated directly:
- `53` focused pytest tests passed with cache disabled: import boundaries, request pipeline failures, receive-layer framing, concurrent upload naming, and notepad rollback failures.
- Import probe succeeded for `src`, `src.http`, `src.security`, `src.server`, `src.cli`.
- Setuptools discovery probe showed namespace discovery would include `src.data.static` and `src.data.static.ui`.

Could not validate mypy: local `mypy` script exists but `import mypy` fails with `ModuleNotFoundError`.

## Documentation Checks
- **Setuptools** `82.0.1` - Context7 topic checked: `package discovery, src-layout, package-dir, package-data`; impact on recommendation: current config works as a root-layout package named `src`, but is not aligned with true src-layout guidance using `package-dir = {"" = "src"}`, `where = ["src"]`, and `namespaces = false`. Source: https://github.com/pypa/setuptools/blob/main/docs/userguide/package_discovery.rst
- **pytest** `9.0.3` - Context7 topic checked: `testpaths, collect_ignore, cache behavior`; impact on recommendation: `tests/conftest.py` `collect_ignore` is a supported mechanism, and `testpaths = ["tests"]` keeps generated `codex-analysis/` out of normal collection.
- **mypy** `1.20.1` - Context7 topic checked: `strict mode, Protocols, explicit package bases, lazy re-exports`; impact on recommendation: current lazy exports are defensible, but package rename work should preserve typed exports with `py.typed` and checked public import tests.

## Detailed Findings

The main design gap is that the project distribution is `exphttp`, while the import package and public examples are `src`. The runtime itself is reasonably explicit at the request boundary: malformed requests return 400 in `RequestPipeline`, receive-layer framing failures intentionally drop the connection, and notepad save failures have rollback tests. The weaker areas are package identity, accumulated storage limits, final-file write atomicity, and WebSocket unexpected-error observability.

## Issues Found
- [MEDIUM] Distribution publishes a generic `src` package as the public API
  - File/area: `pyproject.toml`, `README.md`, tests/imports
  - Evidence: `pyproject.toml:6` names the project `exphttp`, `pyproject.toml:48` maps `exphttp = "src.cli:main"`, `pyproject.toml:75` reads version from `src.config.__version__`, and `pyproject.toml:77-80` discovers `src*` from `"."`. README examples use `python -m src` and `from src import ...`.
  - Detail: This is not a conventional src layout; it makes `src` the installed package. With default namespace discovery, Setuptools also sees `src.data.static` and `src.data.static.ui` as namespace packages unless disabled.
  - Impact: Downstream imports are fragile and confusing, and a later rename to `exphttp` becomes a breaking API migration.
  - Confidence: high

- [HIGH] No aggregate storage quota for repeated uploads or notes
  - File/area: `src/server.py`, `src/handlers/files.py`, `src/handlers/advanced_upload.py`, `src/notepad_service.py`
  - Evidence: `src/server.py:84` sets only per-request upload size. Standard upload writes at `src/handlers/files.py:687-708`; advanced upload writes at `src/handlers/advanced_upload.py:385-405`; notes cap one blob at `src/notepad_service.py:21` but `list_notes()` scans all `*.enc` at `src/notepad_service.py:390-401`.
  - Detail: Each write path enforces per-object limits, but none enforces total bytes, note count, upload count, retention, or free-space backpressure.
  - Impact: A valid client can fill disk through repeated successful writes.
  - Confidence: high

- [MEDIUM] Upload writes are exclusive but not commit-atomic
  - File/area: `src/http/utils.py`, upload handlers
  - Evidence: `write_unique_file_exclusive()` opens the final destination with `"xb"` and writes directly at `src/http/utils.py:667-670`; cleanup only runs after exceptions at `src/http/utils.py:673-676`.
  - Detail: This prevents same-name clobbering, and tests cover races, but the final path exists while bytes are being written. A crash or concurrent GET/FETCH/INFO can observe a partial file.
  - Impact: Partial files can become externally visible or survive process death.
  - Confidence: high

- [MEDIUM] WebSocket unexpected failures close as normal
  - File/area: `src/server.py`, `src/handlers/notepad.py`
  - Evidence: unexpected WebSocket exceptions are logged only at debug level in `src/server.py:1007-1009`, then `finally` calls `send_close()` with default code `1000` at `src/server.py:1010-1011`. WS list calls the service directly at `src/handlers/notepad.py:291-294`; `_ws_run_note_operation()` catches only `NotepadServiceError` at `src/handlers/notepad.py:321-324`.
  - Detail: HTTP request exceptions become logged 500s in `RequestPipeline`, but WebSocket internal failures can look like clean closes to clients.
  - Impact: Clients cannot distinguish server failure from normal close; operators may miss root cause unless debug logs are enabled.
  - Confidence: high

- [LOW] Notepad clear has a less useful partial-failure contract than upload clear
  - File/area: `src/handlers/files.py`, `src/notepad_service.py`
  - Evidence: upload clear returns deleted counts and per-entry errors at `src/handlers/files.py:546-563`; note clear collects errors but raises generic `Failed to clear notes` at `src/notepad_service.py:462-464`.
  - Detail: Both operations are non-atomic, but only uploads expose enough detail to reconcile partial deletion.
  - Impact: Note clients can receive a generic 500 after some notes were already deleted.
  - Confidence: high

## Concrete Recommendations

1. Short term: add `namespaces = false` to `[tool.setuptools.packages.find]` and add a package discovery test asserting static asset directories are not discovered as packages.
2. Plan a package rename from `src` to `exphttp`, with a compatibility shim only if existing users depend on `from src`.
3. Add aggregate storage controls: max total upload bytes, max total note bytes/count, and clear 507/413-style failures before committing writes.
4. Change upload commit flow to hidden temp file plus atomic publish, with stale temp cleanup.
5. Change WebSocket unexpected errors to `logger.exception`, metric increment, and close code `1011` or an explicit JSON error frame before close.

## Quick Wins

- Add `namespaces = false`.
- Add tests for upload write failure leaving no final file.
- Add a WebSocket test for unexpected service failure returning non-1000 close semantics.
- Make notepad clear return partial counts/errors like upload clear.

## Deeper Improvements

- Introduce a shared storage service for uploads and notes with quota accounting and temp-file commit semantics.
- Add public `exphttp` imports and typed export tests before moving docs away from `from src`.
- Define a small error taxonomy for receive/parser/handler/WebSocket boundaries.

## Open Questions

- Must `from src` remain backward compatible after a package rename?
- Is crash durability required, or only no partial state after handled Python exceptions?
- Should aggregate quota be global across `uploads/` and `notes/`, or separately configurable?
