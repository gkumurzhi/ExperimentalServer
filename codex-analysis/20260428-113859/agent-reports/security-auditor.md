# security-auditor Report
_Generated: 2026-04-28 12:02:00 MSK_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/analysis-plan.md_

## Summary

Scope analyzed: the listed `src/security`, `src/http`, `src/request_pipeline.py`, `src/server.py`, `src/websocket.py`, handler modules, notepad storage service, `SECURITY.md`, `docs/threat-model.md`, ADR-002/004, plus relevant tests/docs for CORS, WebSocket, TLS, and advanced upload. No project files or runtime `uploads/` / `notes/` contents were modified or read.

Highest risk: `GET /static/...` can traverse out of bundled static assets and serve files outside `uploads/`. Auth, rate limiting, and WebSocket origin checks are centrally applied before dispatch when enabled, but several handler-specific authorization gaps remain.

## Documentation Checks

- **Context7 MCP** `unknown` — Context7 topic checked: `cryptography AESGCM/ECDH/HKDF, Python ssl, CORS/WebSocket`; impact on recommendation: active tool returned “Monthly quota reached.” Local token status was OK, but I did not rotate/restart MCP because this was a read-only audit.
- **cryptography** `project >=44.0; official latest checked` — Context7 topic checked: `AESGCM nonce/authentication failure, ECDH + HKDF`; impact: AES-GCM decryption failure means key/nonce/AAD/ciphertext may be wrong and should fail closed; ECDH shared secrets should go through a KDF. Source: https://cryptography.io/en/latest/hazmat/primitives/aead/ and https://cryptography.io/en/latest/hazmat/primitives/asymmetric/ec/
- **Python ssl** `3.14 docs / project Python >=3.10` — Context7 topic checked: `PROTOCOL_TLS_SERVER, minimum_version, set_ciphers`; impact: current TLS context shape is defensible for the stated threat model, with TLS 1.2+ and AEAD/ECDHE ciphers. Source: https://docs.python.org/3/library/ssl.html
- **WHATWG Fetch / MDN CORS** `current` — Context7 topic checked: `Access-Control-Allow-Origin`; impact: HTTP CORS must return `*`, `null`, or one origin, not a comma-separated allowlist. Sources: https://fetch.spec.whatwg.org/ and https://developer.mozilla.org/docs/Web/HTTP/Headers/Access-Control-Allow-Origin
- **RFC 6455 WebSocket** `RFC 6455` — Context7 topic checked: `client masking`; impact: servers must close on unmasked client frames; current parser accepts them. Source: https://www.rfc-editor.org/rfc/inline-errata/rfc6455.html
- **Certbot** `5.5.0.dev0 docs` — Context7 topic checked: `certonly standalone non-interactive`; impact: subprocess arguments match documented certbot usage; no shell injection found because commands use argv lists. Source: https://eff-certbot.readthedocs.io/en/latest/using.html

## Detailed Findings

Auth is consistently applied before HTTP dispatch and WebSocket upgrade in `src/request_pipeline.py:104-110`; rate limiting is applied in `src/server.py:432-473`. Path containment is strong where requests go through `resolve_descendant_path()` / `relative_to()`, but the static asset exception bypasses it. Advanced upload has good negative handling for structured invalid JSON/base64/HMAC in several paths, but URL base64 is lenient and AES-GCM authentication failure is not treated as request failure.

Validated with read-only snippets:
- `get_package_resource("static/../../server.py")` resolved to `src/server.py`.
- `parse_ws_frame(build_ws_frame(...))` accepted an unmasked frame.
- comma-separated CORS config emitted one invalid `Access-Control-Allow-Origin` value.
- URL advanced upload decoder accepted malformed `SGVsbG8!!!` as `b"Hello"`.
- AES wrong-key decrypt returned `None`, and handler code would still write the original ciphertext.

## Issues Found

- [HIGH] Static asset path traversal can disclose files outside `uploads/`
  - File/area: `src/handlers/files.py:44-49`, `src/handlers/base.py:25-55`
  - Evidence: `_resolve_get_path()` sends any `static/` path directly to `get_package_resource()`; that helper joins the user path without rejecting `..`. Validation resolved `static/../../server.py` to `src/server.py` and `static/../../../pyproject.toml` to repo root.
  - Detail: A request such as `GET /static/../../server.py` bypasses the uploads-only resolver and can serve files readable by the process.
  - Impact: Remote file disclosure when the service is reachable and auth is disabled or credentials are valid.
  - Confidence: high

- [MEDIUM] Hidden uploads are blocked for GET/INFO but exposed through FETCH/SMUGGLE
  - File/area: `src/handlers/files.py:41-49`, `src/handlers/files.py:327-348`, `src/handlers/smuggle.py:31-54`, `src/handlers/files.py:178-227`
  - Evidence: GET checks `_is_hidden_file()`, INFO checks it in `src/handlers/info.py:23-24`; FETCH, SMUGGLE, and DELETE do not.
  - Detail: `/uploads/.env` is not served by GET/INFO, but `FETCH /uploads/.env` or `SMUGGLE /uploads/.env` can read it if present.
  - Impact: Confidentiality loss for hidden/service files under `uploads/`; integrity loss via individual DELETE.
  - Confidence: high

- [MEDIUM] Advanced upload fails open on AES-GCM wrong key or tampering
  - File/area: `src/handlers/advanced_upload.py:224-228`, `src/security/crypto.py:77-111`
  - Evidence: `decrypt()` returns `None` on AES-GCM auth failure, but handler only skips replacement and continues to write `file_data`. Existing test `tests/test_handlers/test_handler_integration.py:974-997` documents this behavior.
  - Detail: AES-GCM gives an authenticated failure signal; the upload path treats that as “store ciphertext anyway.”
  - Impact: Corrupted or tampered encrypted uploads are accepted as successful, undermining fail-safe behavior and auditability.
  - Confidence: high

- [LOW] URL advanced upload base64 validation is lenient
  - File/area: `src/handlers/advanced_upload.py:40-49`, `src/handlers/advanced_upload.py:201-210`
  - Evidence: `_urlsafe_b64decode()` calls `base64.b64decode(data)` without `validate=True`; malformed `SGVsbG8!!!` decoded to `b"Hello"`.
  - Detail: Header/body transports reject invalid base64; URL transport can silently discard invalid characters.
  - Impact: Inconsistent validation and possible payload confusion across transports.
  - Confidence: high

- [LOW] WebSocket accepts unmasked client frames
  - File/area: `src/websocket.py:90-130`, `src/server.py:657-690`
  - Evidence: parser returns raw payload when `masked` is false; server then processes text/binary frames.
  - Detail: RFC 6455 requires client-to-server frames to be masked and the server to close on unmasked frames.
  - Impact: Protocol non-compliance and weaker intermediary-safety assumptions; not an auth bypass by itself.
  - Confidence: high

- [LOW] Comma-separated CORS allowlist is emitted as invalid ACAO
  - File/area: `src/http/response.py:103-110`, `src/server.py:567-572`, `tests/test_server_methods.py:266-285`
  - Evidence: WebSocket origin allowlist splits comma-separated origins, but HTTP response builder writes the raw string.
  - Detail: `Access-Control-Allow-Origin: https://app.example, https://admin.example` is not browser-valid CORS.
  - Impact: Cross-origin browser clients fail despite matching the configured allowlist.
  - Confidence: high

- [LOW] Security docs/instructions contain stale or overstated guidance
  - File/area: `CLAUDE.md:21-22`, `CLAUDE.md:48-64`, `CLAUDE.md:94-95`, `docs/ADR/ADR-002-advanced-upload-xor-hmac.md:21-28`
  - Evidence: `CLAUDE.md` references removed OPSEC/sandbox flows and recommends `startswith()` path checks; ADR-002 says HMAC covers ciphertext + metadata, but code verifies only `file_data`.
  - Detail: This can steer future edits toward known-bad path checks and overstate upload metadata integrity.
  - Impact: Maintenance risk and misleading security claims.
  - Confidence: high

## Concrete Recommendations

Fix first: route static resources through a safe package-resource resolver that rejects `..`, absolute paths, backslashes-as-separators, and requires the resolved path to remain under `src/data`. Add regression tests for encoded traversal like `/static/%2e%2e/%2e%2e/server.py`.

Then make hidden-file policy consistent: apply `_is_hidden_file()` to FETCH, SMUGGLE, and individual DELETE unless there is a documented reason not to.

For advanced upload, treat `encryption` + `decrypt_key` + `decrypt(...) is None` as `400`. Use strict URL-safe base64 decoding with validation.

## Quick Wins

- Add a guard in `get_package_resource()` before any join: reject path parts `""`, `"."`, `".."`, absolute paths, and separators after URL decoding.
- Change `_urlsafe_b64decode()` to use `base64.b64decode(..., altchars=b"-_", validate=True)`.
- In `handle_advanced_upload()`, return `400 {"ok": false, "err": "decrypt"}` when requested decryption fails.
- Reject unmasked client frames with close code `1002`.

## Deeper Improvements

- Split HTTP CORS allowlist from WebSocket origin allowlist: store parsed origins, reflect only the matching request `Origin`, and set `Vary: Origin`.
- Bind advanced-upload HMAC or AEAD AAD to metadata fields such as filename, encryption mode, and transport when those fields affect security semantics.
- Add an authorization matrix test covering every method: GET, HEAD, FETCH, INFO, SMUGGLE, DELETE, NOTE, WebSocket, standard uploads, and advanced uploads.

## Open Questions

- Should hidden files under `uploads/` be completely inaccessible, or only hidden from GET/INFO listings?
- Is raw-body fallback for unknown-method advanced upload intentional when JSON parsing fails?
- Should `--cors-origin` officially support multiple origins, or remain a single-origin CLI option?
- Is the notepad ECDH server key intended to be long-lived per process, or should each exchange use an ephemeral server key for stronger forward secrecy?
