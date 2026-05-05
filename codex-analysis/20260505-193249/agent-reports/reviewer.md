# reviewer Report
_Generated: 2026-05-05 20:20:30 Europe/Moscow_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260505-193249/analysis-plan.md_

## Summary

Scope analyzed: current dirty diff across TLS/ACME, CLI startup config, server TLS display/startup, tests, docs, Docker, constraints, and the saved `api-documenter.md` plus relevant prior reports. The nested reviewer subagent could not read the repo because its read-only sandbox failed with `bwrap`; the findings below are from my host-side read-only review. No files were modified.

## Documentation Checks

`API.md` and `docs/api.md` only replace stale `exphttp[crypto]` wording; they still omit the Notepad HKDF salt/info and recoverability limits. README documents ACME port 80 and cache location, but not `api.ipify.org`, globally routable IPv4, Docker/NAT/volume requirements, or broken cert/key cache recovery. CI stale-doc grep still matches valid current changelog text, so release smoke will fail before browser/Docker validation.

## Detailed Findings

Normal path checked: built-in ACME helper flow, sslip domain derivation, CLI-to-`TLSManager` config, and Docker install path.

Failure path checked: fresh ACME cert with missing/invalid key, invalid CLI flag combinations, stale Notepad crypto guidance.

Integration edge checked: README/Compose/Docker healthcheck versus ACME `~/.exphttp/acme`, port 80, and TLS/auth modes. Runtime tests were not run to keep the review read-only.

## Issues Found

- [HIGH] Release smoke still fails before browser and Docker validation
  - File/area: `.github/workflows/ci.yml`, `docs/changelog.md`
  - Evidence: `.github/workflows/ci.yml:164` greps for `advanced upload is enabled by default`; `docs/changelog.md:38` contains that exact valid changelog text.
  - Detail: This is a confirmed CI blocker independent of the TLS code. The smoke job exits before browser smoke and Docker smoke, so the new TLS/ACME dependency and container paths are not validated.
  - Impact: Merge confidence is overstated; release smoke cannot reach the checks most relevant to this diff.
  - Merge decision: blocker
  - Confidence: high

- [HIGH] Notepad example remains cryptographically incompatible with server/browser
  - File/area: `examples/notepad_client.py`, `src/security/keys.py`, `src/data/static/ui/notepad.js`, `API.md`
  - Evidence: example uses `salt=None` and `info=b"exphttp-notepad"` at `examples/notepad_client.py:118`; server uses 32 zero bytes and `notepad-e2e-key` at `src/security/keys.py:41`; browser matches server at `notepad.js:501`.
  - Detail: The dirty diff updates example dependency text but leaves the wrong HKDF contract. API docs still say HKDF-SHA256 without exact parameters or recovery semantics.
  - Impact: Consumers can create notes that the bundled browser cannot decrypt, or save data that appears durable but is unrecoverable after key loss/reload.
  - Merge decision: blocker
  - Confidence: high

- [MEDIUM] Fresh ACME cert cache is reused without validating private key state
  - File/area: `src/security/tls_manager.py`, `src/security/tls.py`, `tests/test_security/test_tls_manager.py`
  - Evidence: `_try_letsencrypt()` reuses when `fullchain.pem` exists and `check_cert_needs_renewal()` is false at `tls_manager.py:109`, then assigns `privkey.pem` at `tls_manager.py:134`; `_build_context()` only fails later at `tls_manager.py:151`. Tests cover cert+key reuse at `test_tls_manager.py:112`, not missing/invalid/mismatched key.
  - Detail: A partial restore or broken volume can leave a fresh certificate with no usable key. The server skips renewal/recovery and fails late with an SSL load error.
  - Impact: `--letsencrypt` / `--sslip` deployments can suffer startup outages until manual cache repair.
  - Merge decision: blocker unless owner explicitly accepts fail-late behavior
  - Confidence: high

- [MEDIUM] TLS source validation can silently choose the wrong security mode
  - File/area: `src/cli.py`, `src/security/tls_manager.py`
  - Evidence: TLS activation includes `bool(args.cert)` but not `bool(args.key)` at `src/cli.py:193`; `TLSManager.setup()` returns immediately when disabled at `tls_manager.py:71`. Cert/key plus ACME is not rejected, and ACME overwrites provided paths at `tls_manager.py:121` and `tls_manager.py:134`.
  - Detail: `--key` alone can start plaintext HTTP. `--cert --key --letsencrypt` silently attempts ACME instead of using the supplied pair.
  - Impact: Operator mistakes can downgrade to plaintext or trigger unexpected ACME network calls/rate limits.
  - Merge decision: blocker for this TLS/ACME PR
  - Confidence: high

- [MEDIUM] ACME/sslip Docker/operator path is advertised but not complete
  - File/area: `README.md`, `examples/docker/docker-compose.yml`, `Dockerfile`, `src/security/tls.py`
  - Evidence: README shows `exphttp --sslip -H 0.0.0.0 -p 443` at `README.md:370`; Compose exposes only `8080:8080` and mounts only `/data` at `docker-compose.yml:18`; ACME writes under `~/.exphttp/acme` at `tls.py:322`; Docker healthcheck probes plain HTTP at `Dockerfile:60`.
  - Detail: The docs do not give a working container/NAT recipe for port 80 challenge reachability, 443 serving, writable ACME state, or healthcheck override.
  - Impact: Operators can follow docs and still fail issuance, lose cert state, or get false unhealthy containers.
  - Merge decision: needs owner decision; blocker if `--sslip` is released as supported container guidance
  - Confidence: high

## Concrete Recommendations

Fix CI stale grep first so smoke can run.

Add ACME cache validation before reuse: require cert and key to exist, parse both, compare public keys, then renew or fail early with a cache-repair message.

Normalize CLI TLS validation: reject key-only, cert-only, cert/key plus ACME, and add range checks for `--port`, `--max-size`, `--workers`, and `--acme-http-port`.

Fix `examples/notepad_client.py` HKDF constants and add an interoperability test against `src.security.keys`.

## Quick Wins

Replace remaining runtime/UI `exphttp[crypto]` strings in `src/request_pipeline.py:211`, `src/handlers/notepad.py:39`, and `src/data/static/ui/core.js:257/552`.

Update `.pre-commit-config.yaml` mypy deps to include pinned `acme`, `josepy`, `PyOpenSSL`, and `cryptography==48.0.0`.

Add README notes for `api.ipify.org`, global IPv4, Docker volume/ports, and broken cache recovery.

## Deeper Improvements

Add an opt-in ACME staging smoke/release checklist with controlled domain and port-80 routing.

Make ACME cache directory configurable for containers.

Add Docker TLS smoke with `--tls` and `curl -k -X PING https://...`.

## Open Questions

Should broken ACME cache auto-renew, or fail early with manual repair instructions?

Should bare `--sslip` warn or require `-H 0.0.0.0` for public serving?

Is Secure Notepad intended to be durable across reload/restart, or only within the active browser key session?
