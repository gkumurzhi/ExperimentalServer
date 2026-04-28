# architect-reviewer Report
_Generated: 2026-04-28 12:00:00 MSK_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/analysis-plan.md_

## Summary

Scope analyzed: `docs/architecture.md`, all `docs/ADR/*.md`, `CLAUDE.md`, requested runtime modules, relevant handlers, `src/websocket.py`, `.gitignore`, CI/tooling config, and focused tests. I did not read `uploads/` or `notes/` contents.

The mixin-plus-registry design is coherent for this project size, but it is still only a partial disentanglement: routing is now centralized, while handler dependencies remain implicit server attributes. Storage boundaries are mostly clear in code, with two concrete gaps: `notes/` runtime data is not ignored, and package resources are exposed through a `Path` that may expire outside `importlib.resources.as_file()`.

No tests were run to preserve the read-only constraint.

## Documentation Checks

- **Context7 MCP** `unavailable` — Context7 topic checked: `Python`, `WebSocket RFC 6455`, `pre-commit`, `cryptography`; impact on recommendation: all lookups returned monthly quota exhausted, so I used primary-source fallback docs where needed.
- **RFC 6455** `RFC 6455` — Context7 topic checked: `client-to-server masking`; impact: confirms unmasked inbound WebSocket frames should close with protocol error. Source: https://www.rfc-editor.org/rfc/rfc6455.html
- **Python stdlib** `3.10+ target / docs current` — Context7 topic checked: `importlib.resources.as_file`, `ssl.SSLContext`; impact: supports the package-resource finding; TLSManager direction is broadly aligned. Sources: https://docs.python.org/3/library/importlib.resources.html, https://docs.python.org/3/library/ssl.html
- **CORS / ACAO** `unknown` — Context7 topic checked: unavailable; impact: fallback docs confirm `Access-Control-Allow-Origin` must be `*`, `null`, or one origin, not a comma list. Source: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Access-Control-Allow-Origin

## Detailed Findings

ADR-001 accurately describes the deferred state: `HandlerRegistry` is canonical, but `ExperimentalHTTPServer` still inherits `HandlerMixin`. The main maintainability risk is not the registry itself; it is the implicit handler/server attribute contract spread across `BaseHandler`, `NotepadHandlersMixin`, and `RequestPipelineServer`.

Storage ownership is mostly clean: file handlers constrain user files to `uploads/`, notepad owns `notes/`, and static UI is read-only package data. The weak points are lifecycle/operability, not routing intent.

ADRs are mostly aligned with code. `CLAUDE.md` is the stale outlier and should not be trusted as architecture guidance.

## Issues Found

- [MEDIUM] Unmasked inbound WebSocket frames are accepted
  - File/area: [src/websocket.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/websocket.py:91), [src/server.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/server.py:660), [tests/test_websocket.py](/home/user/PycharmProjects/ExperimentalHTTPServer/tests/test_websocket.py:286)
  - Evidence: `parse_ws_frame()` accepts `masked == False` and returns raw payload; `_handle_notepad_ws()` uses it for client frames; tests assert unmasked frames parse.
  - Detail: RFC 6455 requires clients to mask frames and servers to close unmasked frames, optionally with close code `1002`.
  - Impact: protocol non-compliance and weaker intermediary/proxy attack resistance.
  - Confidence: high

- [MEDIUM] `notes/` runtime data is not ignored
  - File/area: [.gitignore](/home/user/PycharmProjects/ExperimentalHTTPServer/.gitignore:36), [src/server.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/server.py:151)
  - Evidence: `.gitignore` ignores `uploads/*` only; `git status --short` shows `?? notes/`. Contents were not read.
  - Detail: server creates `<root>/notes`; encrypted note blobs and metadata sidecars are runtime user data like uploads.
  - Impact: note ciphertext and metadata can be accidentally committed.
  - Confidence: high

- [MEDIUM] Gzip post-processing defeats streaming
  - File/area: [src/server.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/server.py:262)
  - Evidence: `_maybe_gzip_response()` reads `response.stream_path.read_bytes()`, compresses, then clears `stream_path`.
  - Detail: a compressible uploaded file can be loaded fully into memory during GET/FETCH response decoration.
  - Impact: memory spikes scale with file size and configured upload limit.
  - Confidence: high

- [LOW] Multi-origin CORS works for WebSocket checks but emits invalid HTTP ACAO
  - File/area: [src/server.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/server.py:567), [src/http/response.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/http/response.py:108)
  - Evidence: WebSocket origin check splits comma-separated origins; response builder sends raw `cors_origin`.
  - Detail: browsers expect one allowed origin or `*`; comma-separated ACAO is rejected.
  - Impact: configured multi-origin CORS silently fails for normal HTTP responses.
  - Confidence: high

- [LOW] Metrics under-report handled failures
  - File/area: [src/request_pipeline.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/request_pipeline.py:121), [src/metrics.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/metrics.py:25)
  - Evidence: `error=True` is recorded only in the broad exception path; normal 4xx/5xx responses are recorded as non-errors.
  - Detail: handler-returned 500s, auth failures, size failures, and successful WebSocket upgrades are not represented consistently.
  - Impact: `/metrics` can understate operational failure rate.
  - Confidence: high

- [LOW] Package resource helper returns paths outside `as_file()` lifetime
  - File/area: [src/handlers/base.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/base.py:38)
  - Evidence: `get_package_resource()` returns `path` from inside `with importlib.resources.as_file(...)`.
  - Detail: Python docs state temporary extracted resources are cleaned up when the context exits.
  - Impact: UI/static assets may fail under zip/non-filesystem package loaders.
  - Confidence: high for behavior, medium for deployment likelihood

- [LOW] Stale `CLAUDE.md` can reintroduce removed concepts
  - File/area: [CLAUDE.md](/home/user/PycharmProjects/ExperimentalHTTPServer/CLAUDE.md:7), [CLAUDE.md](/home/user/PycharmProjects/ExperimentalHTTPServer/CLAUDE.md:95)
  - Evidence: documents `--opsec --sandbox`, `OpsecHandlersMixin`, random OPSEC methods, and `startswith()` path defense; current CLI exposes `--advanced-upload`, and ADR-004 rejects `startswith()`.
  - Detail: this is stale AI-facing architecture guidance.
  - Impact: future assisted edits may target dead flags or unsafe path patterns.
  - Confidence: high

- [LOW] Tooling pins drift across local, CI, and lock files
  - File/area: [.pre-commit-config.yaml](/home/user/PycharmProjects/ExperimentalHTTPServer/.pre-commit-config.yaml:14), [constraints/ci.txt](/home/user/PycharmProjects/ExperimentalHTTPServer/constraints/ci.txt:16), `uv.lock`
  - Evidence: pre-commit pins Ruff `0.9.0` and mypy `1.14.0`; constraints pin Ruff `0.15.5`, mypy `1.20.1`, cryptography `46.0.5`; untracked `uv.lock` has newer versions.
  - Detail: CI uses `PIP_CONSTRAINT`; pre-commit does not.
  - Impact: local hooks and CI can disagree on formatting/type behavior.
  - Confidence: high

## Concrete Recommendations

Keep the registry/mixin hybrid for now. A rewrite is not justified. The next risk-reducing move is to make the implicit handler context explicit enough to test and review, without creating a framework.

## Quick Wins

- Reject unmasked inbound WebSocket frames in the server path; preserve unmasked frame building for server-to-client frames.
- Add `notes/*` and `!notes/.gitkeep` or ignore `notes/` entirely, depending on whether an empty directory should be tracked.
- Disable gzip for `stream_path` responses unless streaming compression is implemented.
- For CORS, store allowed origins as a set and echo the request `Origin` only when allowed; add `Vary: Origin`.
- Update `CLAUDE.md` to remove `--opsec`, `--sandbox`, `OpsecHandlersMixin`, and `startswith()` guidance.

## Deeper Improvements

- Introduce a small `HandlerContext` or documented Protocol for handler-owned state: `upload_dir`, `notes_dir`, locks, metrics accessor, ECDH manager, advanced-upload flag.
- Make notepad writes atomic with temp files plus `replace()`, then decide whether reads need the same lock or can rely on atomic snapshots.
- Define metrics semantics: count `status_code >= 500` as errors, optionally expose `client_errors`, `server_errors`, and `websocket_upgrades`.
- Make package resource serving byte/stream based instead of returning temporary filesystem paths.

## Open Questions

- Should `uv.lock` become the authoritative lockfile, or should `constraints/ci.txt` remain the only pinned toolchain source?
- Should `/metrics total_errors` mean only internal exceptions, all 5xx, or all non-2xx?
- Is multi-origin CORS officially supported, or should `--cors-origin` stay singular and reject commas early?
