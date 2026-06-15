# Project Analysis Plan
_Generated: 2026-06-14 23:14:07 Europe/Moscow_

## Stack Summary

ExperimentalHTTPServer is a Python package and CLI published as `exphttp`.

- Runtime language: Python, declared as `>=3.10,<3.14` in `pyproject.toml`.
- Packaging: setuptools build backend, wheel/sdist build path, public `exphttp` package with compatibility implementation under `src`.
- Runtime dependencies: `acme`, `cryptography`, `josepy`.
- Test and quality stack: `pytest`, `pytest-cov`, `hypothesis`, `pytest-benchmark`, `ruff`, strict `mypy`.
- Documentation: MkDocs Material plus generated mirror checks for top-level docs.
- Infrastructure: Docker multi-stage image from pinned `python:3.12-slim` digest, non-root runtime user, healthcheck, Compose examples, GitHub Actions CI/security/release workflows.
- Frontend/product surface: static bundled UI under `src/data/static/ui`; no SPA framework, no Node build pipeline.
- Data/storage: local filesystem only. User-visible uploads live under `uploads/`; encrypted notepad blobs live under top-level `notes/`; temporary SMUGGLE pages live under `uploads/`.
- Network/security surface: custom HTTP methods, TLS/ACME, Basic Auth, auth-file support, CORS policy, browser-origin mutation guard, WebSocket `/notes/ws`, profile-gated capabilities.
- Observability: in-memory metrics exposed through `PING` and `GET /metrics`; no Prometheus/OpenTelemetry exporter or alert/runbook layer.
- No database, cache, queue, background worker system, ML, or external service dependency beyond optional ACME interactions.

The last implementation plan, `implementation-plan/20260525-133607`, is fully closed. That means the next useful work is no longer "finish the previous HIGH findings"; it is choosing the next product and operational direction for the tool.

## Project Structure Overview

- `exphttp/` - public package shims and import surface for the CLI/module identity.
- `src/` - implementation package:
  - `src/server.py` owns socket lifecycle, keep-alive handling, request admission, auth/CORS checks, WebSocket admission, runtime limits, metrics, and startup output.
  - `src/features.py` defines named capability profiles. `DEFAULT_PROFILE = "lab"` and profiles are `serve`, `workspace`, `lab`.
  - `src/request_pipeline.py`, `src/http/*` own HTTP parsing, response rendering, IO limits, content-length validation, and CORS helpers.
  - `src/handlers/*` owns method handlers for files, info, advanced upload, SMUGGLE, and NOTE.
  - `src/notepad_service.py` contains transport-independent Secure Notepad storage and quota logic.
  - `src/security/*` owns Basic Auth, TLS, crypto helpers, ECDH key/session management.
  - `src/websocket.py` owns pure-Python RFC 6455 frame and handshake helpers.
  - `src/data/static/ui/*` owns the bundled browser UI.
- `tests/` - unit, property, live-server, security, HTTP, handler, WebSocket, CLI, metrics, and tooling tests.
- `tools/` - project guards and smoke tooling, including docs sync, stale-doc checks, static UI asset checks, browser smoke, dependency constraints checks.
- `.github/workflows/` - CI, scheduled security audit, release artifact/provenance lane.
- `docs/`, top-level `README.md`, `API.md`, `SECURITY.md`, `CHANGELOG.md`, `examples/` - user, operator, API, and release-facing docs.
- `implementation-plan/` - previous stage-based remediation plans. The active plan pointer targets `implementation-plan/20260525-133607`, whose 11 stages are all `CLOSED`.
- `codex-analysis/` - generated audit artifacts only.

Generated/dependency/cache directories were excluded from exhaustive traversal, including `.git`, `.venv`, `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`, browser capture caches, and generated analysis outputs except the active run directory.

## Reconnaissance Coverage

Read or inspected:

- Project metadata and dependency policy: `pyproject.toml`, `constraints/ci.txt`, lockfile signals.
- Public docs: `README.md`, `API.md`, `SECURITY.md`, `CHANGELOG.md`, `docs/architecture.md`, `docs/threat-model.md`, `mkdocs.yml`, `examples/README.md`.
- Current and prior planning artifacts: `implementation-plan/ACTIVE_PLAN.md`, `implementation-plan/20260525-133607/*`, stage reports, stage status, backlog/risks/decisions, previous source analysis references.
- Core runtime code: `src/features.py`, `src/server.py`, `src/request_pipeline.py`, `src/http/io.py`, `src/http/request.py`, `src/http/response.py`, `src/http/cors.py`, `src/http/utils.py`, `src/metrics.py`, `src/storage.py`.
- Handler and domain code: `src/handlers/files.py`, `src/handlers/advanced_upload.py`, `src/handlers/notepad.py`, `src/handlers/smuggle.py`, `src/handlers/registry.py`, `src/notepad_service.py`, `src/websocket.py`.
- Security code: `src/security/auth.py`, `src/security/crypto.py`, `src/security/keys.py`, `src/security/tls.py`, `src/security/tls_manager.py`.
- Package shims: `exphttp/*`.
- CI/release/security/ops: `.github/workflows/ci.yml`, `.github/workflows/security.yml`, `.github/workflows/release.yml`, `Dockerfile`, Compose docs/examples.
- Test topology: `tests/test_http`, `tests/test_handlers`, `tests/test_security`, property tests, live-server tests, WebSocket tests, CLI and tooling tests.
- Tooling validation:
  - `python tools/sync_docs.py --check` failed because `API.md -> docs/api.md` and `CONTRIBUTING.md -> docs/contributing.md` are out of sync.
  - `python tools/check_stale_docs.py` passed.
  - `python tools/check_pytest_collection_policy.py` passed and reported the allowed ignored local file `tests/test_close_plan_stages.py`.

Skipped for safety or size:

- Secret-heavy paths and files matching the skill policy, including `.env*` except examples, private keys, cert/key material, credentials JSON, and service-account JSON.
- Browser capture caches under `.playwright-cli/` and `.playwright-mcp/`, except noting their existence as generated artifacts.
- Full `uv.lock` dump; dependency signals were sampled only.

## Context7 Documentation Checks

- **cryptography** `>=48.0` - checked AES-GCM nonce uniqueness and ECDH/HKDF usage; impact: future Secure Notepad durability or re-keying work must preserve unique nonces per key, explicit key derivation boundaries, and avoid ad hoc crypto changes.
- **pytest** `>=9.0` - checked current pytest configuration and TOML/marker guidance; impact: module-specific test gates and marker-based acceptance lanes are viable next QA improvements.
- **Docker docs** `current` - checked Python/container operational guidance around non-root runtime, healthchecks, secrets, Compose publishing, SBOM/provenance; impact: current Dockerfile is directionally aligned, but roadmap should decide whether Docker remains a local/trusted-lab convenience or becomes a first-class distribution surface.
- **Python release status** `current as of 2026-06-14` - preflight recorded official Python checks because interpreter support is date-sensitive; impact: `requires-python = ">=3.10,<3.14"` now needs an explicit support-window decision rather than remaining an accidental cap.

## Observed Problems & Risks

- **Docs mirror drift is present now.** `python tools/sync_docs.py --check` fails for `API.md -> docs/api.md` and `CONTRIBUTING.md -> docs/contributing.md`. This is an immediate CI/docs hygiene fix, not a design question.
- **Default profile is still `lab`.** `src/features.py` sets `DEFAULT_PROFILE = "lab"` and docs show CLI default `--profile` as `lab`. This preserves compatibility but makes the full experimental surface the default, including advanced upload, SMUGGLE, NOTE, WebSocket, upload clear, and note clear. The next roadmap should decide whether the tool remains "lab-first" or moves to safe-by-default `serve`/`workspace` behavior with a compatibility bridge.
- **The product identity is split between trusted lab tool and packaged server.** README and SECURITY guidance repeatedly frame trusted-lab usage, while packaging, Docker, release artifacts, provenance, and public package identity have matured. This needs an explicit direction: local developer utility, secure personal workspace, embeddable Python server, or publishable ops tool.
- **Secure Notepad is useful but intentionally not durably recoverable.** `API.md` states keys are session-bound and can become unrecoverable after reload, restart, idle expiry, or LRU eviction. The next product decision is whether Notepad stays an ephemeral encrypted scratchpad or gains a durable key/recovery model.
- **Reverse-proxy identity and auth rate limiting are not a complete production story.** `_authenticate_request` keys the limiter on `client_address[0]`. Docs recommend reverse-proxy rate limiting, but there is no trusted-proxy model, forwarded client identity policy, or proxy-aware abuse boundary. This is acceptable for direct/trusted deployment, but should be revisited before broader hosted usage.
- **API contracts still show mixed legacy behavior.** `API.md` documents JSON errors for many paths, but some receive-layer failures close without an HTTP body, and legacy method bodies remain mixed across `FETCH`, `INFO`, advanced upload, and WebSocket message errors. A client-library or stable public API direction would benefit from normalized response envelopes and versioning.
- **Advanced upload and lab-only features are coupled to compatibility.** Docs describe advanced upload as enabled by default because the default profile is `lab`. If defaults change, migration docs and compatibility flags must be planned carefully.
- **CI coverage is broad but not risk-specific.** The global coverage gate is `--cov-fail-under=65`; there are many targeted tests, but no explicit module-level gates for auth, HTTP parsing, WebSocket framing, Notepad storage, or origin/CORS policy.
- **Python support cap needs renewal.** Metadata and CI cover Python 3.10-3.13. The roadmap should decide whether to add Python 3.14, when to drop older interpreters, and how to test upcoming 3.15.
- **Release lane builds and attests but does not publish.** `.github/workflows/release.yml` produces artifacts, SBOM, and attestations, but does not publish to PyPI/GHCR or create a GitHub Release. That may be intentional; if not, distribution is the next step.
- **Observability is local and in-memory.** `/metrics` exists and is valuable for smoke/ops, but there is no Prometheus/OpenTelemetry export, SLO language, alert examples, or operator runbook.
- **Embedded UI deserves product and accessibility review.** Static UI assets are packaged and smoke-tested, but the future product surface depends on profile awareness, destructive-operation affordances, notepad recovery messaging, keyboard behavior, and status/live-region quality.
- **Changelog/release hygiene needs a pass.** `CHANGELOG.md` remains heavily `[Unreleased]` oriented relative to the completed implementation plan and release lane.

## Recommended Development Paths

1. **Conservative hardening path**
   - Keep the tool as a trusted-lab/developer utility.
   - Fix docs drift, improve docs/runbooks, keep `lab` default for compatibility, and strengthen tests around the existing surface.
   - Best when compatibility and local experimentation matter more than broad distribution.

2. **Safe-by-default server path**
   - Make `serve` or `workspace` the default in a major/minor compatibility plan, keep `lab` explicit, and tighten public defaults around auth, CORS, destructive methods, and WebSocket.
   - Best when the tool should be recommended to less expert users or exposed beyond a private lab network.

3. **Secure workspace path**
   - Treat uploads plus Secure Notepad as the main product.
   - Add durable encrypted-note recovery/re-keying, stronger UI flows, import/export, conflict semantics, and clearer local data lifecycle controls.
   - Best when Notepad is a first-class feature rather than a demo of crypto and WebSocket capability.

4. **Distribution and operations path**
   - Treat `exphttp` as a publishable package/container.
   - Add PyPI/GitHub Release/GHCR publishing, release notes, version policy, Python 3.14 support, image update cadence, Prometheus/OpenTelemetry export, and deployment recipes.
   - Best when the project should be installable and operable without reading the full repository.

5. **API/client platform path**
   - Stabilize contracts for methods, errors, capabilities, WebSocket messages, and profile negotiation.
   - Add a generated or handwritten client, compatibility tests, and versioned API docs.
   - Best when other tools should build on top of the server.

## Selected Agents

### Must Run

- **product-manager** - The main open question is strategic direction: lab utility, safe-by-default server, secure workspace, distribution artifact, or API platform.
- **architect-reviewer** - Core boundaries now span profile gates, socket lifecycle, handler mixins, static UI, package shims, storage domains, and WebSocket logic.
- **security-auditor** - Default `lab`, Basic Auth/rate limiting, CORS/browser-origin policy, NOTE crypto boundaries, SMUGGLE, upload/delete methods, and reverse-proxy assumptions need security-specific prioritization.
- **api-designer** - Future development depends on whether method contracts, error bodies, capabilities, and WebSocket messages become stable public API.
- **qa-expert** - The repository has broad tests, but roadmap work needs risk-based gates rather than only a global 65% coverage threshold.

### High Value

- **websocket-engineer** - STAGE-011 closed operational failure semantics, but future Notepad/product work depends on reconnect, idempotency, backpressure, and message contract choices.
- **performance-engineer** - Request admission, upload streaming, notepad quotas, directory listing, and slow-body controls are central to the server's reliability envelope.
- **devops-engineer** - CI/release/docs sync, artifact publishing, Python matrix policy, and runtime operations are the next likely bottlenecks.
- **dependency-manager** - Python 3.14/3.15 readiness, constraints parity, ACME/crypto dependency cadence, and Dependabot policy need a current package-support review.
- **documentation-engineer** - Docs drift exists now, and direction changes will require clear migration, operator, API, and release docs.
- **frontend-developer** - The static UI is now part of the package and should be evaluated as a real user surface if the tool moves beyond CLI-only operation.
- **accessibility-tester** - Destructive actions, status updates, notepad encryption/recovery state, and WebSocket feedback should be checked before UI expansion.

### Worth Running

- **docker-expert** - Dockerfile is already non-root and healthchecked, but container distribution and Compose/operator posture need a focused review if ops path is chosen.
- **project-manager** - After specialist reports, convert the chosen direction into a new staged implementation plan with dependencies and acceptance criteria.

## Execution Strategy

Thread limit is unknown, so Phase 2 should use no more than 6 concurrent subagents.

- **Parallel batch 1: roadmap foundations**
  - `product-manager`
  - `architect-reviewer`
  - `security-auditor`
  - `api-designer`
  - `qa-expert`

- **Parallel batch 2a: runtime and operations depth**
  - `websocket-engineer`
  - `performance-engineer`
  - `devops-engineer`
  - `dependency-manager`
  - `documentation-engineer`
  - `docker-expert`

- **Parallel batch 2b: product UI depth**
  - `frontend-developer`
  - `accessibility-tester`

- **Sequential chain A: delivery synthesis**
  - `project-manager` after all previous reports are saved.
  - Input: every completed specialist report plus this plan.
  - Output: candidate staged roadmap options, with immediate fixes, short-term roadmap, medium-term strategic work, dependencies, and acceptance criteria.

- **Parent synthesis after Phase 2**
  - Read every saved agent report in full.
  - Deduplicate findings.
  - Write `project-analysis-report.md`.

Phase 2 and Phase 3 must not start until the user explicitly confirms this `analysis-plan.md`.

## Focus Areas Per Agent

### product-manager

- Relevant paths:
  - `README.md`
  - `API.md`
  - `SECURITY.md`
  - `CHANGELOG.md`
  - `docs/architecture.md`
  - `implementation-plan/20260525-133607/*`
  - `codex-analysis/20260525-121051/project-analysis-report.md`
- Questions:
  - Which path should dominate: trusted lab tool, safe-by-default server, secure workspace, distribution/ops product, or API/client platform?
  - What should the default profile be for new users?
  - Which features are core product value versus experimental examples?
- Known risks to verify:
  - Compatibility pressure from `lab` default may block a safer product posture.
  - Secure Notepad's current unrecoverable-session model may surprise users if marketed as durable notes.

### architect-reviewer

- Relevant paths:
  - `src/features.py`
  - `src/server.py`
  - `src/request_pipeline.py`
  - `src/handlers/*`
  - `src/http/*`
  - `src/notepad_service.py`
  - `src/websocket.py`
  - `exphttp/*`
  - `docs/architecture.md`
- Questions:
  - Are server lifecycle, handler mixins, capability profiles, and package shims still coherent after the completed remediation plan?
  - Should profile/capability policy move further away from `server.py`?
  - Are storage domains and static UI responsibilities clean enough for the next feature wave?
- Known risks to verify:
  - `src/server.py` is a broad coordination point and may become the limiting factor for future changes.
  - Compatibility aliases and public shims may constrain architecture changes.

### security-auditor

- Relevant paths:
  - `src/security/auth.py`
  - `src/security/crypto.py`
  - `src/security/keys.py`
  - `src/security/tls.py`
  - `src/security/tls_manager.py`
  - `src/server.py`
  - `src/http/io.py`
  - `src/http/cors.py`
  - `src/handlers/notepad.py`
  - `src/handlers/smuggle.py`
  - `src/notepad_service.py`
  - `src/websocket.py`
  - `SECURITY.md`
  - `docs/threat-model.md`
  - `Dockerfile`
- Questions:
  - Is `lab` default acceptable for the documented audience?
  - What is the correct trusted-proxy and client-IP model for auth rate limiting?
  - Does Notepad's ECDH/AES-GCM/session model remain safe if durable recovery is added later?
  - Are SMUGGLE, advanced upload, clear operations, and WebSocket adequately gated by profiles and browser-origin policy?
- Known risks to verify:
  - Current rate limiting uses direct socket IP, not a trusted-forwarded identity model.
  - Changing Notepad durability without careful crypto design could create a real regression.

### api-designer

- Relevant paths:
  - `API.md`
  - `src/http/response.py`
  - `src/request_pipeline.py`
  - `src/handlers/files.py`
  - `src/handlers/advanced_upload.py`
  - `src/handlers/notepad.py`
  - `src/handlers/smuggle.py`
  - `src/features.py`
  - `src/websocket.py`
  - `tests/test_server_methods.py`
  - `tests/test_websocket_handlers.py`
- Questions:
  - Which contracts should become stable: custom methods, capabilities, error envelopes, WebSocket message types, profile semantics?
  - Is a versioned API needed before adding clients or publishing more broadly?
  - How should receive-layer connection-close failures be represented to clients and docs?
- Known risks to verify:
  - Mixed legacy response formats can make clients brittle.
  - WebSocket operation errors and HTTP errors use related but not identical shapes.

### qa-expert

- Relevant paths:
  - `tests/`
  - `pyproject.toml`
  - `.github/workflows/ci.yml`
  - `.github/workflows/security.yml`
  - `.github/workflows/release.yml`
  - `tools/check_pytest_collection_policy.py`
  - `tools/browser_smoke.py`
  - `tools/check_static_ui_assets.py`
  - `tools/sync_docs.py`
  - `tools/check_stale_docs.py`
- Questions:
  - Which modules need explicit coverage or marker gates?
  - Which smoke tests should block release versus PR CI?
  - Should browser/Docker/live-server checks expand for profile-specific workflows?
- Known risks to verify:
  - Global coverage can hide weak coverage in high-risk auth/parser/WebSocket/storage modules.
  - Docs-sync drift currently indicates local pre-commit or developer-flow gap.

### websocket-engineer

- Relevant paths:
  - `src/websocket.py`
  - `src/server.py`
  - `src/handlers/notepad.py`
  - `src/notepad_service.py`
  - `API.md`
  - `tests/test_websocket.py`
  - `tests/test_websocket_handlers.py`
  - `tests/test_security/test_websocket_frame_limit.py`
  - `tests/test_security/test_websocket_upgrade.py`
- Questions:
  - Is the current no-fragmentation/minimal RFC 6455 implementation enough for expected clients?
  - What should reconnect, duplicate `opId`, conflict, and close-code behavior be if Notepad becomes a real workspace feature?
  - Are backpressure, idle ping, frame-size, and incomplete-frame timeout policies sufficient?
- Known risks to verify:
  - Productizing Notepad will put more pressure on WebSocket semantics than the current implementation plan required.

### performance-engineer

- Relevant paths:
  - `src/http/io.py`
  - `src/server.py`
  - `src/storage.py`
  - `src/notepad_service.py`
  - `src/metrics.py`
  - `src/handlers/files.py`
  - `src/handlers/advanced_upload.py`
  - `tests/test_server_live.py`
  - `tests/test_http/test_io.py`
  - `tests/test_metrics.py`
- Questions:
  - Which hot paths need benchmarks before widening usage?
  - Are body memory reservation, disk quotas, large listings, and slow-reader behavior measurable enough?
  - Should `/metrics` include latency/histogram-style signals or remain simple counters/gauges?
- Known risks to verify:
  - Current metrics are good for local visibility but not yet enough for capacity planning or alerts.

### devops-engineer

- Relevant paths:
  - `.github/workflows/ci.yml`
  - `.github/workflows/security.yml`
  - `.github/workflows/release.yml`
  - `.github/dependabot.yml`
  - `Dockerfile`
  - `docker-compose.yml`
  - `constraints/ci.txt`
  - `tools/check_dependency_constraints.py`
  - `tools/sync_docs.py`
  - `docs/`
- Questions:
  - Should the release lane publish to PyPI/GitHub Releases/GHCR or remain artifact-only?
  - What should the Python support and deprecation policy be?
  - How should docs sync be caught earlier than CI?
- Known risks to verify:
  - Docs mirror drift is already reproducible locally.
  - Release provenance exists, but distribution is not yet automated.

### dependency-manager

- Relevant paths:
  - `pyproject.toml`
  - `constraints/ci.txt`
  - `uv.lock`
  - `.github/dependabot.yml`
  - `.github/workflows/security.yml`
  - `Dockerfile`
- Questions:
  - What is the correct Python 3.14 support plan and 3.10/3.11 deprecation horizon?
  - Are constraints, optional dependency groups, Docker base image, and CI matrix aligned?
  - Are ACME/crypto packages pinned and audited at the right cadence?
- Known risks to verify:
  - Interpreter support policy can become stale quickly if not formalized.

### documentation-engineer

- Relevant paths:
  - `README.md`
  - `API.md`
  - `CONTRIBUTING.md`
  - `SECURITY.md`
  - `CHANGELOG.md`
  - `docs/`
  - `mkdocs.yml`
  - `tools/sync_docs.py`
  - `tools/check_stale_docs.py`
  - `implementation-plan/20260525-133607/*`
- Questions:
  - Which docs need to be regenerated immediately?
  - Does the documentation clearly separate safe profiles, lab features, and production warnings?
  - Are release notes and migration notes ready after the closed implementation plan?
- Known risks to verify:
  - Top-level docs and `docs/` mirrors are currently out of sync.

### frontend-developer

- Relevant paths:
  - `src/data/static/ui/*`
  - `src/server.py`
  - `src/features.py`
  - `API.md`
  - `tools/browser_smoke.py`
  - `tools/browser_smoke.playwright.js`
  - `tests/test_ui_inspector_redaction.py`
- Questions:
  - Does the UI expose profile capabilities accurately and hide unavailable actions?
  - Are destructive operations, Notepad encryption state, quota errors, and WebSocket states visible and recoverable?
  - Is a static no-build UI still the right approach for the desired product path?
- Known risks to verify:
  - UI quality becomes product-critical if the tool moves toward secure workspace or less technical users.

### accessibility-tester

- Relevant paths:
  - `src/data/static/ui/*`
  - `tools/browser_smoke.py`
  - `tools/browser_smoke.playwright.js`
  - `README.md`
  - `API.md`
- Questions:
  - Are controls keyboard-reachable and correctly labelled?
  - Are dynamic Notepad/WebSocket/upload states announced without visual-only cues?
  - Are destructive actions and encryption/recovery warnings accessible?
- Known risks to verify:
  - Static UI smoke tests can pass while keyboard and assistive-tech flows remain weak.

### docker-expert

- Relevant paths:
  - `Dockerfile`
  - `docker-compose.yml`
  - `.dockerignore`
  - `.github/workflows/ci.yml`
  - `.github/workflows/release.yml`
  - `README.md`
  - `SECURITY.md`
- Questions:
  - Should the image stay a local/operator example or become a published artifact?
  - Are mounts, non-root ownership, auth-file secrets, TLS/ACME state, healthchecks, and port binding examples complete?
  - Is the base-image refresh process operationally sufficient?
- Known risks to verify:
  - Container posture is good for local use, but publishing raises maintenance and vulnerability-response obligations.

### project-manager

- Relevant paths:
  - This `analysis-plan.md`
  - All completed reports under `codex-analysis/20260614-225437/agent-reports/`
  - `implementation-plan/20260525-133607/*`
- Questions:
  - What are the best next implementation stages once direction is selected?
  - Which quick wins should be separated from strategic work?
  - Which tasks depend on product/security decisions?
- Known risks to verify:
  - Without sequencing, the project can spend time on tactical polish before resolving default-profile and product-identity decisions.
