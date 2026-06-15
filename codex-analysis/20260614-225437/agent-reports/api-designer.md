# api-designer Report
_Generated: 2026-06-14 23:39:08 Europe/Moscow_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/analysis-plan.md_

## Summary
The current API should be treated as a **legacy v0 contract**: useful and documented, but not clean enough for SDKs or broad publication. The stable pieces are already de facto public: custom methods, `profile`/`capabilities`, NOTE HTTP/WS message shapes, and receive rejection metrics.

A versioned API is needed before adding clients. Keep current behavior for lab users, then add an opt-in v1 surface with normalized errors, explicit idempotency, and exact capability semantics.

## Documentation Checks
Read-only analysis only. No files modified.

I did not use Context7 because the recommendations are API-contract decisions, not dependent on current library/platform details. Parent Context7 checks for pytest, Docker, and cryptography are sufficient for this pass.

## Detailed Findings
Profiles are already a public contract. `src/features.py` defines fixed profile names, method lists, default `lab`, and non-null capability booleans ([src/features.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/features.py:7), [src/features.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/features.py:23), [src/features.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/features.py:47)). `PING` documents `profile` and `capabilities` as source of truth for UI, handlers, CORS, and WebSocket availability ([API.md](/home/user/PycharmProjects/ExperimentalHTTPServer/API.md:376)).

Error handling is intentionally mixed today. `API.md` documents endpoint-specific JSON, text, empty-body, and WebSocket error forms ([API.md](/home/user/PycharmProjects/ExperimentalHTTPServer/API.md:7), [API.md](/home/user/PycharmProjects/ExperimentalHTTPServer/API.md:14)). Shared handler and server helpers both use `{"error": "...", "status": NNN}` ([src/handlers/base.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/base.py:239), [src/server.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/server.py:1036)), but advanced upload, FETCH, INFO, NOTE, and WS keep legacy variants.

Receive-layer failures are not normal HTTP API failures. `src/http/io.py` records low-cardinality rejection reasons and returns empty data on framing failures ([src/http/io.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/http/io.py:29), [src/http/io.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/http/io.py:283)). The server only turns `body_memory_budget_exceeded` into an HTTP `503`; most other receive failures close the connection without a body ([src/server.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/server.py:756)). Docs already say this, but client retry semantics are not explicit ([API.md](/home/user/PycharmProjects/ExperimentalHTTPServer/API.md:76)).

WebSocket application errors differ from HTTP errors. Invalid JSON, non-object messages, unknown types, and invalid IDs return `{"type":"error","error":"..."}`; domain errors for save/load/delete/clear can keep the operation response type and add `error`/`status` ([src/handlers/notepad.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/notepad.py:287), [src/handlers/notepad.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/notepad.py:332), [API.md](/home/user/PycharmProjects/ExperimentalHTTPServer/API.md:735)).

There is a contract mismatch on note IDs: docs describe 32-char hex IDs, while `is_valid_note_id` accepts 1 to 32 lowercase hex chars ([API.md](/home/user/PycharmProjects/ExperimentalHTTPServer/API.md:553), [src/notepad_service.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/notepad_service.py:49)).

## Issues Found
- **Medium: no explicit API version boundary.** `PING` exposes methods, capabilities, and metrics together, making future field changes client-breaking ([API.md](/home/user/PycharmProjects/ExperimentalHTTPServer/API.md:286)).
- **Medium: error taxonomy is not actionable.** Most JSON errors lack stable machine codes, retry hints, and consistent request correlation.
- **Medium: receive-layer close failures are observable only out-of-band.** Clients cannot know whether the reason was header size, transfer encoding, timeout, or invalid content length.
- **Medium: WebSocket errors are not shape-compatible with HTTP errors.** Tests confirm operation-error payloads and generic WS errors differ ([tests/test_websocket_handlers.py](/home/user/PycharmProjects/ExperimentalHTTPServer/tests/test_websocket_handlers.py:372), [tests/test_websocket_handlers.py](/home/user/PycharmProjects/ExperimentalHTTPServer/tests/test_websocket_handlers.py:609)).
- **Low/Medium: advanced upload is hard to build clients around.** Unknown-method upload is lab-friendly but proxy/client-hostile, and success does not return the saved filename/path ([API.md](/home/user/PycharmProjects/ExperimentalHTTPServer/API.md:818)).
- **Low: `X-Request-Id` is not universal.** Docs note direct guard/upgrade errors may be sent before decoration ([API.md](/home/user/PycharmProjects/ExperimentalHTTPServer/API.md:879)); implementation adds it only in normal post-processing ([src/server.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/server.py:950)).

## Concrete Recommendations
Declare current behavior as **legacy v0** and preserve it for lab users. Add an opt-in v1 contract before SDKs or broader publication.

Smallest v1 surface:
- `GET /api/v1/capabilities` for profile, capabilities, supported methods, limits, and supported API versions.
- `GET /api/v1/files?path=...` for INFO/list metadata with `offset`, `limit`, and explicit sort.
- `POST /api/v1/uploads` or `PUT /api/v1/files?path=...` for standard upload clients.
- `GET/POST/DELETE /api/v1/notes...` plus exact `GET /api/v1/notes/ws`.
- Keep SMUGGLE and advanced upload as `lab` capabilities unless product direction says they are public API.

Canonical v1 error envelope:
```json
{"error":{"code":"PAYLOAD_TOO_LARGE","message":"Payload too large","status":413,"retryable":false,"details":{}},"requestId":"abc123"}
```

Canonical critical responses:
```json
{"apiVersion":"1","profile":"lab","capabilities":{"note_http":true,"websocket_notes":true},"methods":["GET","POST","NOTE"]}
```

```json
{"success":true,"id":"0123456789abcdef0123456789abcdef","title":"My Note","created":true,"size":256}
```

```json
{"type":"saved","opId":"save-1","success":true,"id":"0123456789abcdef0123456789abcdef","size":256}
```

```json
{"type":"error","opId":"save-1","operation":"save","error":{"code":"NOTE_NOT_FOUND","message":"Note not found","status":404,"retryable":false}}
```

For receive-layer closes, do not pretend there is an HTTP response. Document them as client transport errors: `transport_closed_before_response`, `httpStatus: null`, `requestId: null`, no handler side effects, reason available only in server metrics/logs. Only `body_memory_budget_exceeded` and request admission failures are HTTP `503` when the server can safely respond.

## Quick Wins
- Add a "Contract Stability" section to `API.md`: legacy v0, stable fields, compatibility promises, and non-stable metrics.
- Add stable error `code` fields to shared JSON errors while keeping existing `error`/`status`.
- Clarify note ID length: either docs change to `1..32 lowercase hex`, or v1 requires exactly 32 and legacy keeps current acceptance.
- Add `api_versions` or `contract_versions` to `PING` as an additive discovery field.
- Document retry guidance for receive-layer closes and for idempotent NOTE saves using `noteId + createIfMissing + opId`.

## Deeper Improvements
- Split health, capabilities, and metrics so `PING` does not freeze the metrics schema.
- Add v1 conformance tests for error envelopes, capability optionality, pagination, and WS errors.
- Introduce idempotency keys for mutating v1 HTTP operations, especially uploads and destructive clears.
- Normalize WebSocket v1 errors to one shape while preserving legacy `/notes/ws`.
- Keep profiles append-only: adding capability keys is safe; removing or renaming keys should require a major contract version.

## Open Questions
- Is the product still lab-first, or should `serve`/`workspace` become the future default?
- Are SMUGGLE and advanced upload public features or lab-only experiments?
- Should future clients target custom methods, or should v1 prefer standard HTTP endpoints?
- Is this permanently single-tenant per server instance, or will hosted/multi-user scope appear?
- Should Notepad become durable/recoverable, which would change session and key semantics?
- What is the deprecation window for legacy text/empty-body errors once v1 exists?
