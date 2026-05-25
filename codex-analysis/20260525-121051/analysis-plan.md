# Project Analysis Plan
_Generated: 2026-05-25 12:17:30 MSK_

## Stack Summary

`exphttp` is a Python 3.10-3.13 package and CLI for an experimental HTTP/WebSocket server. The runtime code is under a package currently named `src`, with the CLI entry point `exphttp = src.cli:main`.

Primary stack:

- Python package built by Setuptools (`pyproject.toml`) with dynamic version from `src.config.__version__`.
- Runtime dependencies: `cryptography>=48.0`, `acme>=5.5,<6`, `josepy>=2.2,<3`.
- Server model: raw sockets, `ThreadPoolExecutor`, custom HTTP parser, custom method registry, streamed GET/FETCH responses, built-in static UI.
- Security features: Basic Auth with PBKDF2-SHA256, request size/header caps, path containment under `uploads/`, CORS/browser-origin mutation guard, TLS/self-signed/ACME, ECDH/AES-GCM Secure Notepad, advanced upload HMAC/AES/XOR support.
- State: `<root>/uploads/` for file operations, `<root>/notes/` for encrypted Notepad blobs and plaintext metadata, `~/.exphttp/acme` for ACME account/domain keys and cert cache.
- Frontend: static HTML/CSS/JS packaged under `src/data`, browser smoke via Playwright CLI wrapper, CSP with `script-src 'self'` and current `style-src 'self' 'unsafe-inline'`.
- Test/quality: pytest, pytest-cov, Hypothesis property tests, ruff, mypy strict, pre-commit, GitHub Actions matrix for Python 3.10-3.13 and cross-platform smoke.
- Deployment: multi-stage Dockerfile pinned to a Python 3.12 slim digest, non-root runtime user, Docker healthcheck, Compose examples with `read_only`, `tmpfs`, `cap_drop`, and ACME profile.
- Docs: README/API/SECURITY/ADR/MkDocs, semantic stale-doc guard scripts, previous implementation plans in `implementation-plan/`.

## Project Structure Overview

Top-level boundaries:

- `src/` - application/runtime code. Important submodules:
  - `src/server.py` - socket lifecycle, worker admission, keep-alive, WebSocket loop, CORS/origin decisions.
  - `src/request_pipeline.py` - parse/auth/origin/size/dispatch/send orchestration.
  - `src/http/` - request parsing, response building, CORS helpers, receive-layer IO, path utilities.
  - `src/handlers/` - method handlers for file ops, INFO/PING, NOTE, advanced upload, SMUGGLE.
  - `src/security/` - Basic Auth, crypto, ECDH keys, TLS/ACME helpers and manager.
  - `src/data/` - packaged browser UI assets.
- `tests/` - unit/integration/property/live tests. Strong coverage around HTTP parsing, traversal, auth/crypto/TLS, WebSocket, metrics, server methods, and UI redaction.
- `tools/` - release and verification utilities: docs sync/staleness, dependency constraints check, browser smoke, static UI package-data check, decrypt tool.
- `.github/` - CI, security scanning, Dependabot, PR template.
- `docs/`, `API.md`, `SECURITY.md`, `README.md`, `CHANGELOG.md` - public docs and mirrored MkDocs content.
- `examples/` - shell/client/Compose examples.
- `constraints/ci.txt` - pinned CI/tool/runtime constraints.
- `implementation-plan/` and old `codex-analysis/` - generated planning/audit history; sampled only for active-plan context, not treated as source code.

Omitted from exhaustive traversal: `.git/`, `.codex/`, `.agents/`, `.venv/`, caches, `build/`, `dist/`, `site/`, `__pycache__/`, generated old analysis reports, and runtime data. Secret-heavy files were skipped.

## Reconnaissance Coverage

Read or inspected directly:

- Project guidance/docs: `README.md`, `API.md`, `CLAUDE.md`, `SECURITY.md`, `CHANGELOG.md`, `docs/architecture.md`, `docs/threat-model.md`, ADR-002 and ADR-003, active implementation-plan status/findings.
- Manifests/configs: `pyproject.toml`, `constraints/ci.txt`, `.pre-commit-config.yaml`, `.gitignore`, `.dockerignore`, `mkdocs.yml` sampled through docs/tool references.
- CI/CD/security: `.github/workflows/ci.yml`, `.github/workflows/security.yml`, `.github/dependabot.yml`.
- Deployment: `Dockerfile`, `examples/docker/docker-compose.yml`.
- Core backend: `src/server.py`, `src/request_pipeline.py`, `src/http/io.py`, `src/http/request.py`, `src/http/response.py`, `src/http/utils.py`, `src/http/cors.py`.
- Handlers: `src/handlers/__init__.py`, `base.py`, `files.py`, `info.py`, `registry.py`, `advanced_upload.py`, `notepad.py`, `smuggle.py`.
- Security/runtime: `src/security/auth.py`, `crypto.py`, `keys.py`, `tls.py`, `tls_manager.py`, `src/websocket.py`, `src/notepad_service.py`, package `__init__.py` files.
- Frontend samples: `src/data/index.html`, `src/data/static/ui/core.js`, `dialogs.js`, `files.js`, `inspector.js`, `upload.js`, `opsec.js`, `notepad.js`.
- Tests/tools samples: `tests/conftest.py`, `tests/test_http/test_io.py`, `tests/test_security/test_websocket_upgrade.py`, `tests/test_websocket.py`, `tests/test_request_pipeline.py`, `tests/test_import_boundaries.py`, `tools/check_static_ui_assets.py`, `tools/browser_smoke.py`, `tools/browser_smoke.playwright.js`, `tools/check_stale_docs.py`, `tools/check_dependency_constraints.py`.
- High-signal searches: TODO/FIXME, broad exception handling, `innerHTML`, `localStorage`, CORS headers, `shell=True`, TLS verification bypass, `type: ignore`, `noqa`, auth/password/secret/rate-limit, quota/retention/disk, version/package references.

Static counts from non-cache source areas:

- `118` files under `src`, `tests`, `docs`, `examples`, `tools` excluding `__pycache__`.
- `33` Python source files under `src` excluding `__pycache__`.
- `34` test files matching `tests/**/test_*.py` excluding `__pycache__`.

Not run during Phase 1:

- No pytest, mypy, ruff, browser smoke, Docker build, or networked ACME flows were executed. This phase stayed static/read-only except generated analysis artifacts.

## Context7 Documentation Checks

- **Setuptools** `>=75.0` - checked: package discovery, src-layout, package-data patterns; impact: current config (`where = ["."]`, package named `src`) should be reviewed before deeper library development because Setuptools documentation favors explicit source layout with `where = ["src"]` / `package-dir` and project-named packages.
- **Docker** `docs current` - checked: production Dockerfile security practices; impact: Dockerfile/Compose already align with non-root and read-only runtime guidance, but the audit should verify secrets, protocol-aware healthchecks, resource limits, and release image policy.
- **pytest** `9.x` - checked: discovery, `collect_ignore`, cache behavior, and CI discovery practices; impact: `collect_ignore` in `tests/conftest.py` is a valid pytest mechanism, and follow-up should focus on coverage/risk gaps rather than discovery mechanics.

## Observed Problems & Risks

- [HIGH] No total storage quota, retention, or backpressure for accumulated `uploads/` and `notes/`.
  - Evidence: per-request default upload cap is 100 MB in `src/server.py:84`; upload writes call `write_unique_file_exclusive(self.upload_dir / safe_filename, request.body)` in `src/handlers/files.py:418-419`; Notepad limits individual encrypted blobs in `src/notepad_service.py:313-330` but `list_notes()` scans all `*.enc` without count/total-byte caps in `src/notepad_service.py:390-401`; `docs/threat-model.md` frames disk-fill mitigation as `--max-size`, which is per request.
  - Risk: an authenticated user, lab peer, or misconfigured exposed instance can fill disk over repeated writes even when individual requests respect caps.

- [HIGH] High-risk demo capabilities are always present and lack coarse feature gating.
  - Evidence: `self.advanced_upload_enabled = True` in `src/server.py:148`; CLI `--advanced-upload` is documented as a deprecated no-op in `src/cli.py:90-94` and `README.md:163`; handlers expose deletion, `SMUGGLE`, advanced unknown-method upload, and Notepad when auth permits.
  - Risk: before operational use, operators cannot disable advanced upload/SMUGGLE/DELETE/NOTE to run a least-privilege file-serving profile.

- [HIGH] Secret injection story is operationally incomplete.
  - Evidence: CLI only accepts `--auth CREDS` as a command argument in `src/cli.py:171-177` and passes it directly into server config at `src/cli.py:264`; docs recommend secret-manager credentials in `SECURITY.md:91-93`, while Compose examples still show command-line `admin:replace-with-a-strong-secret` at `examples/docker/docker-compose.yml:31-40`.
  - Risk: service credentials can leak via shell history, process args, Compose files, logs, or operator copy/paste. A production-ready mode needs environment/file/stdin/secret mount handling with redaction.

- [MEDIUM] CORS wildcard is allowed to authorize browser mutations and WebSocket origins.
  - Evidence: `parse_cors_origins("*")` returns `("*",)` in `src/http/cors.py:83-86`; response CORS emits wildcard at `src/http/cors.py:95-99`; mutating browser requests and WebSockets accept wildcard at `src/server.py:803-805` and `src/server.py:840-841`; docs warn against it in `README.md:216-217` and `SECURITY.md:97-98`.
  - Risk: one operator typo can intentionally or accidentally permit browser-origin state changes from any site. Before broader operation, wildcard should likely be disallowed for mutation/WebSocket admission even if still allowed for read-only CORS.

- [MEDIUM] Package/import layout uses a top-level package named `src`, which is fragile for further development as a library.
  - Evidence: project name is `exphttp` in `pyproject.toml:6`, script entry is `src.cli:main` in `pyproject.toml:47-48`, package discovery uses `where = ["."]` and `include = ["src*"]` in `pyproject.toml:77-80`, and public imports are `from src import ...` in docs/examples.
  - Risk: package name collides with the generic `src` convention, makes downstream imports awkward, and raises migration cost as public APIs grow.

- [MEDIUM] ACME/TLS lifecycle is startup-bound and healthchecks are not protocol-aware by default.
  - Evidence: TLS acquisition/build happens in `TLSManager.setup()` at `src/security/tls_manager.py:71-89`; renewal decisions happen during `_try_letsencrypt()` at `src/security/tls_manager.py:99-153`; Dockerfile healthcheck probes plain HTTP PING at `Dockerfile:61-64`; ACME Compose profile disables healthcheck at `examples/docker/docker-compose.yml:96-99`.
  - Risk: long-running services need renewal scheduling, reload/restart guidance, and health probes that reflect TLS/auth modes.

- [MEDIUM] Operational auth/rate limiting is simple and proxy-unaware.
  - Evidence: auth limiter is in-memory per client IP in `src/security/auth.py:183-210`; request auth uses `client_address[0]` in `src/server.py:629-650`.
  - Risk: behind a reverse proxy all clients may collapse to the proxy IP unless the deployment handles rate limiting externally. The current model is fine for local/trusted lab, but not sufficient as a public control plane.

- [MEDIUM] Notepad has an explicit recoverability/product decision that blocks treating it as durable secure notes.
  - Evidence: `API.md:405-407` states current keys are process/session-bound and page reload, client/server restart, session expiry, or LRU eviction can make note bodies undecryptable by that client.
  - Risk: this is acceptable for experiments, but before further product development the team must decide whether Notepad is ephemeral encrypted scratchpad or durable encrypted storage with backup/re-key UX.

- [MEDIUM] Release/supply-chain posture is good for CI but incomplete for public distribution.
  - Evidence: CI matrix, pinned constraints, static UI gates, browser smoke, pip-audit, Bandit, Dependabot, and Docker smoke are present; no SBOM, provenance/signing, release publishing workflow, or artifact attestation was found in `.github/workflows/`.
  - Risk: acceptable for internal development, weaker for distributing an HTTP/security-adjacent server.

- [LOW] Documentation is generally strong, but some examples still normalize risky commands.
  - Evidence: README quick examples include explicit `--auth admin:secretpassword` and `--auth admin:pass` at `README.md:192-199`, while later text correctly warns about secret storage and external exposure.
  - Risk: examples can be copied into service manifests without a safer secret source.

- [LOW] Generated/local artifacts are present in the worktree but ignored.
  - Evidence: `find` saw `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`, `build/`, `dist/`, `site/`, `.playwright-*`, and old generated plans/reports. `.gitignore` and `.dockerignore` largely exclude them.
  - Risk: low code risk, but audit/release tooling should keep ignoring generated runtime and analysis artifacts.

## Selected Agents

### Must Run
- **security-auditor** - Verify auth, CORS wildcard mutation behavior, advanced upload, SMUGGLE, Notepad crypto/session assumptions, TLS/ACME, path containment, and secret-handling risks.
- **architect-reviewer** - Evaluate whether the current package/module shape, handler mixin registry, feature exposure model, and operational boundary are fit for further development.
- **python-pro** - Review Python packaging/import layout, IO/storage semantics, exception surfaces, typing contracts, and runtime edge cases.
- **devops-engineer** - Review CI/security workflow, constraints, Dependabot, release gates, deployment lifecycle, and artifact/release process.
- **performance-engineer** - Review worker admission, socket timeouts, streaming, gzip, WebSocket loops, memory/disk pressure, and quota/retention gaps.
- **qa-expert** - Map test coverage to the risk surface and identify missing regression/e2e/property tests before further development.

### High Value
- **docker-expert** - Review Dockerfile and Compose profiles against current runtime hardening, healthcheck, resource limit, secret mount, and ACME needs.
- **websocket-engineer** - Review `/notes/ws`, frame parser, reconnect/idempotency assumptions, session lifecycle, and resource exhaustion controls.
- **dependency-manager** - Review `pyproject.toml`, `constraints/ci.txt`, security scans, dependency ranges, update workflow, and package-data policy.
- **frontend-developer** - Review packaged static UI, CSP assumptions, `innerHTML` usage, redaction, browser smoke coverage, and accessibility-adjacent issues.

### Worth Running
- **documentation-engineer** - Verify README/API/SECURITY/ADR/operator docs against implementation and risk posture.
- **api-documenter** - Check API contracts, error-body consistency, metrics, NOTE/WebSocket behavior, and public examples.
- **reviewer** - Final cross-cutting review after domain agents to catch contradictions, missing tests, and over/under-ranked findings.

## Execution Strategy

Parallel batch 1, max 6 agents:

- `security-auditor`
- `architect-reviewer`
- `python-pro`
- `devops-engineer`
- `performance-engineer`
- `qa-expert`

Parallel batch 2, max 6 agents after batch 1:

- `docker-expert`
- `websocket-engineer`
- `dependency-manager`
- `frontend-developer`
- `documentation-engineer`
- `api-documenter`

Sequential chain after both parallel batches:

- `reviewer`

The reviewer should receive the saved reports from all prior agents and focus on deduplication, severity calibration, contradictions, and missing verification.

## Focus Areas Per Agent

### security-auditor
- Relevant paths:
  - `src/server.py`
  - `src/request_pipeline.py`
  - `src/security/auth.py`
  - `src/security/crypto.py`
  - `src/security/keys.py`
  - `src/security/tls.py`
  - `src/security/tls_manager.py`
  - `src/http/cors.py`
  - `src/http/io.py`
  - `src/http/request.py`
  - `src/http/utils.py`
  - `src/handlers/files.py`
  - `src/handlers/advanced_upload.py`
  - `src/handlers/notepad.py`
  - `src/handlers/smuggle.py`
  - `src/notepad_service.py`
  - `src/websocket.py`
  - `SECURITY.md`
- Questions:
  - Is external exposure safe enough for the documented trusted-lab/external modes?
  - Should wildcard CORS be blocked for mutations and WebSocket upgrade even if allowed for read-only responses?
  - Are Basic Auth, rate limiting, secret handling, and reverse-proxy assumptions operationally safe?
  - Do advanced upload, SMUGGLE, DELETE, and NOTE need feature flags or role/method authorization?
- Known risks to verify:
  - Storage exhaustion through repeated uploads/notes.
  - Command-line credential leakage.
  - Browser-origin mutation wildcard.
  - Notepad recoverability/security expectations.

### architect-reviewer
- Relevant paths:
  - `pyproject.toml`
  - `src/__init__.py`
  - `src/__main__.py`
  - `src/server.py`
  - `src/request_pipeline.py`
  - `src/handlers/__init__.py`
  - `src/handlers/registry.py`
  - `docs/architecture.md`
  - `docs/ADR/`
- Questions:
  - Is the `src` package name acceptable for future public API development?
  - Are handler mixins and `RequestPipeline` boundaries still coherent as features grow?
  - Should feature profiles replace the current always-on capability set?
  - What architecture should separate experimental/offensive demos from safer file-server operation?
- Known risks to verify:
  - Package rename migration cost.
  - All-or-nothing auth/feature surface.
  - Cross-module state owned by `ExperimentalHTTPServer`.

### python-pro
- Relevant paths:
  - `pyproject.toml`
  - `src/**/*.py`
  - `tests/**/*.py`
  - `tools/*.py`
- Questions:
  - Are package discovery/package-data settings robust and aligned with Setuptools guidance?
  - Are exception handling and error contracts predictable across parser/receive/handler layers?
  - Are write paths atomic enough and do they handle partial failure consistently?
  - Are type annotations and strict mypy assumptions honest around Protocols and lazy exports?
- Known risks to verify:
  - Generic `src` package name.
  - Public imports and CLI entry points.
  - Broad `except Exception` in request/WebSocket/handler paths.

### devops-engineer
- Relevant paths:
  - `.github/workflows/ci.yml`
  - `.github/workflows/security.yml`
  - `.github/dependabot.yml`
  - `.pre-commit-config.yaml`
  - `constraints/ci.txt`
  - `tools/check_dependency_constraints.py`
  - `tools/check_static_ui_assets.py`
  - `tools/check_stale_docs.py`
  - `tools/sync_docs.py`
  - `Dockerfile`
- Questions:
  - Are CI gates sufficient before merging and release?
  - Should security scanning cover SBOM/provenance, wheel contents, container image scanning, and artifact signing?
  - Is constraints refresh policy documented and enforceable?
  - Are browser/Docker smoke checks stable and representative?
- Known risks to verify:
  - No release/publish workflow found.
  - No SBOM/provenance/signing found.
  - Coverage gate currently 65%.

### performance-engineer
- Relevant paths:
  - `src/server.py`
  - `src/http/io.py`
  - `src/http/response.py`
  - `src/handlers/files.py`
  - `src/handlers/advanced_upload.py`
  - `src/notepad_service.py`
  - `src/websocket.py`
  - `src/metrics.py`
  - `tests/test_server_live.py`
  - `tests/test_server_methods.py`
- Questions:
  - Can accepted connections or WebSockets still pin workers/resources under slow clients?
  - Are upload, advanced upload, SMUGGLE, and Notepad memory/disk limits sufficient?
  - Are metrics enough to detect pressure before outage?
  - Are streamed and buffered response paths correctly bounded?
- Known risks to verify:
  - No accumulated storage quota.
  - 300-second body timeout occupying worker.
  - SMUGGLE generates temporary HTML from file contents.

### qa-expert
- Relevant paths:
  - `tests/`
  - `tools/browser_smoke.py`
  - `tools/browser_smoke.playwright.js`
  - `tools/check_static_ui_assets.py`
  - `.github/workflows/ci.yml`
  - `pyproject.toml`
- Questions:
  - Which high-risk behaviors lack targeted tests?
  - Is 65% coverage acceptable for the current security-adjacent server?
  - Do browser smoke tests cover a11y-critical and failure-path behavior?
  - Are Docker/TLS/auth/CORS modes covered enough?
- Known risks to verify:
  - No full test run in Phase 1.
  - Operational secret-source/feature-profile behavior absent, so no tests exist.

### docker-expert
- Relevant paths:
  - `Dockerfile`
  - `.dockerignore`
  - `examples/docker/docker-compose.yml`
  - `.github/workflows/ci.yml`
  - `SECURITY.md`
- Questions:
  - Does the container follow current hardening guidance beyond non-root/read-only examples?
  - Are secrets, ACME state, healthchecks, resource limits, and volume permissions safe?
  - Should default image command run HTTP on `0.0.0.0`?
- Known risks to verify:
  - Plain HTTP default image command.
  - Auth/TLS healthcheck mismatch.
  - Compose command examples with credentials.

### websocket-engineer
- Relevant paths:
  - `src/websocket.py`
  - `src/server.py`
  - `src/handlers/notepad.py`
  - `src/notepad_service.py`
  - `src/data/static/ui/notepad.js`
  - `tests/test_websocket.py`
  - `tests/test_websocket_handlers.py`
  - `tests/test_security/test_websocket_frame_limit.py`
  - `tests/test_security/test_websocket_upgrade.py`
- Questions:
  - Are frame parsing, masking, size, fragmentation, close-code, and timeout rules correct?
  - Is reconnection/idempotent save robust under disconnect/race conditions?
  - Are WebSocket resource limits enough under slow or malicious clients?
- Known risks to verify:
  - Session state audit-only semantics.
  - Incomplete frame timeout and active slot behavior.
  - Origin wildcard acceptance.

### dependency-manager
- Relevant paths:
  - `pyproject.toml`
  - `constraints/ci.txt`
  - `.github/dependabot.yml`
  - `.github/workflows/security.yml`
  - `.pre-commit-config.yaml`
  - `tools/check_dependency_constraints.py`
- Questions:
  - Are dependency version ranges and constraints consistent?
  - Does `pip-audit --no-deps -r constraints/ci.txt` cover the intended package set?
  - Are transitive runtime dependencies pinned for CI and compatible with package metadata?
  - Is a constraints refresh process missing?
- Known risks to verify:
  - Runtime ranges are broad while CI pins exact versions.
  - No SBOM/provenance workflow found.

### frontend-developer
- Relevant paths:
  - `src/data/index.html`
  - `src/data/static/ui/*.js`
  - `src/data/static/ui/*.css`
  - `tools/browser_smoke.playwright.js`
  - `tools/check_static_ui_assets.py`
  - `tests/test_ui_inspector_redaction.py`
- Questions:
  - Are all `innerHTML` uses fed escaped/trusted content?
  - Is CSP compatible with current UI and tight enough for an HTTP file server?
  - Are redaction and clipboard behavior safe for keys, auth, and advanced upload payloads?
  - Are accessibility states and keyboard flows covered?
- Known risks to verify:
  - Many custom UI flows and `innerHTML` renderers.
  - Current CSP still needs inline styles.

### documentation-engineer
- Relevant paths:
  - `README.md`
  - `API.md`
  - `SECURITY.md`
  - `CONTRIBUTING.md`
  - `docs/`
  - `examples/`
  - `tools/check_stale_docs.py`
  - `tools/sync_docs.py`
- Questions:
  - Do docs correctly answer "what must be fixed before further development and operation"?
  - Are risky examples framed safely?
  - Do generated docs mirror source docs without drift?
  - Are operational runbooks missing?
- Known risks to verify:
  - CLI examples with inline credentials.
  - Strong warnings exist but safer secret-source feature is absent.

### api-documenter
- Relevant paths:
  - `API.md`
  - `src/handlers/*.py`
  - `src/request_pipeline.py`
  - `src/http/response.py`
  - `src/websocket.py`
  - `tests/test_request_pipeline.py`
  - `tests/test_server_methods.py`
- Questions:
  - Are response bodies/statuses/header contracts consistent and documented?
  - Which receive-layer failures intentionally close without bodies?
  - Are metrics and NOTE/WebSocket contracts stable enough for clients?
- Known risks to verify:
  - Mixed legacy text/empty/JSON errors documented but operationally awkward.
  - Direct guard responses may lack `X-Request-Id`.

### reviewer
- Relevant paths:
  - All saved agent reports under `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260525-121051/agent-reports`
  - `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260525-121051/analysis-plan.md`
- Questions:
  - Which findings are duplicates or severity-misaligned?
  - What are the minimum pre-development and pre-operation action lists?
  - Which findings need runtime verification rather than static confidence?
- Known risks to verify:
  - Domain agents may over-focus on their area and under-rank cross-cutting operation blockers.
