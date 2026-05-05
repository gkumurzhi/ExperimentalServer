# security-auditor Report
_Generated: 2026-05-05 20:00:20 Europe/Moscow_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260505-193249/analysis-plan.md_

## Summary

Read-only security audit of the requested boundary: `src/security/*`, `src/request_pipeline.py`, `src/server.py`, `src/http/io.py`, `src/http/cors.py`, `src/handlers/*`, `src/data/static/ui/*`, `SECURITY.md`, `docs/threat-model.md`, plus directly relevant tests and packaging metadata.

The strongest confirmed issue is ACME certificate cache reuse: the manager treats a fresh certificate as reusable without verifying the paired private key exists and is loadable. The rest of the reviewed security boundaries are mostly consistent: Basic Auth has hashing, dummy verification and rate limiting; request framing rejects duplicate conflicting `Content-Length` and all `Transfer-Encoding`; CORS is explicit and does not emit credentials; WebSocket upgrades validate headers and origins; path access is sandboxed with hidden-file checks; upload HTML/SVG is forced to download.

Static review did not find a confirmed attacker-controlled frontend `innerHTML` sink in the inspected UI flows. The main frontend concern is defense-in-depth: CSP still permits inline script, so future escaping regressions would have less browser-side containment.

## Documentation Checks

- **cryptography** `>=48.0` - Context7 topic checked: PEM X.509 certificate loading, PEM private-key loading/serialization; impact on recommendation: reuse checks should parse both certificate and key with `x509.load_pem_x509_certificate` / `serialization.load_pem_private_key`, and the application remains responsible for file existence, pairing and permissions.

- **Certbot acme** `5.5.x` - Context7 topic checked: `ClientV2` account/order flow and HTTP-01 standalone challenge server; impact on recommendation: ACME issuance depends on a reachable temporary HTTP-01 server, normally port 80, and bind/reachability failures need explicit operational verification.

- **pytest** `9.0.3` - Context7 topic checked from parent context: fixtures, monkeypatching and parametrization; impact on recommendation: the missing ACME cache-state tests can be added with the project's existing monkeypatch-based test style.

- **MDN Web Docs / browser platform** `unknown` - Context7 topic checked: CSP `unsafe-inline`, `innerHTML`/Trusted Types, and inline event handling; impact on recommendation: no confirmed XSS was found, but the current CSP allows inline script and therefore weakens containment if a DOM sink later becomes attacker-controlled.

## Detailed Findings

Confirmed positive controls:

- Basic Auth uses PBKDF2 verification, dummy password verification for unknown users, and an IP rate limiter in `src/security/auth.py:152` and `src/security/auth.py:183`; request authentication resets failures on success in `src/server.py:472`.
- Request framing rejects duplicate conflicting or negative `Content-Length` and any `Transfer-Encoding` in `src/http/io.py:21` and `src/http/io.py:109`.
- CORS requires an exact configured origin or `*`, rejects mixed wildcard and explicit origins, and does not emit `Access-Control-Allow-Credentials` in `src/http/cors.py:69` and `src/http/response.py:121`.
- WebSocket upgrades validate RFC 6455 headers and same-origin/CORS origin policy in `src/websocket.py:55` and `src/server.py:610`.
- File paths are resolved under the intended base directory and hidden path segments are blocked in `src/handlers/base.py:124` and `src/handlers/base.py:206`.
- Advanced upload size limits and HMAC-before-decrypt ordering are present in `src/handlers/advanced_upload.py:62` and `src/handlers/advanced_upload.py:329`.
- Frontend inspector redacts sensitive request/response fields before rendering in `src/data/static/ui/inspector.js:4`, `src/data/static/ui/inspector.js:334`, and `src/data/static/ui/inspector.js:484`.

Runtime validation was not performed. Findings below are based on static source and test review only.

## Issues Found

- [MEDIUM] Fresh ACME certificates are reused without validating the private key cache state
  - File/area: `src/security/tls_manager.py`, `src/security/tls.py`, `tests/test_security/test_tls_manager.py`
  - Evidence: `TLSManager._try_letsencrypt()` only checks `cert_path.exists()` and `check_cert_needs_renewal(cert_path)` before reusing the pair, then assigns `self.key_file = str(key_path)` in `src/security/tls_manager.py:109` and `src/security/tls_manager.py:134`. `check_cert_needs_renewal()` parses only the certificate in `src/security/tls.py:283`. The actual failure is deferred to `context.load_cert_chain(self.cert_file, self.key_file)` in `src/security/tls_manager.py:151`. Existing tests cover "cert and key both exist" reuse in `tests/test_security/test_tls_manager.py:112`, but not "fresh cert, missing key".
  - Detail: A partial restore, manual cleanup, broken backup, or local cache tampering can leave `~/.exphttp/acme/live/<domain>/fullchain.pem` present and fresh while `privkey.pem` is missing or invalid. Startup then skips ACME issuance/renewal and fails later while building the SSL context. This is fail-closed but not recoverable.
  - Impact: HTTPS startup outage for `--letsencrypt` / `--sslip` deployments until an operator manually repairs the cache. Remote exploitation requires the attacker to already have filesystem/cache manipulation ability.
  - Confidence: high

- [MEDIUM] Secure Notepad privacy wording overstates E2E coverage because titles are plaintext metadata
  - File/area: `src/handlers/notepad.py`, `src/notepad_service.py`, `src/data/static/ui/notepad.js`, `docs/threat-model.md`
  - Evidence: Handler docstring says "The server never sees plaintext" while also mentioning metadata title storage in `src/handlers/notepad.py:2`. The browser sends `title` as plaintext over both WebSocket and HTTP save paths in `src/data/static/ui/notepad.js:690` and `src/data/static/ui/notepad.js:699`. The service writes `"title": title[:200]` to metadata in `src/notepad_service.py:184` and returns it from list/load paths in `src/notepad_service.py:222` and `src/notepad_service.py:342`. The threat-model asset list does not call out note title metadata in `docs/threat-model.md:10`.
  - Detail: The encrypted note body is opaque to the server, but note titles are plaintext metadata. A user can reasonably interpret "server never sees plaintext" as applying to the full note, then put sensitive content into the title.
  - Impact: Sensitive note titles are exposed to server-side storage, backups, logs/debug tooling, and any authenticated user/API flow that can list or load notes. Prerequisites are server filesystem access or legitimate API access, not unauthenticated remote access.
  - Confidence: high

- [LOW] Secure Notepad failure messages still recommend an empty `exphttp[crypto]` extra
  - File/area: `src/request_pipeline.py`, `src/handlers/notepad.py`, `src/data/static/ui/core.js`, `pyproject.toml`
  - Evidence: Runtime errors say `install exphttp[crypto]` in `src/request_pipeline.py:208` and `src/handlers/notepad.py:38`. UI strings repeat the same requirement in `src/data/static/ui/core.js:257` and `src/data/static/ui/core.js:552`. `pyproject.toml:37` makes `cryptography>=48.0` a normal dependency, while `pyproject.toml:49` defines `crypto = []`.
  - Detail: The suggested remediation no longer installs anything additional. If cryptography is missing because the environment is broken, users are directed to a no-op extra instead of reinstalling or repairing the package environment.
  - Impact: Security-feature availability and operator recovery degrade; Secure Notepad remains unavailable longer after dependency drift or broken installs. Exploitation path is operational, not attacker-driven.
  - Confidence: high

- [LOW] ACME HTTP-01 live operational path is mock-tested but not runtime-verified
  - File/area: `src/security/tls.py`, `tests/test_security/test_tls.py`, `README.md`
  - Evidence: ACME tests patch `_acme_client_for_key`, `_ensure_account`, `_http01_challenges`, and `_challenge_server` in `tests/test_security/test_tls.py:250`. Bind failure is unit-tested in `tests/test_security/test_tls.py:238`, and README documents external port 80 reachability in `README.md:360`.
  - Detail: The code's ACME flow matches the documented standalone HTTP-01 shape, but CI does not exercise staging issuance, real challenge serving, NAT/firewall reachability, or port-80 conflicts.
  - Impact: Production issuance or renewal can fail only after deployment. No direct exploit path was confirmed, but renewal failure can cause HTTPS availability loss.
  - Confidence: high

- [LOW] HTML CSP permits inline script, reducing XSS containment if an escaping regression appears
  - File/area: `src/handlers/files.py`, `src/utils/smuggling.py`, `src/data/static/ui/*`
  - Evidence: HTML responses set `script-src 'self' 'unsafe-inline'` and `style-src 'self' 'unsafe-inline'` in `src/handlers/files.py:119`. Generated smuggle HTML uses inline scripts and an inline `onclick` handler in `src/utils/smuggling.py:82` and `src/utils/smuggling.py:153`.
  - Detail: Current inspected UI sinks generally escape user/server data with `esc()` or use `textContent`; for example `src/data/static/ui/core.js:737`, `src/data/static/ui/files.js:155`, and `src/data/static/ui/inspector.js:461`. No confirmed exploitable DOM XSS was found. The risk is that CSP will not block inline execution if a future `innerHTML` path becomes attacker-controlled.
  - Impact: Defense-in-depth is weaker for frontend regressions. Exploitation requires a separate XSS injection path.
  - Confidence: medium

## Concrete Recommendations

1. Add a single ACME cache validation helper that requires both `fullchain.pem` and `privkey.pem` to exist, parses both, and optionally compares certificate public key to private key public key before reuse.
2. If the fresh cert exists but the key is missing or invalid, either call `obtain_letsencrypt_cert()` to recover or fail with a clear message naming both cache paths and the recovery command.
3. Update Notepad docs/UI wording to say note bodies are encrypted but titles are plaintext metadata, or encrypt titles client-side if the intended guarantee is full-note privacy.
4. Replace `exphttp[crypto]` runtime/UI remediation with "repair/reinstall the default package environment; `cryptography` is a normal runtime dependency."
5. Add an env-gated ACME staging smoke test or documented release checklist that verifies HTTP-01 reachability, bind behavior, renewal, and key/cert persistence.
6. Start CSP hardening by adding `base-uri 'none'; object-src 'none'`; then plan removal of inline smuggle scripts or replace them with nonces/hashes.

## Quick Wins

- Add tests for ACME cache states: fresh cert with missing key, invalid key, and mismatched cert/key.
- Change two backend error strings and four UI translation strings away from `exphttp[crypto]`.
- Add a short Secure Notepad warning near the title field and in `docs/threat-model.md` that titles are metadata.
- Add `rel="noopener"` to the `window.open` smuggle flow or call `window.open(..., 'noopener')` as a low-risk frontend hardening cleanup.

## Deeper Improvements

- Treat ACME account/domain key material as a documented secret store: expected paths, modes, backup rules, restore behavior, and rotation procedure.
- Add a periodic renewal/check command that validates cert/key pair health without starting the full server.
- Move generated smuggle inline JS to a static script or hash/nonce-based policy so CSP can drop `unsafe-inline`.
- Add browser-level tests for inspector redaction and representative `innerHTML` render paths with filenames, headers, note titles, and response bodies containing HTML metacharacters.

## Open Questions

- Is Secure Notepad intended to hide only note bodies, or should titles also be encrypted?
- Should `--letsencrypt` try automatic recovery when the cert is fresh but the key is missing, or should it fail with explicit manual instructions to avoid accidental rate-limit pressure?
- Do release environments have a safe domain for an optional ACME staging smoke test?
- Are reverse proxy CSP/security headers expected to override the app's built-in CSP in deployed scenarios?
