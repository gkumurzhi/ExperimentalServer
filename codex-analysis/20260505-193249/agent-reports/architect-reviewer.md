# architect-reviewer Report
_Generated: 2026-05-05 19:59:30 Europe/Moscow_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260505-193249/analysis-plan.md_

## Summary

Scope analyzed: `src/server.py`, `src/request_pipeline.py`, `src/handlers/__init__.py`, `src/handlers/base.py`, `src/handlers/notepad.py`, `src/notepad_service.py`, `src/security/tls_manager.py`, supporting `src/security/tls.py`, `docs/architecture.md`, `docs/ADR/*`, and targeted docs/tests references for storage and TLS/ACME drift.

Read-only review only. I did not write files or run tests. Validation was by code/docs inspection plus Context7 checks for current `cryptography` and Certbot `acme` API shape.

Handler/server boundaries are mostly coherent after TLS/ACME changes: `TLSManager` owns certificate acquisition/context setup, `server.py` owns lifecycle/socket display state, `RequestPipeline` owns parse/auth/dispatch/WS upgrade orchestration, and `NotepadService` owns transport-independent note persistence. The main risks are not a full architectural break; they are cache-pair recovery, stale dependency-policy messaging, and incomplete persistence documentation.

## Documentation Checks

- **Certbot acme** `>=5.5,<6` - Context7 topic checked: `ClientV2` account/order flow, HTTP-01 standalone resources, `finalized_order.fullchain_pem`; impact on recommendation: embedded ACME flow is directionally aligned, so recommendations focus on local cache/key recovery and documentation, not replacing the API approach.
- **cryptography** `>=48.0` - Context7 topic checked: `CertificateBuilder`, PEM private-key serialization, X.509 certificate loading/validity APIs; impact on recommendation: current in-process cert generation/expiry checks are consistent with current APIs, and there is no reason to restore external OpenSSL as a runtime dependency.
- **pytest** `9.0.3` - Context7 topic checked in source plan: fixtures/monkeypatch/parametrization; impact on recommendation: add focused regression cases for ACME cache-pair behavior rather than broad new integration suites.

## Detailed Findings

Code storage boundaries are clearer than the architecture docs. `server.py` creates `<root>/uploads` and `<root>/notes`, handlers keep ordinary file access under uploads, and `NotepadService` validates note IDs before resolving `<root>/notes/*.enc` and sidecars. ACME material is separate under `~/.exphttp/acme`, with both account keys and domain keys written by `src/security/tls.py`.

TLS/ACME dependency direction is reasonable: `server.py` delegates setup to `TLSManager`, while `TLSManager` delegates low-level ACME/X.509 work to `src.security.tls`. The dirty TLS/ACME change removed `certbot`/`openssl` runtime requirements, but old helper APIs and user-facing messages still expose the previous model.

Validated paths by inspection:
- Normal path: self-signed TLS uses `generate_self_signed_cert()` then `_build_context()`.
- Failure path: explicit ACME failure propagates and does not silently fall back to self-signed.
- Integration edge: legacy `~/.exphttp/letsencrypt` reuse checks both cert and key, but the new `~/.exphttp/acme` reuse path does not.

## Issues Found

- [MEDIUM] Cached ACME certificate reuse does not require the matching private key to exist
  - File/area: [src/security/tls_manager.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/security/tls_manager.py:99)
  - Evidence: `_try_letsencrypt()` defines `fullchain.pem` and `privkey.pem`, but the reuse branch checks only `cert_path.exists()` and `check_cert_needs_renewal(cert_path)` before assigning `self.key_file = str(key_path)`. `_build_context()` later calls `context.load_cert_chain(self.cert_file, self.key_file)` at [src/security/tls_manager.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/security/tls_manager.py:151).
  - Detail: The legacy fallback checks both `legacy_cert_path.exists()` and `legacy_key_path.exists()`, but the primary new ACME cache does not apply the same pair invariant.
  - Impact: If `~/.exphttp/acme/live/<domain>/privkey.pem` is deleted while `fullchain.pem` is still fresh, startup fails late in SSL context creation instead of renewing/recreating the cert/key pair.
  - Confidence: high

- [MEDIUM] Crypto-unavailable remediation points users to an empty compatibility extra
  - File/area: [src/request_pipeline.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/request_pipeline.py:208), [src/handlers/notepad.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/notepad.py:38), [pyproject.toml](/home/user/PycharmProjects/ExperimentalHTTPServer/pyproject.toml:37)
  - Evidence: `pyproject.toml` makes `acme` and `cryptography` runtime dependencies and keeps `crypto = []`, but NOTE/WS errors still say `install exphttp[crypto]`. The bundled UI repeats this at [src/data/static/ui/core.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/core.js:552).
  - Detail: ADR-003 intentionally keeps `[crypto]` as a no-op compatibility extra, so this remediation no longer fixes a broken environment.
  - Impact: In manually modified or broken installs, users follow an instruction that can leave the failure unchanged.
  - Confidence: high

- [LOW] Architecture docs omit the full runtime persistence boundary
  - File/area: [docs/architecture.md](/home/user/PycharmProjects/ExperimentalHTTPServer/docs/architecture.md:75)
  - Evidence: architecture security layers document only `<root>/uploads/`; code also creates `<root>/notes/` at [src/server.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/server.py:183), and ACME keys/certs live under `~/.exphttp/acme` via [src/security/tls_manager.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/security/tls_manager.py:99) and [src/security/tls.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/security/tls.py:112).
  - Detail: API docs do describe notes separately, and README mentions ACME certificate storage, but the architecture boundary does not identify notes, account keys, domain private keys, or legacy read-only ACME migration.
  - Impact: Backup, cleanup, container volume, and incident-recovery decisions can miss persistent secrets or note data.
  - Confidence: high

- [LOW] Legacy external-tool probes are now misleading compatibility surface
  - File/area: [src/security/tls.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/security/tls.py:261), [src/__init__.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/__init__.py:10)
  - Evidence: `check_openssl_available()` and `check_certbot_available()` still shell out to external binaries, while ADR-003 says TLS no longer requires external `openssl` or `certbot`. `check_openssl_available` is still re-exported from the package root.
  - Detail: These helpers may still be useful as legacy diagnostics, but their names imply runtime readiness checks.
  - Impact: Downstream code or contributors can incorrectly treat missing OpenSSL/certbot executables as TLS/ACME blockers.
  - Confidence: high

- [LOW] ADR-003 is updated, but navigation and summary text still carry old dependency concepts
  - File/area: [mkdocs.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/mkdocs.yml:57), [README.md](/home/user/PycharmProjects/ExperimentalHTTPServer/README.md:11), [CLAUDE.md](/home/user/PycharmProjects/ExperimentalHTTPServer/CLAUDE.md:7)
  - Evidence: ADR-003 title and ADR index now say runtime crypto and ACME dependencies, but MkDocs nav still says `ADR-003 · Optional cryptography`; README still says no external dependencies; CLAUDE.md still says zero external dependencies for core functionality.
  - Detail: ADR-002 correctly marks dependency-policy portions as superseded by ADR-003, so the remaining drift is around discovery and high-level summaries.
  - Impact: Reviewers and future agents may make dependency-policy decisions from stale entry points.
  - Confidence: high

## Concrete Recommendations

1. Treat ACME cert/key as an atomic pair in `TLSManager._try_letsencrypt()`: renew when `not cert_path.exists() or not key_path.exists() or check_cert_needs_renewal(cert_path)`. Add a regression test where `fullchain.pem` exists, `privkey.pem` is missing, and `obtain_letsencrypt_cert()` is called.

2. Replace `install exphttp[crypto]` messages with a runtime-dependency repair message, for example: `cryptography runtime dependency unavailable; reinstall exphttp or install cryptography>=48.0`. Update HTTP, WS, and UI strings together.

3. Add a short `Persistence and Storage Boundaries` section to `docs/architecture.md`: `<root>/uploads`, `<root>/notes`, `~/.exphttp/acme/accounts/*.pem`, `~/.exphttp/acme/live/<domain>/{fullchain.pem,privkey.pem}`, and legacy `~/.exphttp/letsencrypt` read behavior.

4. Mark `check_openssl_available()` / `check_certbot_available()` as legacy external-tool probes, or deprecate them. Avoid presenting them as TLS readiness checks.

5. Update MkDocs nav and stale top-level dependency claims. Add a docs-sync grep for `zero external`, `exphttp[crypto]`, `Optional cryptography`, `certbot subprocess`, and `OpenSSL not found`.

## Quick Wins

- Change the MkDocs ADR-003 label.
- Fix NOTE/WS/UI `exphttp[crypto]` strings.
- Add the missing `key_path.exists()` condition in `TLSManager`.
- Add one focused test for the missing ACME key cache case.

## Deeper Improvements

- Introduce a small storage-boundary manifest in docs and maybe startup output for all persistent locations, including ACME secrets.
- Consider a future `NotepadWebSocketTransport` extraction so `server.py` no longer calls handler-mixin WebSocket message methods directly.
- Decide whether package-root TLS helper exports are part of the public API before removing or renaming them.

## Open Questions

- Should `check_openssl_available()` remain public for backward compatibility, or move to a clearly named legacy/diagnostic namespace?
- Should ACME cache repair also validate corrupt private keys, not just missing keys?
- Should architecture docs document operational ownership of `~/.exphttp/acme` as user home state or allow overriding it for containers/services?
