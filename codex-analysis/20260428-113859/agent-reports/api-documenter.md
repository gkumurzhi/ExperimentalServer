# api-documenter Report
_Generated: 2026-04-28 12:43:22 MSK_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/analysis-plan.md_

**Summary**
Domain boundary analyzed: API docs and examples against the request flow `parse/auth/size check -> handler registry -> handler response -> post-processing -> HTTPResponse headers`, plus the WebSocket upgrade path before normal dispatch. I did not modify files, and I did not read secret/runtime data paths.

Primary risk: the docs describe a more uniform API than the implementation provides. Main defects are SMUGGLE response shape, mixed error bodies, INFO schema mismatch, CORS/preflight ambiguity, and advanced-upload examples/edge cases.

**Documentation Checks**
- Checked `API.md`, `docs/api.md`, `README.md`, `src/handlers/*.py`, `src/http/response.py`, `src/request_pipeline.py`, `src/server.py`, and `examples/*`.
- `docs/api.md` is generated from `API.md`; `tools/sync_docs.py --check` passed. The only diff is the generated header in [docs/api.md](/home/user/PycharmProjects/ExperimentalHTTPServer/docs/api.md:1), so `API.md` findings apply to `docs/api.md` with a +2 line offset.
- No external documentation lookup was used. Context7 was not queried because this pass validated project docs against current implementation behavior only.
- `git diff --check` on scoped files reported no whitespace errors.

**Issues Found**
- **HIGH: SMUGGLE API response is documented as HTML, but implementation returns JSON with a temporary URL.**
  Evidence: [API.md](/home/user/PycharmProjects/ExperimentalHTTPServer/API.md:222) says SMUGGLE response is an HTML page; [src/handlers/smuggle.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/smuggle.py:75) returns JSON and `X-Smuggle-URL`. README’s example is closer to reality at [README.md](/home/user/PycharmProjects/ExperimentalHTTPServer/README.md:472). Confidence: high.

- **HIGH: documented global JSON error model is false for several endpoints.**
  Evidence: [API.md](/home/user/PycharmProjects/ExperimentalHTTPServer/API.md:7) says errors use `{"error","status"}` JSON. `FETCH` 404 is `text/plain` at [src/handlers/files.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/files.py:331); invalid `INFO` path is `text/plain` at [src/handlers/info.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/info.py:36); advanced upload can return empty `text/plain` 400 at [src/handlers/advanced_upload.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/advanced_upload.py:179). Confidence: high.

- **MEDIUM: INFO response example does not match implementation.**
  Evidence: [API.md](/home/user/PycharmProjects/ExperimentalHTTPServer/API.md:164) shows child entries with `type`, `size`, `size_human`, `modified`. Implementation returns top-level metadata and directory children only as `name`/`is_dir` at [src/handlers/info.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/info.py:54) and [src/handlers/info.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/info.py:69). Docs also omit the 400 invalid-path case. Confidence: high.

- **MEDIUM: `X-Request-Id` is documented as all-response behavior, but direct error paths bypass post-processing.**
  Evidence: [README.md](/home/user/PycharmProjects/ExperimentalHTTPServer/README.md:229) says all HTTP responses. Normal responses get it in [src/server.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/server.py:536), but auth, payload-size, and WebSocket upgrade errors are sent directly in [src/request_pipeline.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/request_pipeline.py:104) and [src/request_pipeline.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/request_pipeline.py:171). Confidence: high.

- **MEDIUM: CORS contract is underspecified and partly inconsistent with registered methods/headers.**
  Evidence: default CORS methods omit `SMUGGLE` at [src/http/response.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/http/response.py:111); exposed headers omit `X-Request-Id`, `X-Smuggle-URL`, `X-File-Modified`, and `Content-Disposition` at [src/http/response.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/http/response.py:125). `OPTIONS` can append any requested method without checking `--advanced-upload` at [src/handlers/files.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/files.py:317). Confidence: high.

- **MEDIUM: advanced-upload docs and nginx example miss required runtime behavior and failure cases.**
  Evidence: advanced upload is only enabled when unknown methods with payload are allowed at [src/handlers/__init__.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/__init__.py:61), but the nginx example starts without `--advanced-upload` at [examples/advanced_upload_nginx.md](/home/user/PycharmProjects/ExperimentalHTTPServer/examples/advanced_upload_nginx.md:10). Failure cases include invalid base64, empty payload, HMAC failure, and 500 write errors in [src/handlers/advanced_upload.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/advanced_upload.py:204). Confidence: high.

- **MEDIUM: WebSocket docs omit important failure and message semantics.**
  Evidence: upgrade failures can be 400, 403, or 501 in [src/request_pipeline.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/request_pipeline.py:171). Origin policy is implemented in [src/server.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/server.py:557) but not documented. `clear` is supported at [src/handlers/notepad.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/notepad.py:303) but absent from [API.md](/home/user/PycharmProjects/ExperimentalHTTPServer/API.md:445). Domain errors may keep result types like `saved`/`deleted` because `_ws_run_note_operation` overwrites `type` at [src/handlers/notepad.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/notepad.py:312). Confidence: high for visible handler behavior, medium for service-specific payloads.

- **LOW: GET conditional status is missing from GET docs.**
  Evidence: [API.md](/home/user/PycharmProjects/ExperimentalHTTPServer/API.md:28) lists only 200/404, while `_serve_file` returns 304 for matching `If-None-Match` at [src/handlers/files.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/files.py:70). Confidence: high.

**Recommendations**
Smallest safe change: update `API.md` as the canonical contract, then regenerate `docs/api.md`. Favor documenting actual behavior first, because normalizing implementation would be a behavioral change for clients.

Priority edits:
- Replace SMUGGLE response docs with the JSON body, `X-Smuggle-URL`, follow-up `GET`, and one-time deletion behavior.
- Change the global error statement to endpoint-specific error contracts, or normalize the implementation to JSON errors first.
- Update INFO examples to actual top-level fields and child item shape.
- Document exact CORS allow/expose headers and the fact preflight success does not guarantee unknown-method dispatch unless `--advanced-upload` is enabled.
- Add WebSocket 400/403/501 upgrade failures, origin behavior, `clear`, and error-frame semantics.
- Add `--advanced-upload` to `examples/advanced_upload_nginx.md`.

**Quick Wins**
- Fix the nginx advanced-upload command; current recipe will likely produce 405 for `CHECKDATA`.
- Fix SMUGGLE in `API.md`; this is the most visible response/body mismatch.
- Add one failure example each for `FETCH` 404, advanced-upload invalid base64/HMAC failure, and WebSocket forbidden origin.
- Add `304 Not Modified` to GET docs and mention ETag/Last-Modified.

**Open Questions**
- Should all handler errors be normalized to JSON, or should docs preserve current mixed `text/plain`/empty/JSON behavior?
- Should `X-Request-Id` become a true guarantee for auth, 413, and WebSocket upgrade errors?
- Should CORS allowed methods be derived from the handler registry, and should unknown methods only be advertised when `--advanced-upload` is enabled?
- Should advanced-upload decryption/HMAC failures fail closed more aggressively, or remain best-effort as implemented?
- Runtime validation was intentionally not performed because starting the server can create or mutate `uploads/` and `notes/`; these contracts still need a live smoke pass in a disposable temp root.
