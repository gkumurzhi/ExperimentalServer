# Project Analysis Plan
_Generated: 2026-05-05 19:32:49 Europe/Moscow_

## Stack Summary

ExperimentalHTTPServer is a Python 3.10-3.13 package and CLI (`exphttp`) for a single-process HTTP/1.1 server with custom methods, uploads-only file access, Secure Notepad, WebSocket support, TLS, Basic Auth, metrics, and a bundled static browser UI.

- Language/runtime: Python package under `src/`, typed with `py.typed`, strict `mypy`.
- Packaging/build: `setuptools.build_meta`, dynamic version from `src.config.__version__`, console script `exphttp = src.cli:main`.
- Runtime dependencies: `acme>=5.5,<6`, `cryptography>=48.0`; `[crypto]` remains an empty compatibility extra.
- Test/tooling dependencies: `pytest`, `pytest-cov`, `hypothesis`, `pytest-benchmark`, `ruff`, `mypy`, `mkdocs`, `mkdocs-material`, `pip-audit`, `bandit`.
- Runtime architecture: blocking sockets, `ThreadPoolExecutor`, request parsing in `src/http`, orchestration in `src/request_pipeline.py`, handler registry/mixins in `src/handlers`, TLS lifecycle in `src/security/tls_manager.py`, built-in ACME helpers in `src/security/tls.py`.
- Persistence: filesystem-backed runtime data under `<root>/uploads/` and `<root>/notes/`.
- Frontend: bundled HTML/JS/CSS in `src/data/`, served through package resources and static handlers.
- CI/CD: GitHub Actions for Python matrix, docs, smoke, Docker smoke, weekly security workflow; Dependabot for pip, GitHub Actions, Docker, and pre-commit.
- Infrastructure: multi-stage `Dockerfile`, example Compose file under `examples/docker/docker-compose.yml`.

## Project Structure Overview

- `src/cli.py` parses CLI flags and constructs `ExperimentalHTTPServer`.
- `src/server.py` owns socket lifecycle, TLS setup, keep-alive, WebSocket loop, metrics, auth setup, and server startup/shutdown.
- `src/request_pipeline.py` centralizes request parse/auth/dispatch/send orchestration and WebSocket upgrade routing.
- `src/http/` contains request parsing, response construction, CORS helpers, and socket request framing.
- `src/handlers/` contains file operations, INFO/PING, NOTE, advanced upload, SMUGGLE, and method registry composition.
- `src/security/` contains Basic Auth, crypto helpers, ECDH session management, TLS/X.509/ACME helpers, and TLS manager lifecycle.
- `src/data/` contains the browser UI and static assets; `crypto-js.min.js` is minified and was excluded from detailed reading.
- `tests/` is broad: 37 Python test files, 9,251 LOC, including unit, property, integration, live socket, WebSocket, TLS/ACME mock, CLI, and frontend inspector redaction tests.
- `.github/`, `Dockerfile`, `.dockerignore`, `.pre-commit-config.yaml`, `constraints/ci.txt`, and `mkdocs.yml` define delivery, security, reproducibility, and docs behavior.
- `codex-analysis/20260428-113859/` and `implementation-plan/20260428-154031/` are previous audit/implementation artifacts. They were sampled as historical context, not treated as source of truth for current code.
- Omitted from exhaustive traversal: `.git/`, `.codex/`, `.claude/`, caches, `.venv/`, `site/`, `build/`, generated/cache directories, minified JS, runtime data, and secret-heavy patterns.

## Reconnaissance Coverage

Read or inspected:
- Project guidance and docs: `README.md`, `CLAUDE.md`, `API.md`, `SECURITY.md`, `docs/index.md`, `docs/architecture.md`, `docs/threat-model.md`, selected ADRs, previous final audit summary, active implementation plan status.
- Python/package config: `pyproject.toml`, `constraints/ci.txt`, `src/__init__.py`, `src/__main__.py`, `src/config.py`.
- Runtime code: `src/cli.py`, `src/server.py`, `src/request_pipeline.py`, `src/http/*`, `src/handlers/*`, `src/security/*`, `src/notepad_service.py`, `src/websocket.py`, `src/metrics.py`, representative `tools/*`.
- Frontend code: `src/data/index.html` file size and representative modules `app.js`, `requests.js`, `notepad.js`, `upload.js`, `files.js`, `dialogs.js`, `core.js`; high-signal `innerHTML`/storage searches.
- Tests: `tests/conftest.py`, test structure/LOC, representative TLS/TLS manager/live socket tests, high-signal searches across all tests.
- CI/infra: `.github/workflows/ci.yml`, `.github/workflows/security.yml`, `.github/dependabot.yml`, `.pre-commit-config.yaml`, `Dockerfile`, `.dockerignore`, `.gitignore`, `mkdocs.yml`, examples.

Commands used for reconnaissance were read-only except for creating analysis artifacts under this output directory. No Phase 2 agents were spawned. No test suite was run as part of this audit phase; prior turn verification exists, but Phase 2 agents should independently verify relevant areas.

Skipped for safety/size:
- `.env*`, private keys/certs/credential JSON patterns, runtime `uploads/`/`notes/` contents.
- `.venv/`, caches, previous ignored `.claude/` and `.codex/` report trees.
- `src/data/static/crypto-js.min.js` because it is minified third-party code.

## Context7 Documentation Checks

- **cryptography** `>=48.0` - checked: X.509 certificate generation, PEM private-key serialization, timezone-aware certificate validity APIs; impact: TLS/self-signed/expiry review should compare against `CertificateBuilder`, `private_bytes`, and `not_valid_after_utc` usage.
- **Certbot acme** `5.5.0` - checked: `ClientV2`, account/order flow, HTTP-01 challenge response, `HTTP01DualNetworkedServers`, standalone port-80 constraints; impact: ACME review should focus on account reuse, challenge server binding, wildcard/DNS-01 limits, and key/cert storage behavior.
- **pytest** `9.0.3` - checked: fixture/monkeypatch/parametrization guidance; impact: QA review should validate the current mock-heavy ACME/TLS tests, live socket tests, and local/CI coverage split.

Additional docs likely needed in Phase 2: MkDocs Material, GitHub Actions, Docker, `pip-audit`, and Python packaging/pre-commit guidance if agents make recommendations in those areas.

## Observed Problems & Risks

- [HIGH] Example Secure Notepad client derives the wrong ECDH/HKDF key. `examples/notepad_client.py:118-123` uses `salt=None` and `info=b"exphttp-notepad"`, while the server and browser UI use 32 zero bytes and `notepad-e2e-key` in `src/security/keys.py:41-42` and `src/data/static/ui/notepad.js:501-507`. The example can save unreadable notes or fail round-trip decryption.
- [MEDIUM] Runtime docs and guidance drift after the dependency-policy change. `README.md:11`, `CLAUDE.md:7`, and `docs/index.md:3` still describe pure Python / zero external dependencies, while `pyproject.toml:37-40` makes `acme` and `cryptography` runtime dependencies.
- [MEDIUM] User-facing crypto-unavailable errors still tell users to install `exphttp[crypto]` even though `[crypto]` is now empty: `src/request_pipeline.py:208-212` and `src/handlers/notepad.py:38-40`.
- [MEDIUM] Pre-commit mypy environment is stale relative to current runtime deps. `.pre-commit-config.yaml:21-28` installs only `cryptography==46.0.5`; it does not include `acme`/`josepy` and conflicts with `cryptography>=48.0` in `pyproject.toml:37-40`.
- [MEDIUM] Local ignored files can affect local test results but are absent from tracked source and CI. `.gitignore:63-64` ignores `tools/close_plan_stages.py` and `tests/test_close_plan_stages.py`; both exist locally as ignored files and are collected by local `pytest`.
- [MEDIUM] TLSManager checks certificate freshness but not matching private-key existence before reusing a cached ACME cert. `src/security/tls_manager.py:99-132` can set `key_file` to a missing `privkey.pem` when `fullchain.pem` exists and is fresh, pushing the failure to SSL context load instead of renewing/recovering.
- [MEDIUM] CLI validation is asymmetric. `src/cli.py:175-182` validates ACME-specific combinations and port range, but `-p/--port`, `-m/--max-size`, and `-w/--workers` accept negative or zero values until lower-level socket, request-size, or `ThreadPoolExecutor` failures.
- [LOW] MkDocs nav label is stale: `mkdocs.yml:57` still says `ADR-003 · Optional cryptography`, while the ADR title is `Runtime crypto and ACME dependencies`.
- [LOW] ACME live issuance was not exercised. Current tests mock `ClientV2`/challenge server behavior; Phase 2 should explicitly distinguish mock coverage from operational coverage that requires routable port 80 and a real domain/IP.
- [LOW] The bundled frontend still relies heavily on generated `innerHTML`. Many call sites use `esc()`, but the UI is large enough that frontend/security agents should re-check XSS/redaction/a11y paths rather than assume previous fixes still cover every flow.
- [LOW] Current worktree is dirty from the just-implemented TLS/ACME/sslip plan. Phase 2 should evaluate current dirty state as the audit target and avoid treating previous implementation-plan closure as proof that new changes did not reintroduce drift.

Positive signals:
- Broad test suite with property tests, live socket tests, TLS/ACME mocks, WebSocket protocol tests, and docs sync checks.
- Strong file path containment patterns through `Path.resolve().relative_to()`.
- Runtime data/secret ignore policies are extensive in `.dockerignore`/`.gitignore`.
- Docker runtime is non-root and has a healthcheck for the default HTTP mode.
- Context7 is available for docs-backed Phase 2 recommendations.

## Selected Agents

### Must Run
- **security-auditor** - TLS/ACME, Basic Auth, path containment, advanced upload, CORS, NOTE/WebSocket, and frontend inspector/redaction risks are central to this server.
- **python-pro** - Python packaging/runtime/import behavior, typing, exception handling, filesystem use, and ACME/cryptography integration need a Python-specific pass.
- **architect-reviewer** - The server spans socket lifecycle, request pipeline, handler mixins, storage boundaries, and docs/ADR decisions; architecture drift matters.
- **qa-expert** - The suite is broad but has local-only ignored tests, mock-only ACME coverage, and example-client gaps that need a test strategy review.
- **devops-engineer** - CI, security workflow, pre-commit, constraints, dirty/ignored local artifacts, and release smoke are high-risk process surfaces.
- **dependency-manager** - Runtime dependency policy just changed; constraints, transitive deps, pre-commit pins, Dependabot, and vulnerability workflows need dedicated review.

### High Value
- **websocket-engineer** - WebSocket protocol and Secure Notepad transport remain specialized and security-sensitive.
- **performance-engineer** - Blocking sockets, worker pool, uploads, advanced uploads, SMUGGLE, WebSocket buffers, and ACME challenge startup all have resource implications.
- **docker-expert** - Dockerfile/Compose defaults, non-root runtime, healthcheck behavior under TLS/auth, and ACME port needs require a container-specific pass.
- **frontend-developer** - Bundled UI is large, stateful, and security-adjacent; inspector, upload, request runner, and notepad flows need browser/UI review.
- **documentation-engineer** - README, CLAUDE, docs mirrors, ADR naming, Security docs, and examples have visible drift.
- **cli-developer** - CLI validation and TLS/ACME flag ergonomics are a distinct user-facing surface.

### Worth Running
- **api-documenter** - Custom methods, NOTE/WebSocket semantics, error bodies, CORS, TLS/ACME flags, and examples should be reconciled against implementation.
- **reviewer** - A final PR-style read of the dirty diff can catch regressions missed by domain agents before synthesis.

## Execution Strategy

Do not start Phase 2 until the saved plan is confirmed.

Parallel batch 1, core runtime and security, max 6 agents:
- `security-auditor`
- `python-pro`
- `architect-reviewer`
- `websocket-engineer`
- `performance-engineer`
- `cli-developer`

Parallel batch 2, delivery, tests, docs, UI, max 6 agents:
- `qa-expert`
- `devops-engineer`
- `dependency-manager`
- `docker-expert`
- `frontend-developer`
- `documentation-engineer`

Sequential chain A after batches 1 and 2:
- `api-documenter`, using the domain-agent findings and current implementation to verify the public API/docs contract.

Sequential chain B after chain A:
- `reviewer`, focused on the current dirty diff, residual high/medium findings, missing tests, and synthesis-ready risk ranking.

Phase 3 synthesis will read every saved report in full, deduplicate findings, preserve unique evidence, and write `project-analysis-report.md`.

## Focus Areas Per Agent

### security-auditor
- Relevant paths: `src/security/*`, `src/request_pipeline.py`, `src/server.py`, `src/http/io.py`, `src/http/cors.py`, `src/handlers/*`, `src/data/static/ui/*`, `SECURITY.md`, `docs/threat-model.md`.
- Questions:
  - Does built-in ACME store and reuse account/domain keys safely?
  - Are cert/key cache-miss and renewal states fail-closed and recoverable?
  - Are Basic Auth, CORS, WebSocket origin, path containment, hidden files, and advanced upload policies consistent?
  - Are frontend inspector and static UI flows safe from sensitive data exposure and XSS?
- Known risks to verify:
  - `TLSManager` cert reuse without key existence check.
  - Empty `[crypto]` extra but stale install guidance in runtime errors.
  - Mock-only ACME coverage versus live challenge operational risks.

### python-pro
- Relevant paths: `pyproject.toml`, `src/__init__.py`, `src/security/__init__.py`, `src/security/tls.py`, `src/security/tls_manager.py`, `src/cli.py`, `src/server.py`, `src/http/request.py`, `src/http/io.py`, `src/notepad_service.py`.
- Questions:
  - Are imports/build metadata safe with runtime dependencies now imported by `src.__init__`?
  - Are exceptions too broad or swallowed in places that should log/propagate?
  - Are type hints and strict mypy settings aligned with current runtime deps?
  - Are filesystem writes atomic where needed and bounded where user input is involved?
- Known risks to verify:
  - Pre-commit mypy missing `acme`/`josepy`.
  - CLI lower-bound validation for port/workers/max-size.
  - ACME account/key path behavior and private-key serialization choices.

### architect-reviewer
- Relevant paths: `src/server.py`, `src/request_pipeline.py`, `src/handlers/__init__.py`, `src/handlers/base.py`, `src/notepad_service.py`, `src/security/tls_manager.py`, `docs/architecture.md`, `docs/ADR/*`.
- Questions:
  - Are handler/server boundaries still coherent after TLS/ACME changes?
  - Are runtime storage boundaries (`uploads/`, `notes/`, `~/.exphttp/acme`) explicit and documented?
  - Does ADR-003 supersede all old stdlib-only guidance cleanly?
  - Are compatibility helpers such as `check_certbot_available()`/`check_openssl_available()` still useful or misleading?
- Known risks to verify:
  - Docs/ADR nav title drift.
  - Previous plan closed many architecture issues; current dirty changes may reintroduce conceptual drift.

### websocket-engineer
- Relevant paths: `src/websocket.py`, `src/server.py`, `src/request_pipeline.py`, `src/handlers/notepad.py`, `src/notepad_service.py`, `src/data/static/ui/notepad.js`, `tests/test_websocket.py`, `tests/test_websocket_handlers.py`, `tests/test_server_live.py`.
- Questions:
  - Are WebSocket upgrade, origin, masking, size, close-frame, and timeout semantics still correct?
  - Are HTTP NOTE and WebSocket NOTE contracts aligned?
  - Does the example client use the same ECDH/HKDF contract as server/browser?
- Known risks to verify:
  - `examples/notepad_client.py` HKDF mismatch.
  - WebSocket worker occupancy and incomplete-frame timeout behavior.

### performance-engineer
- Relevant paths: `src/server.py`, `src/http/io.py`, `src/handlers/files.py`, `src/handlers/advanced_upload.py`, `src/handlers/smuggle.py`, `src/notepad_service.py`, `src/security/tls.py`, tests around upload/streaming.
- Questions:
  - Where are request/response bodies fully buffered?
  - Do advanced upload, SMUGGLE, NOTE, and WebSocket limits bound peak memory?
  - Can ACME public-IP lookup/challenge issuance block startup unexpectedly?
  - Are metrics sufficient for observing latency/errors/resource pressure?
- Known risks to verify:
  - Base64 transports multiply memory.
  - Fixed worker pool and long-lived WebSockets/keep-alive share capacity.

### cli-developer
- Relevant paths: `src/cli.py`, `src/server.py`, `src/security/tls_manager.py`, `README.md`, `tests/test_cli.py`.
- Questions:
  - Are flags validated consistently (`--port`, `--max-size`, `--workers`, TLS cert/key, `--letsencrypt`, `--sslip`, custom ACME server)?
  - Are incompatible combinations rejected early with actionable messages?
  - Does CLI help match actual behavior and docs?
- Known risks to verify:
  - Only `--acme-http-port` has explicit range validation.
  - `--cert/--key` with `--letsencrypt` ambiguity.

### qa-expert
- Relevant paths: `tests/`, `pyproject.toml`, `.github/workflows/ci.yml`, `tools/browser_smoke.py`, `tests/test_ui_inspector_redaction.py`, ignored `tests/test_close_plan_stages.py`.
- Questions:
  - Which current risks lack regression tests?
  - Does local `pytest` collect ignored tests that CI will not see?
  - Are ACME tests over-mocked or sufficiently behavioral?
  - Are examples tested beyond `--help`?
- Known risks to verify:
  - Notepad example HKDF mismatch has no round-trip test.
  - Live Let’s Encrypt issuance is not exercised.
  - Local ignored stage-runner tests can distort local confidence.

### devops-engineer
- Relevant paths: `.github/workflows/ci.yml`, `.github/workflows/security.yml`, `.github/dependabot.yml`, `.pre-commit-config.yaml`, `constraints/ci.txt`, `.gitignore`, `.dockerignore`, `pyproject.toml`.
- Questions:
  - Are CI, security, docs, smoke, Docker, and pre-commit workflows aligned with the new runtime dependencies?
  - Are ignored/untracked local artifacts a process hazard?
  - Do scheduled audits and constraints cover runtime + transitive dependencies?
  - Are docs sync and stale-reference greps covering new dependency/TLS/ACME language?
- Known risks to verify:
  - Pre-commit mypy isolated deps are stale.
  - Existing stale-doc grep does not catch zero-dependency claims.
  - Local ignored files under `tools/` and `tests/`.

### dependency-manager
- Relevant paths: `pyproject.toml`, `constraints/ci.txt`, `.pre-commit-config.yaml`, `.github/dependabot.yml`, `Dockerfile`, `SECURITY.md`, `docs/ADR/ADR-003-cryptography-optional.md`.
- Questions:
  - Is `constraints/ci.txt` consistent with declared lower/upper bounds?
  - Are runtime deps, transitive deps, extras, pre-commit deps, and Docker installs reproducible?
  - Are vulnerability scans and Dependabot coverage adequate after adding `acme`/`cryptography` to runtime?
- Known risks to verify:
  - `cryptography>=48.0` but pre-commit pins `46.0.5`.
  - Empty `[crypto]` extra may be okay for compatibility but can mislead docs/errors.

### docker-expert
- Relevant paths: `Dockerfile`, `.dockerignore`, `examples/docker/docker-compose.yml`, `.github/workflows/ci.yml`, `README.md`.
- Questions:
  - Does the Docker image install the new runtime ACME/crypto dependencies reproducibly?
  - Are non-root filesystem permissions compatible with `~/.exphttp/acme`, `/data/uploads`, `/data/notes`, and `/tmp`?
  - How should healthchecks behave under TLS/auth/ACME modes?
  - Are port 80/443 and capabilities documented for ACME/sslip use?
- Known risks to verify:
  - ACME may need port 80 reachability while container defaults expose 8080.
  - Healthcheck is HTTP-only by default.

### frontend-developer
- Relevant paths: `src/data/index.html`, `src/data/static/ui/*.js`, `src/data/static/ui/*.css`, `tools/browser_smoke.py`, `tests/test_ui_inspector_redaction.py`, `tests/test_server_routing.py`.
- Questions:
  - Does the UI surface new TLS/sslip/ACME behavior or avoid misleading users?
  - Are request inspector, upload, files, opsec, and notepad flows safe and accessible?
  - Are `innerHTML` uses escaped or otherwise controlled?
  - Do browser smoke tests cover the flows that matter?
- Known risks to verify:
  - Large JS surface with many `innerHTML` call sites.
  - Notepad example mismatch may indicate client contract drift.

### documentation-engineer
- Relevant paths: `README.md`, `API.md`, `SECURITY.md`, `CHANGELOG.md`, `CLAUDE.md`, `docs/*`, `docs/ADR/*`, `examples/*`, `tools/sync_docs.py`, `mkdocs.yml`.
- Questions:
  - Do root-canonical docs and generated mirrors match current code?
  - Are old zero-dependency and `[crypto]` instructions gone everywhere?
  - Are ACME/sslip operational limits documented clearly?
  - Are ADR titles, nav labels, and changelog entries accurate?
- Known risks to verify:
  - README/CLAUDE/docs index stale dependency language.
  - MkDocs nav label still says optional cryptography.
  - Runtime error text still recommends empty extra.

### api-documenter
- Relevant paths: `API.md`, `docs/api.md`, `README.md`, `src/handlers/*`, `src/request_pipeline.py`, `src/http/response.py`, `src/security/tls_manager.py`, `src/cli.py`.
- Questions:
  - Are method contracts, status codes, headers, error body formats, CORS behavior, NOTE/WebSocket behavior, TLS/ACME flags, and examples accurate?
  - Are receive-layer no-response close cases documented distinctly from JSON errors?
  - Are `--sslip` and `--letsencrypt` flows documented with constraints?
- Known risks to verify:
  - Docs mirrors are generated; source of truth must be root docs.
  - New ACME/sslip flags need API/CLI documentation consistency.

### reviewer
- Relevant paths: dirty diff from `git status --short`, especially `src/security/tls.py`, `src/security/tls_manager.py`, `src/cli.py`, `src/server.py`, tests, docs, constraints.
- Questions:
  - What correctness/security regressions are most likely in the current dirty diff?
  - Which findings should block merge versus become backlog?
  - Are tests and docs proportionate to the new TLS/ACME behavior?
- Known risks to verify:
  - Real ACME not run.
  - Key/cache edge cases.
  - Pre-commit/docs drift after runtime dependency change.
