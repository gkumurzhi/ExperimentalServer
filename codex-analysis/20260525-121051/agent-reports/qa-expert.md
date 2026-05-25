# qa-expert Report
_Generated: 2026-05-25 12:46:08 MSK_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260525-121051/analysis-plan.md_

## Summary

Scope analyzed: `analysis-plan.md`, all `tests/**/*.py`, named `tools/*` QA scripts, CI/security workflows, Docker files, and representative `src/` runtime paths for HTTP parsing, CORS, uploads, Notepad, WebSocket, TLS/ACME, auth, CLI, and package layout.

Static QA result: the test posture is strong for parser/framing, traversal, auth/crypto, Notepad contracts, WebSocket frame/admission limits, static UI packaging, stale-doc guards, and browser smoke. The main release-risk gaps are not generic coverage gaps; they map to missing or un-gated product behavior: aggregate disk exhaustion, always-on risky capabilities, no safe secret source, wildcard CORS mutation/WebSocket policy, protocol-aware Docker health, and risk-aligned coverage gates.

No files were modified. I did not run pytest, browser smoke, Docker, or ACME flows because this was requested as read-only analysis.

## Documentation Checks
- **pytest** `>=9.0` - Context7 topic checked: `pyproject.toml` discovery, `testpaths`, `python_files`, strict markers, marker-based selection; impact on recommendation: current discovery config is valid, so recommendations focus on adding risk-targeted tests and optional markers for long-running/env-specific checks, not changing discovery mechanics.
- **coverage.py** `unknown/current` - Context7 topic checked: TOML config, `branch = true`, `source`, XML reports, `--fail-under`; impact on recommendation: current branch/source setup is valid, but the global `65` threshold is not risk-aligned for critical server modules.
- **GitHub Actions** `unknown/current` - Context7 topic checked: matrix jobs, artifact upload/download, Python release/PyPI OIDC, artifact attestations; impact on recommendation: CI matrix and artifact upload patterns are sound, but release/smoke gates should become mode-aware before public distribution.

## Detailed Findings

Confirmed strong coverage areas:
- HTTP parser/framing: `tests/test_http/test_io.py` covers header caps, body caps, duplicate/conflicting `Content-Length`, and transfer encoding rejection.
- Path traversal and uploads-only scope: `tests/test_handlers/test_path_traversal.py`, `tests/test_http/test_path_traversal_prefix.py`, `tests/test_property/test_path_traversal.py`.
- WebSocket limits: `_MAX_FRAME_SIZE` in `src/websocket.py:16`, parser rejection in `src/websocket.py:187-188`, tests in `tests/test_security/test_websocket_frame_limit.py:32-54`, admission budget in `tests/test_server_live.py:364-412`.
- Notepad correctness: per-note limits in `tests/test_handlers/test_notepad.py:167-237` and WebSocket equivalents in `tests/test_websocket_handlers.py:339-411`; atomic write/recovery tests in `tests/test_handlers/test_notepad.py:265-321` and corrupt metadata fallback in `tests/test_handlers/test_notepad.py:720-780`.
- Browser smoke is representative for the unauthenticated local UI: it starts temporary servers in `tools/browser_smoke.py:134-232`, checks static assets and inspector APIs in `tools/browser_smoke.playwright.js:300-336`, advanced upload capability in `:338-423`, request method matrix including `DELETE`, `NOTE`, `SMUGGLE` in `:1307-1323`, opsec transport switching in `:2071-2245`, and Notepad normal/unavailable states in `:2750-2756` and `:2961-2983`.
- CI has useful breadth: Python 3.10-3.13 test matrix in `.github/workflows/ci.yml:17-63`, cross-platform subset in `:104-141`, static UI/browser/Docker smoke in `:143-246`, and security workflow with `pip-audit`/Bandit in `.github/workflows/security.yml:15-65`.

## Issues Found

- [HIGH] Aggregate storage exhaustion is not implemented or regression-tested
  - File/area: `src/server.py`, `src/handlers/files.py`, `src/handlers/advanced_upload.py`, `src/notepad_service.py`, `docs/threat-model.md`
  - Evidence: per-request upload cap defaults to 100 MB in `src/server.py:84`; `uploads/` and `notes/` are created separately in `src/server.py:206-212`; standard uploads write via `write_unique_file_exclusive` in `src/handlers/files.py:418-420`; advanced uploads write via `src/handlers/advanced_upload.py:385-387`; Notepad limits one blob in `src/notepad_service.py:313-337` but `list_notes()` scans all `*.enc` without count/total-byte cap in `src/notepad_service.py:390-401`; threat model says disk fill is mitigated by `--max-size` in `docs/threat-model.md:62`.
  - Detail: tests prove individual oversized requests are rejected, but there is no total quota, retention policy, backpressure, or regression test for repeated valid uploads/notes filling the data volume.
  - Impact: an authenticated user, lab peer, or misconfigured public instance can fill disk while every request remains below the configured per-request limit.
  - Confidence: high

- [MEDIUM] Tests lock in always-on high-risk capabilities instead of validating feature profiles
  - File/area: `src/server.py`, `src/cli.py`, `src/handlers/__init__.py`, live/method tests
  - Evidence: `advanced_upload_enabled = True` in `src/server.py:148`; `--advanced-upload` is a deprecated no-op in `src/cli.py:90-93`; handler registry always registers `DELETE`, `NOTE`, `SMUGGLE`, and advanced fallback in `src/handlers/__init__.py:36-65`; tests assert advanced upload is enabled without mode flags in `tests/test_server_live.py:269-345` and unknown methods upload by default in `tests/test_server_methods.py:177-214`.
  - Detail: this is not a missing test for current behavior; the suite codifies the risky default. There is no QA matrix for a safe file-server profile because there is no profile/feature-gate implementation to test.
  - Impact: operators cannot run a least-privilege mode that disables advanced upload, `SMUGGLE`, `DELETE`, or `NOTE`; future profile work could regress without explicit positive/negative tests.
  - Confidence: high

- [MEDIUM] Secret-source behavior is recommended in docs but not supported or tested
  - File/area: `src/cli.py`, `src/server.py`, `tests/test_cli.py`, `SECURITY.md`, `examples/docker/docker-compose.yml`
  - Evidence: CLI only accepts `--auth CREDS` in `src/cli.py:171-177` and passes it directly in `src/cli.py:242-268`; server supports only `random`, `user:pass`, or username-generated password in `src/server.py:220-236`; tests only cover `--auth random` and `--auth admin:secret` in `tests/test_cli.py:117-123` and config propagation in `tests/test_cli.py:235-263`; docs recommend a secret manager in `SECURITY.md:90-95`, while Compose comments still show `admin:replace-with-a-strong-secret` in `examples/docker/docker-compose.yml:27-40`.
  - Detail: there is no `--auth-file`, stdin, or secret-mount path, so QA cannot validate safe secret loading, precedence, trimming, missing-file failure, or redaction.
  - Impact: service credentials can leak through shell history, process arguments, Compose files, and operational copy/paste.
  - Confidence: high

- [MEDIUM] Wildcard CORS authorizes browser mutations and WebSocket origins
  - File/area: `src/http/cors.py`, `src/server.py`, `tests/test_server_methods.py`
  - Evidence: wildcard parses to `("*",)` in `src/http/cors.py:83-86` and resolves as `*` in `src/http/cors.py:95-99`; mutation checks allow wildcard in `src/server.py:777-782` and `src/server.py:803-805`; WebSocket origin checks allow wildcard in `src/server.py:834-841`; tests explicitly assert cross-origin WebSocket wildcard allow in `tests/test_server_methods.py:289-304` and cross-origin mutation wildcard allow in `tests/test_server_methods.py:507-521`.
  - Detail: default rejection is tested, but wildcard is treated as full write/WS opt-in rather than read-only CORS. That may be intentional for a lab server, but it is a high-blast-radius setting.
  - Impact: one `--cors-origin *` deployment can allow arbitrary browser origins to trigger state-changing uploads/notes/WebSocket flows.
  - Confidence: high

- [MEDIUM] Docker health/smoke coverage does not represent auth/TLS/ACME modes
  - File/area: `Dockerfile`, `examples/docker/docker-compose.yml`, `.github/workflows/ci.yml`
  - Evidence: image healthcheck always probes plain HTTP `PING` at `Dockerfile:61-64`; Compose warns TLS/auth needs override/disable in `examples/docker/docker-compose.yml:27-42`; ACME profile disables healthcheck in `examples/docker/docker-compose.yml:96-99`; CI Docker smoke probes HTTP and TLS with curl in `.github/workflows/ci.yml:224-246` but does not inspect Docker health status or auth-enabled health behavior.
  - Detail: the Docker smoke proves the image starts and serves plain/TLS `PING`, but not that container health semantics work for the modes documented for operators.
  - Impact: real deployments can be falsely unhealthy or falsely healthy when auth/TLS/ACME are enabled.
  - Confidence: high

- [MEDIUM] TLS/ACME lifecycle verification is startup-only
  - File/area: `src/security/tls_manager.py`, `tests/test_security/test_tls_manager.py`
  - Evidence: certificate acquisition/build happens in `TLSManager.setup()` at `src/security/tls_manager.py:71-89`; ACME cache/renewal decisions occur in `_try_letsencrypt()` at `src/security/tls_manager.py:99-153`; tests cover fresh cache, renewal, invalid cache, sslip, and failure paths in `tests/test_security/test_tls_manager.py:121-597`.
  - Detail: unit coverage is strong for startup decisions, but there is no long-running renewal/reload behavior to validate. If the intended deployment model is restart-before-expiry, that needs an explicit release gate or operator check.
  - Impact: long-running services can drift toward certificate expiry without a tested renewal/reload path.
  - Confidence: medium

- [LOW] Coverage gate is global and weak for the critical risk surface
  - File/area: `pyproject.toml`, `.github/workflows/ci.yml`
  - Evidence: coverage measures `source = ["src"]` with branch coverage in `pyproject.toml:103-108`; CI enforces only `--cov-fail-under=65` in `.github/workflows/ci.yml:61-62`.
  - Detail: a global threshold can pass while important branches in `server.py`, `request_pipeline.py`, `http/io.py`, `handlers/*`, `notepad_service.py`, or `security/*` lose coverage.
  - Impact: silent regressions in security-sensitive modules can pass if total project coverage remains above 65%.
  - Confidence: high

- [LOW] End-user package/import migration is only partially represented
  - File/area: `pyproject.toml`, `tests/test_import_boundaries.py`, CI smoke
  - Evidence: package entry point is `exphttp = "src.cli:main"` in `pyproject.toml:47-48`; package discovery includes `src*` in `pyproject.toml:77-88`; import boundary tests use `import src` in `tests/test_import_boundaries.py:23-75`; CI builds a wheel and checks static assets in `.github/workflows/ci.yml:170-176` but does not install the wheel in an isolated environment and run `exphttp --help` from that install.
  - Detail: current tests are useful for the existing `src` package, but they do not protect an eventual public `exphttp` import/package rename path.
  - Impact: package layout or import migration could break installed-user behavior while editable-install tests still pass.
  - Confidence: high

## Concrete Recommendations

1. Add aggregate storage controls before more feature work:
   - Normal path: upload/note saves under a configured total cap succeed.
   - Failure path: over-cap save returns `413`/clear error and writes nothing.
   - Integration edge: mixed `uploads/` plus `notes/` accounting behaves predictably and `list_notes()` remains bounded.

2. Introduce a minimal feature profile/gate, then test it:
   - Normal path: default/current profile keeps existing behavior.
   - Failure path: safe profile rejects `SMUGGLE`, advanced unknown-method upload, `NOTE`, and destructive `DELETE`.
   - Integration edge: browser smoke or API smoke verifies safe profile still serves GET/PING/static UI as intended.

3. Add a safe auth secret source:
   - Prefer `--auth-file` or mounted secret file for containers.
   - Test precedence, missing/unreadable file, newline trimming, invalid format, and no secret leakage to stdout/stderr.

4. Decide wildcard CORS policy:
   - Safer minimum: allow `*` for read-only CORS responses, reject it for browser mutations and WebSocket upgrades.
   - Add negative regression tests mirroring the existing wildcard-allow tests.

5. Make Docker smoke mode-aware:
   - Check `docker inspect` health for default HTTP.
   - Add auth-enabled container smoke with a matching healthcheck override.
   - Add TLS healthcheck override or assert healthcheck is intentionally disabled for TLS/ACME examples.

## Quick Wins

- Add a test that documents the current aggregate storage gap as `xfail` or pending until quota exists, so it stays visible.
- Add pytest markers such as `integration`, `docker`, `browser`, `slow` for mode-specific gates; current pytest config supports this pattern.
- Add isolated wheel install smoke: build wheel, install into temp venv, run `exphttp --help`, `exphttp --version`, and a minimal import probe.
- Add CI artifact upload for the browser smoke JSON result to make failures easier to triage.

## Deeper Improvements

- Replace global-only coverage confidence with risk-targeted gates for critical modules or a required test manifest mapped to HTTP parser, CORS, upload storage, Notepad, WebSocket, TLS/ACME, Docker, and CLI auth.
- Define the Notepad product contract: ephemeral encrypted scratchpad vs durable recoverable notes. Current docs explicitly say keys are session-bound and not recoverable in `API.md:405`; tests match that, but browser/server-restart UX should be gated if durability becomes a goal.
- Add release supply-chain gates if public distribution is planned: SBOM/image scan, artifact attestation, and provenance-aware publish workflow.

## Open Questions

- Is internet-facing operation a supported release target, or only localhost/trusted lab?
- Should storage limits be per directory, combined root total, or configurable by feature?
- Which secret source should be canonical for services: file, env var, stdin, or orchestrator secret mount?
- Should `--cors-origin *` remain a full mutation/WebSocket opt-in, or become read-only only?
- Is Notepad intended to be intentionally ephemeral, or should recoverability/re-keying become a release requirement?
