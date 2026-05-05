# api-documenter Report
_Generated: 2026-05-05 20:18:00 Europe/Moscow_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260505-193249/analysis-plan.md_

## Summary

Applied a read-only api-documenter pass over the public API/docs boundary: `API.md` -> `docs/api.md`, README API/TLS sections, `examples/notepad_client.py`, Docker examples, and implementation flow from socket receive to `RequestPipeline`, handlers, WebSocket handling, and TLS/ACME setup.

The canonical API docs are much better than the prior reports: INFO/SMUGGLE examples, error-body caveats, CORS preflight behavior, advanced upload availability, WebSocket origin checks, and receive-layer no-response closes are now mostly documented. The remaining highest-risk docs gap is Secure Notepad's key/recovery contract: the API explains ECDH but does not clearly document the current session-key durability limit or the exact HKDF parameters consumers need.

No files were modified. `tools/sync_docs.py --check` reports that `API.md` and `docs/api.md` are in sync.

## Documentation Checks

- Normal path checked: custom method registry maps GET/HEAD/POST/PUT/PATCH/DELETE/OPTIONS/FETCH/INFO/PING/NONE/NOTE/SMUGGLE, with unknown payload methods routed to advanced upload in [src/handlers/__init__.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/__init__.py:33).
- Failure path checked: API docs distinguish JSON/text errors from receive-layer connection closes in [API.md](/home/user/PycharmProjects/ExperimentalHTTPServer/API.md:12); implementation closes without HTTP response for unsupported transfer encoding, invalid/conflicting content length, size guards, and timeouts in [src/http/io.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/http/io.py:82).
- Integration edge checked: ACME/sslip CLI help, README, `TLSManager`, ACME issuance, Docker Compose, and Docker healthcheck were compared.
- External docs were not re-queried because these findings depend on local implementation behavior; the parent/prior agents already recorded Context7 checks for the relevant ACME, argparse, WebSocket, and crypto APIs.

## Detailed Findings

The API reference is synchronized and now documents several important edge cases: request guards without HTTP bodies, WebSocket upgrade failures before handshake, CORS preflight headers, and advanced upload routing. That removes several older documentation-engineer findings from the current API surface.

The major remaining gap is decision quality for consumers: a client author can follow the Secure Notepad docs and example, save notes, and still produce ciphertext that is not reload/restart recoverable or is incompatible with the browser/server HKDF contract. The TLS/ACME docs are close but still omit practical deployment constraints that determine whether `--sslip` works in Docker/NAT environments.

## Issues Found

- [HIGH] Secure Notepad key contract omits recoverability limits and exact HKDF parameters
  - File/area: [API.md](/home/user/PycharmProjects/ExperimentalHTTPServer/API.md:327), [examples/notepad_client.py](/home/user/PycharmProjects/ExperimentalHTTPServer/examples/notepad_client.py:118), [src/security/keys.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/security/keys.py:41), [src/data/static/ui/notepad.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/notepad.js:501)
  - Evidence: API says clients derive AES-256-GCM via ECDH/HKDF-SHA256, but omits salt/info and reload/restart recoverability semantics. Server/browser use 32 zero salt and info `notepad-e2e-key`; the example client uses `salt=None` and info `exphttp-notepad`.
  - Detail: `sessionId` is documented as audit-only in [API.md](/home/user/PycharmProjects/ExperimentalHTTPServer/API.md:371), and stored notes are opaque ciphertext plus plaintext metadata. The browser keeps `notepadDerivedKey` only in memory, while the server stores ciphertext bytes and plaintext title metadata. The docs do not clearly tell consumers that the server cannot decrypt, repair, or re-key notes, and that current browser-created ciphertext depends on the active client key material.
  - Impact: API consumers can build clients that save notes they cannot decrypt after reload/server restart, or that cannot interoperate with the bundled browser UI.
  - Confidence: high

- [MEDIUM] ACME/sslip docs under-specify runtime prerequisites and recovery behavior
  - File/area: [README.md](/home/user/PycharmProjects/ExperimentalHTTPServer/README.md:360), [src/security/tls.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/security/tls.py:38), [src/security/tls_manager.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/security/tls_manager.py:99), [examples/docker/docker-compose.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/examples/docker/docker-compose.yml:18)
  - Evidence: README mentions external port 80 and cache reuse, but implementation auto-detects public IPv4 through `https://api.ipify.org`, rejects non-global IPv4s, binds an HTTP-01 challenge server, and reuses a fresh `fullchain.pem` without first validating that `privkey.pem` exists.
  - Detail: Docker Compose exposes only `8080:8080`, keeps the container read-only except `/tmp` and `/data`, and does not document an ACME cache volume or port 80 mapping. Docker healthcheck probes plain HTTP on port 8080.
  - Impact: Operators may believe `exphttp --sslip -H 0.0.0.0 -p 443` is sufficient, but issuance can fail behind NAT, without public port 80 forwarding, without outbound `api.ipify.org`, or with a broken cache state.
  - Confidence: high

- [LOW] WebSocket text-frame contract is stricter than implementation
  - File/area: [API.md](/home/user/PycharmProjects/ExperimentalHTTPServer/API.md:534), [src/server.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/server.py:773), [src/handlers/notepad.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/notepad.py:267)
  - Evidence: API says all WebSocket messages are UTF-8 JSON text frames. The server dispatches both text and binary opcodes to the Notepad message handler, where invalid UTF-8/binary payloads become JSON `Invalid JSON` app errors.
  - Detail: This is not a server correctness bug by itself, but the documented protocol contract does not match the actual compatibility/error model.
  - Impact: Custom clients and protocol tests may expect binary frames to be rejected at the WebSocket protocol layer, but the server currently treats them as application-message errors.
  - Confidence: high

- [LOW] Advanced upload cap wording overstates early rejection for JSON bodies
  - File/area: [API.md](/home/user/PycharmProjects/ExperimentalHTTPServer/API.md:602), [src/handlers/advanced_upload.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/advanced_upload.py:141), [src/handlers/advanced_upload.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/advanced_upload.py:292)
  - Evidence: Docs say advanced upload applies memory caps before decoding or writing. For JSON body transport, implementation parses the full JSON body first, then validates encoded field size.
  - Detail: The receive layer still enforces the global upload cap, but the advanced-upload-specific cap does not protect the JSON parser from oversized-but-received request bodies.
  - Impact: Integrators may overestimate how early advanced upload rejects large JSON payloads and choose JSON transport for sizes better handled by standard body uploads.
  - Confidence: high

- [LOW] README response-header table omits upload aliases
  - File/area: [README.md](/home/user/PycharmProjects/ExperimentalHTTPServer/README.md:227), [src/handlers/files.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/files.py:311), [src/handlers/__init__.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/__init__.py:33)
  - Evidence: README lists `X-File-Name`, `X-File-Path`, and `X-Upload-Status` for `NONE`, while POST/PATCH delegate to `handle_none` and PUT is registered directly to `handle_none`.
  - Detail: `API.md` documents POST/PUT/PATCH/NONE correctly; README is the drift point.
  - Impact: Users relying on README may miss useful response headers for standard-method uploads.
  - Confidence: high

## Concrete Recommendations

Update canonical `API.md` first, then regenerate/sync `docs/api.md`.

Smallest safe change: add a Secure Notepad "key and recovery contract" subsection that states exact HKDF parameters, encrypted blob wire format, plaintext metadata fields, `sessionId` audit-only behavior, and the current limitation that the server cannot recover/re-key ciphertext when the client key is lost. Fix or mark `examples/notepad_client.py` as incompatible until it uses the same HKDF salt/info as the server/browser.

For ACME/sslip, add an operator note covering `api.ipify.org`, globally routable IPv4 requirement, public port 80 reaching the HTTP-01 challenge server, Docker/NAT port and volume requirements, unsupported wildcard/DNS-01, and broken cache recovery when `fullchain.pem` exists but `privkey.pem` is missing.

## Quick Wins

- Add HKDF constants near [API.md](/home/user/PycharmProjects/ExperimentalHTTPServer/API.md:352): salt = 32 zero bytes, info = `notepad-e2e-key`.
- Add one warning near [API.md](/home/user/PycharmProjects/ExperimentalHTTPServer/API.md:404) that note titles are plaintext metadata and `data` is the only encrypted body field.
- Correct the README header table to list POST/PUT/PATCH/NONE for upload response headers.
- Clarify whether WebSocket binary frames are unsupported-but-app-error or should be protocol-closed.
- Add a short ACME Docker example showing `80:80`, `443:443`, and a writable ACME cache path.

## Deeper Improvements

- Add contract tests that execute API examples for NOTE key exchange/save/load and advanced upload failure cases.
- Add a live or manual ACME smoke checklist for sslip/NAT/Docker, separate from mocked ACME unit tests.
- Decide whether Secure Notepad is intended to be durable across browser reload/server restart; if yes, the implementation needs a documented key persistence/migration design before docs can safely promise durability.
- Consider generating selected method/status/header tables from handler tests to keep README and API reference aligned.

## Open Questions

- Is Secure Notepad intended to provide durable decryptability across browser reloads and server restarts, or only within the active browser key session?
- Should binary WebSocket frames be accepted as application errors, or should they close with a protocol/policy code?
- Should the ACME cache directory be configurable for containers?
- Should the empty `exphttp[crypto]` compatibility extra remain visible in runtime/UI/docs, or be removed from user-facing guidance?
