# python-pro Report
_Generated: 2026-04-28 12:35:29 _
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/analysis-plan.md_

## Summary

I attempted to run the `python-pro` subagent, but its shell sandbox failed before file access (`bwrap ... Operation not permitted`). I completed the requested read-only audit directly in this session, without modifying project files and without reading runtime data contents in `uploads/` or `notes/`.

Execution boundary analyzed: `src/cli.py:137` builds config and starts `ExperimentalHTTPServer`; `src/server.py:395` receives per-client data; `src/request_pipeline.py:82` parses/authenticates/dispatches/sends; handlers under `src/handlers/` return `HTTPResponse`; `src/server.py:536` post-processes gzip and request IDs.

## Documentation Checks

- **pytest** `9.0.0/9.0.3` — Context7 topic checked: `pyproject.toml configuration`; impact on recommendation: current `[tool.pytest.ini_options]` usage is valid, but failure-path tests should pin malformed request behavior explicitly.
- **mypy** `1.20.2 lock / >=1.14 config` — Context7 topic checked: `strict mode, Protocols, protocol attributes`; impact on recommendation: mutable protocol attributes and dynamic mixin attributes should reflect runtime truth, not be weakened with `Any` unless intentional.
- **setuptools** `>=75.0 / unknown runtime` — Context7 topic checked: `package-data in pyproject.toml`; impact on recommendation: `[tool.setuptools.package-data]` can include static assets, but untracked files still will not exist in clean CI/release checkouts.

## Detailed Findings

Parser behavior is the weakest contract boundary. `HTTPRequest._parse()` initializes `method` and `path` to empty strings, catches all parse failures, and exposes no parse-validity state. The pipeline then treats the request as dispatchable.

Gzip post-processing is confirmed to convert streamed responses into buffered bodies. A direct in-process check showed `stream_path` changes from set to `None` after gzip, with the full file compressed into `response.body`.

Metrics currently count “errors” only when callers pass `error=True`, not when a handler returns `5xx`.

Package-data patterns cover current `src/data/static/ui/*` files, but `src/data/static/ui/inspector.js` is untracked while `src/data/index.html` references it.

Local validation limits: `pytest`, `mypy`, and `ruff` are not installed in the current interpreter, so I did not run full suites.

## Issues Found

- [MEDIUM] Malformed request lines can reach handler dispatch and advanced-upload writes
  - File/area: `src/http/request.py:14`, `src/http/request.py:55`, `src/handlers/__init__.py:55`, `src/handlers/__init__.py:61`
  - Evidence: invalid request lines leave `method == ""` and `path == ""`; with `advanced_upload=True`, a malformed request with a body is accepted by `handle_advanced_upload`.
  - Detail: the parser swallows malformed input instead of returning a bad-request signal. Dispatch sees an unknown empty method, and advanced-upload routing treats any body as a valid advanced upload payload.
  - Impact: malformed HTTP can produce `200` and write into `uploads/` when advanced upload is enabled, instead of returning `400 Bad Request`.
  - Confidence: high

- [HIGH] Gzip reads streamed files fully into memory
  - File/area: `src/server.py:262`
  - Evidence: `_maybe_gzip_response()` calls `response.stream_path.read_bytes()`, then sets `response.body` and clears `stream_path`.
  - Detail: this defeats streaming for compressible file responses.
  - Impact: large text/JSON/HTML uploads can cause memory and CPU pressure on `GET`/`FETCH` with `Accept-Encoding: gzip`.
  - Confidence: high

- [MEDIUM] WebSocket parser accepts unmasked client frames
  - File/area: `src/websocket.py:91`, `src/websocket.py:127`, `src/server.py:659`
  - Evidence: `parse_ws_frame()` decodes unmasked frames by assigning `payload = raw_payload`; `_handle_notepad_ws()` uses this parser for client frames.
  - Detail: RFC client-to-server frames must be masked. Tests also encode this permissive behavior via server-frame roundtrips in `tests/test_websocket.py`.
  - Impact: non-browser clients can send protocol-invalid frames that the server accepts.
  - Confidence: high

- [MEDIUM] `/metrics` under-reports handler-produced 5xx responses
  - File/area: `src/metrics.py:25`, `src/request_pipeline.py:121`, `src/handlers/files.py:415`, `src/handlers/advanced_upload.py:268`
  - Evidence: `MetricsCollector.record()` increments `total_errors` only for `error=True`; normal handler responses are recorded without that flag.
  - Detail: only pipeline exceptions count as errors. Handler-returned `500` responses increment `status_counts[500]` but not `total_errors`.
  - Impact: operational dashboards can report zero errors while clients receive 5xx responses.
  - Confidence: high

- [MEDIUM] Referenced UI runtime asset is untracked
  - File/area: `src/data/index.html:494`, `src/data/static/ui/inspector.js`, `pyproject.toml:79`
  - Evidence: `index.html` loads `/static/ui/inspector.js`; `git status` shows `?? src/data/static/ui/inspector.js`.
  - Detail: package-data globs would include the file if present, but clean checkouts and releases will not contain untracked files.
  - Impact: committed HTML can ship with a missing script, breaking the bundled UI inspector.
  - Confidence: high

- [LOW] Worker-level exceptions can disappear without logs or metrics
  - File/area: `src/server.py:395`, `src/server.py:427`
  - Evidence: `_handle_client()` wraps the full client loop in `except Exception: pass`.
  - Detail: pipeline exceptions are logged, but failures before/around `_process_request()` are silently dropped.
  - Impact: socket/read-loop bugs and unexpected operational failures are hard to diagnose.
  - Confidence: medium

- [LOW] Dependency truth sources are drifting
  - File/area: `uv.lock`, `constraints/ci.txt`, `.pre-commit-config.yaml`
  - Evidence: `uv.lock` is untracked; it pins e.g. `pytest 9.0.3`, `mypy 1.20.2`, `ruff 0.15.12`, while `constraints/ci.txt` pins `pytest 9.0.2`, `mypy 1.20.1`, `ruff 0.15.5`; pre-commit pins `ruff v0.9.0`, `mypy v1.14.0`.
  - Detail: CI/Docker use `constraints/ci.txt`, not `uv.lock`.
  - Impact: local checks can diverge from CI if developers use uv or pre-commit as authoritative.
  - Confidence: high

## Concrete Recommendations

Add an explicit parser contract: `HTTPRequest` should either raise a controlled parse exception or expose `parse_error` / `is_valid`. `RequestPipeline.process()` should return `400` before auth/dispatch when method, path, or HTTP version is invalid.

Keep streamed responses streamed when gzip is requested. Either skip gzip for `stream_path` responses or implement chunked/on-the-fly gzip with bounded memory.

Split WebSocket parsing by direction: keep unmasked parsing only for server-frame tests/helpers, and require masking for client frames used by `_handle_notepad_ws()`.

Define the metrics contract. If `total_errors` means client-visible errors, derive it from `status_code >= 500`; if it means unhandled exceptions only, rename it.

Track `src/data/static/ui/inspector.js` or remove its script tag before release. Add a packaging/static-assets test that checks every local `script`/`link` in `index.html` resolves through `get_package_resource()`.

## Quick Wins

- Add tests for malformed request line -> `400`, including `advanced_upload=True`.
- Change `_handle_client()` to `logger.exception(...)` before closing.
- Add an unmasked client WebSocket frame test expecting close code `1002`.
- Decide whether to commit or delete `uv.lock`.

## Deeper Improvements

- Move request parsing from “best effort object with empty fields” to a typed parse result.
- Add artifact validation for wheel/sdist package data.
- Align `constraints/ci.txt`, pre-commit revisions, and any lockfile policy.

## Open Questions

- Is advanced upload intentionally allowed for any unknown syntactically valid method only, or for malformed request lines too?
- Should `total_errors` represent only internal exceptions or every 5xx response?
- Is `uv.lock` intended to become a supported workflow artifact?
