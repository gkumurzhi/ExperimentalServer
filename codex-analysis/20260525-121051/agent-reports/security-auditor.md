# security-auditor Report
_Generated: 2026-05-25 12:47:23 MSK_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260525-121051/analysis-plan.md_

## Summary

Read-only static audit of `/home/user/PycharmProjects/ExperimentalHTTPServer` across the requested server, auth, crypto, TLS, CORS, handler, WebSocket, docs, Docker, CLI, and security test paths. No files were modified and no tests were executed.

External exposure is not safe enough without additional operational controls. The highest risk items are aggregate disk exhaustion, command-line credential exposure, wildcard browser mutation/WebSocket admission, always-on destructive/demo features, and proxy-unaware auth rate limiting.

Positive controls found: path containment is strong, `Content-Length`/`Transfer-Encoding` smuggling defenses are present, Basic Auth hashing uses PBKDF2 and constant-time comparison, AES-GCM nonce/HMAC usage is sound, WebSocket frame parsing enforces masks and caps, and TLS uses a modern server context.

## Documentation Checks

- **Python stdlib** `3.10-3.13` - Context7 topic checked: `ssl.SSLContext`, `secrets`, `hmac.compare_digest`; impact on recommendation: current TLS context, randomness, and digest comparison choices are generally appropriate.
- **cryptography** `>=48.0`, pinned `48.0.0` in constraints - Context7 topic checked: `AESGCM`, nonce reuse, ECDH/HKDF`; impact on recommendation: AES-GCM nonce handling and ECDH-derived session keys are reasonable, but Notepad durability/forward-secrecy semantics remain product decisions.
- **MDN Web Docs / Browser platform** `current/unknown` - Context7 topic checked: CORS wildcard credentials and WebSocket `Origin`; impact on recommendation: wildcard CORS should not be treated as trust for browser mutations or WebSocket upgrades.
- **Docker** `python:3.12-slim` pinned digest - Context7 topic checked previously in Phase 1: production hardening; impact on recommendation: image has good non-root/pinned-base signals, but TLS/auth healthcheck behavior remains an operational edge.

## Detailed Findings

Scope analyzed: `src/server.py`, `src/request_pipeline.py`, `src/security/*`, `src/http/*`, `src/handlers/*`, `src/notepad_service.py`, `src/websocket.py`, `src/cli.py`, `SECURITY.md`, README/API/docs, Dockerfile/Compose examples, and security-relevant tests under `tests/`.

Validated by static review: normal auth-before-dispatch flow, same-origin mutation allowance, per-request body caps, path traversal rejection, hidden file protections, malformed WebSocket rejection, and TLS context construction. Still requiring runtime/environment verification: real reverse-proxy behavior, client IP attribution, filesystem quota behavior, ACME renewal/reload behavior, and browser credential behavior for deployed origins.

## Issues Found

- [HIGH] Aggregate storage exhaustion through repeated uploads and notes
  - File/area: `src/server.py`, `src/handlers/files.py`, `src/handlers/advanced_upload.py`, `src/notepad_service.py`, `docs/threat-model.md`
  - Evidence: default per-request upload cap is 100 MB at `src/server.py:84`; `uploads/` and `notes/` are created without aggregate budgets at `src/server.py:206-212`; standard upload writes each body at `src/handlers/files.py:418-420`; advanced upload writes decoded payloads at `src/handlers/advanced_upload.py:385-387`; notes are capped per blob at `src/notepad_service.py:21` and written at `src/notepad_service.py:373-375`; threat model lists “Large upload fills disk” as mitigated only by `--max-size` at `docs/threat-model.md:61-62`.
  - Detail: Attack path is repeated authenticated uploads/notes, or unauthenticated writes when `--auth` is disabled, each under the per-object cap. There is no total byte, file count, note count, retention, or reserved-free-space enforcement.
  - Impact: Disk exhaustion can take down the service or host, break logs/cert renewal/temp writes, and degrade external/trusted-lab availability.
  - Confidence: high

- [HIGH] Service/container Basic Auth secrets are exposed through argv-only injection
  - File/area: `src/cli.py`, `src/server.py`, `SECURITY.md`, README, Docker examples
  - Evidence: CLI exposes only `--auth CREDS` at `src/cli.py:173-176` and passes it directly at `src/cli.py:264`; server parses literal `user:password` at `src/server.py:225-231`; non-interactive `--auth random` refuses and tells operators to pass explicit credentials at `src/server.py:241-244`; docs recommend explicit `user:password` for services at `SECURITY.md:90-93`; examples show `--auth admin:...` in README and Compose.
  - Detail: Attack path is local/container/CI/orchestration/log access to process arguments, shell history, Compose files, or service manifests. Prerequisite is host/container observability, which is common in deployments.
  - Impact: Leaked credentials grant the same global access as a valid Basic Auth user, including upload, delete, note, and SMUGGLE operations.
  - Confidence: high

- [MEDIUM] Wildcard CORS is treated as authorization for browser mutations and WebSocket upgrades
  - File/area: `src/http/cors.py`, `src/server.py`, `src/request_pipeline.py`, tests/docs
  - Evidence: wildcard config becomes `("*",)` at `src/http/cors.py:83-86`; mutation guard allows wildcard at `src/server.py:781` and `src/server.py:804-805`; WebSocket origin guard allows wildcard at `src/server.py:840-841`; tests assert this behavior at `tests/test_server_methods.py:289-304` and `tests/test_server_methods.py:507-522`; docs explicitly say wildcard opts into browser mutations at `API.md:786-787`.
  - Detail: MDN guidance distinguishes wildcard read CORS from credentialed trust and recommends rejecting unacceptable WebSocket origins. Attack path is a malicious browser origin reaching the server and triggering state-changing HTTP methods or Notepad WebSocket operations when `--cors-origin *` is configured.
  - Impact: Cross-origin file upload/delete, note mutation/clear, or WebSocket note actions become possible under a configuration that operators may expect to mean “read CORS from anywhere.”
  - Confidence: high

- [MEDIUM] High-risk methods and demo features are always enabled behind one global auth decision
  - File/area: `src/server.py`, `src/cli.py`, `src/handlers/__init__.py`, `src/handlers/files.py`, `src/handlers/notepad.py`, `src/handlers/smuggle.py`
  - Evidence: advanced upload is always enabled at `src/server.py:148`; `--advanced-upload` is a deprecated no-op at `src/cli.py:89-93`; registry always registers `DELETE`, `NOTE`, and `SMUGGLE` at `src/handlers/__init__.py:36-51`; unknown methods with body/`X-D`/`?d=` route to advanced upload at `src/handlers/__init__.py:64-77`; `DELETE /uploads?clear=1` clears uploads at `src/handlers/files.py:206-210`; `NOTE /notes?clear=1` clears notes at `src/handlers/notepad.py:87-90`.
  - Detail: Attack path is any valid Basic Auth user, or any reachable client if auth is disabled, invoking destructive/demo endpoints. There is no method-level authorization, role split, or external-mode feature profile.
  - Impact: Least-privilege deployments are not possible; compromised credentials or accidental browser/API actions can clear data or expose risky demo capabilities.
  - Confidence: high

- [MEDIUM] Basic Auth rate limiting is proxy-unaware and in-memory
  - File/area: `src/security/auth.py`, `src/server.py`, reverse-proxy examples
  - Evidence: limiter is per in-memory IP at `src/security/auth.py:183-215`; server keys it on `client_address[0]` at `src/server.py:649-677`; nginx example forwards `X-Real-IP`/`X-Forwarded-For` at `examples/advanced_upload_nginx.md:34-35`, but the app does not consume trusted proxy headers.
  - Detail: Behind a reverse proxy, all clients can collapse to one backend IP, causing shared lockout and poor brute-force attribution. Restarts also clear limiter state.
  - Impact: External baseline depends on proxy rate limiting, but the app’s own limiter is unreliable in common deployment topology.
  - Confidence: high

- [LOW] ACME/TLS lifecycle and Docker healthcheck are startup-bound operational risks
  - File/area: `src/server.py`, `src/security/tls_manager.py`, `src/security/tls.py`, `Dockerfile`, README
  - Evidence: TLS setup runs at startup only at `src/server.py:482-485`; Let’s Encrypt renewal logic runs inside setup at `src/security/tls_manager.py:81-90` and `src/security/tls_manager.py:99-153`; README states renewal occurs at start at `README.md:391`; Docker healthcheck probes plain HTTP at `Dockerfile:61-64`.
  - Detail: Long-running ACME deployments can expire without in-process renewal/reload. TLS/auth modes require an overridden healthcheck, which docs acknowledge at `README.md:437-441`.
  - Impact: Availability and certificate trust failures, not a direct code-execution or auth bypass issue.
  - Confidence: medium

- [LOW] Notepad crypto is reasonable, but session/recoverability semantics are not access control
  - File/area: `src/handlers/notepad.py`, `src/notepad_service.py`, `src/security/keys.py`, `src/websocket.py`
  - Evidence: session IDs are audit-only by design in `src/handlers/notepad.py`; note list/load/delete routes do not require a session at `src/handlers/notepad.py:96-103` and `src/handlers/notepad.py:254-268`; metadata stores title/timestamps/size at `src/notepad_service.py:354-360`; process ECDH private key is generated at `src/security/keys.py:72`; AES-GCM uses 12-byte random nonces at `src/security/keys.py:182-185`.
  - Detail: Any authenticated user can list/load/delete encrypted blobs; encryption protects note content, not note metadata or per-user authorization. Restart/session eviction can break recoverability unless the client UX/key model handles it.
  - Impact: Product/security expectation mismatch, especially for multi-user or durable-note deployments.
  - Confidence: medium

## Concrete Recommendations

1. Add aggregate storage controls: `--max-upload-bytes`, `--max-upload-files`, `--max-notes-bytes`, `--max-notes`, retention age, and pre-write reservation under lock. Return a clear `507` or `413` before writing.
2. Add safe feature profiles or flags: disable `SMUGGLE`, advanced upload, `NOTE`, and destructive `DELETE`/`clear=1` unless explicitly enabled for trusted-lab mode.
3. Split read CORS from write/WebSocket trust. Keep `Access-Control-Allow-Origin: *` only for read-only responses; require exact origins for browser mutations and WebSocket upgrades.
4. Add non-argv secret injection: `--auth-env VAR`, `--auth-file PATH`, and/or `--auth-stdin`; update docs and examples away from literal `--auth user:password`.
5. Define reverse-proxy behavior: either document app rate limiting as local-only and require proxy rate limits, or implement `--trusted-proxy CIDR` before honoring `Forwarded`/`X-Forwarded-For`.
6. Treat ACME renewal/health as deployment requirements: schedule restart/reload or add background renewal; require protocol-aware healthchecks for TLS/auth.

## Quick Wins

- Change wildcard behavior so `_is_browser_origin_allowed_for_mutation()` and `_is_websocket_origin_allowed()` reject `("*",)` while preserving wildcard read CORS.
- Update tests currently asserting wildcard mutation/WS allow to expect `403`.
- Add a warning in `--help`, README, and `SECURITY.md` that `--auth USER:PASS` leaks through process arguments.
- Add OS/container quotas and monitoring for `<dir>/uploads` and `<dir>/notes` before code-level quotas land.
- Fix `docs/threat-model.md` so `--max-size` is described as per-request only, not disk-exhaustion mitigation.

## Deeper Improvements

- Add method-level authorization or roles: read-only, upload-only, destructive admin, notepad admin.
- Add per-user note namespaces if Notepad is intended for more than one authenticated user.
- Add durable client-side key backup/recovery UX if Notepad is intended to survive restarts/session loss.
- Add trusted-proxy configuration with strict CIDR validation and tests for forwarded host/scheme/client IP.
- Add storage-pressure tests that repeatedly write uploads/notes until aggregate limits trigger.

## Open Questions

- Is “external exposure” meant to include untrusted internet clients, or only controlled external networks with allowlists?
- Should `--cors-origin *` ever permit writes, or should wildcard be read-only by policy?
- Should Basic Auth represent one shared admin identity, or multiple users with different method permissions?
- Should Notepad be a scratchpad with ephemeral sessions, or durable encrypted storage?
- Who owns storage enforcement in production: app-level quotas, filesystem quotas, container volume limits, or reverse proxy policy?
