# Project Analysis Report
_Generated: 2026-04-28 12:50:55 MSK_
_Agents used: 12_
_Output directory: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859_

## Executive Summary

ExperimentalHTTPServer is a compact Python HTTP/1.1 server with a clear learning-oriented architecture, broad tests, explicit docs, and several good security foundations: uploads are usually constrained with resolved paths, auth/rate-limit gates are centralized, TLS defaults are modern, Docker runs non-root, and docs mirrors are checked.

The audit found no critical issues, but it did find several high-impact gaps. The most urgent implementation issue is static asset path traversal: `/static/...` bypasses the safer uploads resolver and can resolve outside bundled assets. The next operational risk is large response buffering: gzip and SMUGGLE paths can read full user files into memory despite otherwise streamed file serving. The WebSocket path needs stricter RFC enforcement and connection-budget thinking. The UI currently depends on an untracked inspector asset and the inspector can expose advanced-upload secrets in raw/copy views.

Process and documentation risks are also material. CI/security checks have drift: `pip-audit --disable-pip` appears misapplied, pre-commit and CI tool versions disagree, `uv.lock` is untracked but divergent, and browser smoke relies on unpinned Playwright resolution. API docs overstate a uniform JSON contract and misdocument SMUGGLE. `CLAUDE.md` is stale enough to be risky because it describes removed flags and unsafe path-check guidance.

## Scope & Coverage

Analyzed repository root: `/home/user/PycharmProjects/ExperimentalHTTPServer`.

Covered areas: core socket server, request parsing, response finalization, file handlers, advanced upload, smuggling, WebSocket notepad flow, crypto/auth/TLS helpers, metrics, bundled UI, browser smoke, tests, docs, Docker, GitHub Actions, Dependabot, dependency constraints, package metadata, and generated docs mirrors.

Excluded by design: secret-heavy files, `.env*`, keys/certificates/credential JSON, and runtime/user data contents under `uploads/` and `notes/`. Generated/cache/dependency directories were not exhaustively traversed.

Context7 was available during preflight and Phase 1 and was used for `cryptography`, `pytest`, and `MkDocs` checks. Later agent attempts often hit Context7 monthly quota limits; those reports either used official primary docs as fallback or did not need external docs.

Coverage limitations: `python-pro` and `performance-engineer` reports note sandbox limitations in their subagent execution and completed the read-only audit through direct inspection. Most tests were not run by the parent audit; the WebSocket report did run targeted WebSocket/NOTE tests. `mkdocs` was not installed for the documentation agent's build check.

## Agents Used

| Agent | Role | Report | Status |
|---|---|---|---|
| security-auditor | Auth, path containment, crypto, CORS, TLS, advanced upload, security docs | `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/security-auditor.md` | completed |
| python-pro | Python runtime contracts, parser behavior, package data, metrics | `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/python-pro.md` | completed with sandbox fallback noted |
| architect-reviewer | Architecture, storage boundaries, ADR alignment | `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/architect-reviewer.md` | completed |
| websocket-engineer | RFC 6455 framing, upgrade/origin, WS notepad behavior | `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/websocket-engineer.md` | completed |
| performance-engineer | Memory, streaming, workers, benchmarks, metrics | `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/performance-engineer.md` | completed with sandbox fallback noted |
| qa-expert | Test gaps, CI test strategy, browser smoke risks | `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/qa-expert.md` | completed |
| devops-engineer | GitHub Actions, security scans, CI reproducibility | `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/devops-engineer.md` | completed |
| docker-expert | Dockerfile, Compose, image hardening, build context | `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/docker-expert.md` | completed |
| frontend-developer | Bundled UI, inspector redaction, a11y, browser smoke | `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/frontend-developer.md` | completed |
| documentation-engineer | Root docs, mirrors, stale docs, ADR/process accuracy | `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/documentation-engineer.md` | completed |
| dependency-manager | Dependency authority, constraints, lockfiles, Dependabot | `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/dependency-manager.md` | completed |
| api-documenter | API reference accuracy, headers/status/body contracts | `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/api-documenter.md` | completed |

## Critical & High Issues

| # | Severity | Issue | Source Agent(s) | File / Area | Recommended Fix |
|---|---|---|---|---|---|
| 1 | HIGH | Static asset path traversal can disclose files outside bundled UI assets | security-auditor | `src/handlers/files.py:44-49`, `src/handlers/base.py:25-55` | Reject `..`, absolute paths, and separator tricks in package-resource paths; require resolved assets to remain under `src/data`; add encoded traversal tests. |
| 2 | HIGH | Gzip and SMUGGLE can buffer large files fully in memory | performance-engineer, python-pro, qa-expert, architect-reviewer | `src/server.py:262`, `src/handlers/smuggle.py`, `src/utils/smuggling.py` | Skip gzip for streamed files or implement bounded streaming gzip; cap SMUGGLE source size and avoid serving generated HTML through full reads. |
| 3 | HIGH | Client WebSocket masking is not enforced | websocket-engineer, architect-reviewer, python-pro, qa-expert, security-auditor | `src/websocket.py:74-130`, `src/server.py:657-690` | Add inbound parser mode requiring masks; close unmasked client frames with `1002`; keep unmasked helpers only for server-frame tests. |
| 4 | HIGH | Required UI inspector asset is untracked and can be absent in clean checkout/package | frontend-developer, python-pro | `src/data/index.html:494`, `src/data/static/ui/inspector.js`, `pyproject.toml:79` | Commit `inspector.js` intentionally or remove its script tag and call sites; add package/static asset resolution tests. |
| 5 | HIGH | Inspector raw/copy path can expose advanced-upload secrets and payloads | frontend-developer | `src/data/static/ui/inspector.js`, `opsec.js`, `requests.js` | Centralize redaction before render and copy; redact keys/passwords/payloads/query params; remove or test-gate raw clipboard state. |
| 6 | HIGH | Docker build context can include runtime or secret-like files | docker-expert | `.dockerignore`, untracked `notes/` signal | Add `notes/`, `.env*`, key/cert, credential, and secret JSON patterns to `.dockerignore`, especially before remote builds. |
| 7 | HIGH | `pip-audit` security workflow likely uses the wrong mode | devops-engineer | `.github/workflows/security.yml:29-36` | Remove `--disable-pip` for installed-environment audit or switch to a documented hashed/no-deps requirements audit. |
| 8 | HIGH | API docs misdocument SMUGGLE response shape | api-documenter | `API.md:222`, `src/handlers/smuggle.py:75` | Update `API.md`/`docs/api.md` to describe JSON response, `X-Smuggle-URL`, follow-up GET, and temporary file behavior. |
| 9 | HIGH | API docs promise a global JSON error model that implementation does not provide | api-documenter | `API.md:7`, `src/handlers/files.py:331`, `src/handlers/info.py:36`, `src/handlers/advanced_upload.py:179` | Either normalize handler errors to JSON or document endpoint-specific text/empty/JSON error bodies. |
| 10 | HIGH | `CLAUDE.md` documents removed flags and unsafe path guidance | documentation-engineer, architect-reviewer, security-auditor | `CLAUDE.md:7`, `CLAUDE.md:22`, `CLAUDE.md:95` | Replace stale OPSEC/sandbox guidance with current `--advanced-upload` docs and remove `startswith()` path-check advice. |

## Architecture & Design

The current handler registry plus mixin model is acceptable for this project size. The main design risk is implicit handler context: handlers rely on server attributes such as upload paths, note paths, locks, metrics, crypto/session managers, and advanced-upload flags without one explicit interface.

Runtime storage boundaries are conceptually clean: user files live under `uploads/`, encrypted notes under `notes/`, and static UI under package data. The implementation breaks that boundary in two places: static resource resolution bypasses the safer descendant resolver, and `notes/` is not treated consistently as runtime data in ignore/build-context policies.

Package resource serving should move away from returning a `Path` from inside `importlib.resources.as_file()` when packaged loaders are possible. A byte/stream-serving abstraction would also make static path containment easier to reason about.

## Security & Compliance

Static asset traversal is the top security fix. It is reachable through normal HTTP GET/HEAD-style static serving and can disclose process-readable files when auth is disabled or valid credentials are supplied.

Hidden upload policy is inconsistent. GET and INFO block hidden files, but FETCH, SMUGGLE, and DELETE do not. Decide whether hidden files under `uploads/` are forbidden or merely hidden from listings, then enforce that policy uniformly.

Advanced upload should fail closed on authenticated decryption failure. AES-GCM wrong-key/tamper failures currently leave ciphertext accepted as a successful upload; no-crypto AES paths can silently write corrupted output. URL base64 decoding is also more lenient than other transports.

CORS handling needs a single-origin response contract. WebSocket origin checks split comma-separated origins, while HTTP responses emit the raw comma-separated string as `Access-Control-Allow-Origin`, which browsers reject.

The frontend inspector currently creates a client-side secrecy gap by retaining or copying raw payloads containing keys, note data, session identifiers, ciphertext, and base64 file content. Safe redaction should happen before both display and copy operations.

## Performance & Reliability

File responses are streamed in the plain path, but gzip post-processing converts streamed files into in-memory bodies. SMUGGLE generation adds more full-size representations. With the default `100 MB` upload cap and `10` workers, a small number of concurrent large compressible downloads can cause severe memory pressure.

The upload receive path buffers full requests before writing. Base64 advanced uploads and notepad save/load multiply payload memory through encoded and decoded copies. Size limits cap accepted payloads, not peak process memory.

Keep-alive and WebSocket connections share the fixed worker pool. Ten idle WebSockets or keep-alive connections can occupy all default workers, delaying normal HTTP requests. WebSocket partial-frame buffering can retain near-limit payloads and worker state across timeouts.

Metrics under-report application errors and lack performance signals. `total_errors` currently means mostly unhandled exceptions, not client-visible 4xx/5xx or handler-produced 500s, and there are no active connection, latency, byte, or WebSocket gauges.

## Code Quality & Maintainability

Malformed request parsing is too permissive. `HTTPRequest` can expose empty method/path after parse failure; with advanced upload enabled, malformed request lines with bodies can route into upload behavior instead of producing `400 Bad Request`.

Worker-level exceptions can disappear under a broad `except Exception: pass` in client handling. Pipeline exceptions are handled, but failures before or around request processing need structured logging and metrics.

Tests are broad, but several high-risk regressions are currently encoded as expected behavior or missing: unmasked WebSocket rejection, gzip streaming memory behavior, no-crypto AES upload behavior, malformed request lines, hidden-file method matrix, and static asset traversal.

## DevOps & Infrastructure

Dependency policy is split across broad `pyproject.toml` lower bounds, `constraints/ci.txt`, untracked `uv.lock`, and separate pre-commit hook revisions. CI and Docker use constraints, while local uv users can resolve different versions.

Pre-commit does not mirror CI: Ruff and mypy hooks are much older than constrained CI versions. `pre-commit` itself is a dev dependency but not pinned in `constraints/ci.txt`, so the pinned-toolchain claim is incomplete.

Dependabot covers pip and GitHub Actions but not pre-commit, Docker, or uv if `uv.lock` becomes authoritative. Python metadata allows `>=3.10`, but CI only tests through 3.13 even though Python 3.14 is stable as of October 7, 2025.

Docker has good foundations but needs safer context hygiene, base digest refresh policy, TLS/auth-aware healthcheck examples, bind-mount ownership guidance, stronger reproducibility if required, and basic Compose hardening.

## Frontend & UX

The bundled UI is tightly coupled to static package assets. `index.html` loads `inspector.js`, and feature modules call inspector APIs, but that file is currently untracked. This can break clean checkouts and packaged releases.

The advanced upload tab is always visible even though the server advertises `PING.advanced_upload` and unknown-method dispatch only works when `--advanced-upload` is enabled. The UI should disable, hide, or explain the feature based on server capability.

Notepad connection/save statuses update visually but are not live regions. Add `role="status"`, `aria-live="polite"`, and `aria-atomic="true"` to status surfaces.

Browser smoke has useful breadth, but it misses sensitive inspector redaction and has an assertion helper that ignores expected arguments. It also uses fixed sleeps and unpinned Playwright resolution.

## Data & ML

No database, ML, queue, cache, or analytics pipeline was found. Persistent runtime data is filesystem-backed under `uploads/` and `notes/`. The audit intentionally did not read user/runtime data contents.

## Product & Growth

No product/growth instrumentation was in scope or detected. Product-facing risk is primarily trust and usability: docs describe behavior clients cannot rely on, advanced upload can look available when server support is off, and lost WebSocket save acknowledgements can create duplicate notes.

## Documentation & Process

Root-canonical docs and generated mirrors are in sync, but several canonical docs are stale. `API.md` misstates SMUGGLE and global error behavior, INFO examples, CORS/preflight details, WebSocket failure semantics, and advanced-upload examples. `CHANGELOG.md` contradicts the current advanced-upload default. The threat model still treats Transfer-Encoding rejection as unfixed even though code rejects it.

`CONTRIBUTING.md` says `--check` regenerates docs mirrors, but `tools/sync_docs.py --check` only reports drift. MkDocs edit links may point contributors at generated mirror files instead of root-canonical sources.

## Quick Wins Backlog

| Priority | Task | Source Agent(s) | Area | Estimated Effort |
|---|---|---|---|---|
| P0 | Reject traversal in static package resource paths and add regression tests | security-auditor | Security | S |
| P0 | Stop gzip buffering for streamed files, at least by skipping gzip on `stream_path` | performance-engineer, python-pro, qa-expert | Performance | S |
| P0 | Enforce client masking for inbound WebSocket frames | websocket-engineer, qa-expert | WebSocket/Security | S |
| P0 | Track or remove `src/data/static/ui/inspector.js` | frontend-developer, python-pro | Frontend/Packaging | S |
| P0 | Redact advanced-upload keys and payloads before inspector render/copy | frontend-developer | Frontend/Security | M |
| P0 | Remove `--disable-pip` from `pip-audit` or switch audit mode intentionally | devops-engineer | CI/Security | S |
| P0 | Add missing `.dockerignore` runtime/secret patterns | docker-expert | Docker/Supply chain | S |
| P1 | Update `CLAUDE.md`, `API.md`, `CHANGELOG.md`, ADR-002, and threat model; regenerate docs mirrors | documentation-engineer, api-documenter | Docs | M |
| P1 | Align pre-commit Ruff/mypy with CI constraints | dependency-manager, devops-engineer | Tooling | S |
| P1 | Decide whether `uv.lock` is local-only or CI authority | dependency-manager, devops-engineer | Dependency policy | S |
| P1 | Add `notes/` to runtime-data ignore policies | architect-reviewer, docker-expert | Data hygiene | S |
| P1 | Normalize or document handler error response bodies | api-documenter | API | M |
| P1 | Fix browser smoke preview-toggle assertion and add redaction/static-asset checks | frontend-developer | QA/Frontend | S |

## Deeper Improvements Roadmap

- Make request parsing explicit: return a typed parse result or controlled parse exception and reject invalid method/path/version before auth and dispatch.
- Define a small handler context/protocol so handler dependencies are explicit without rewriting the server into a framework.
- Stream uploads to temporary files for standard upload methods, and add early `Content-Length` rejection before full body reads.
- Add WebSocket protocol validation for FIN/fragmentation, RSV bits, unknown opcodes, control frames, close payloads, and missing Host; add an incomplete-frame idle deadline.
- Add WebSocket operation IDs or client-generated IDs so lost save acknowledgements cannot duplicate new notes after reconnect.
- Redesign metrics around a clear contract: status-class counters, handler-produced 5xx, latency, bytes, active workers/connections, WebSocket counts, and queue pressure.
- Adopt one dependency authority: either keep constraints as source of truth or commit/use `uv.lock` with `uv sync --locked`; then configure Dependabot accordingly.
- Harden Docker/Compose for production use if the examples are meant beyond local dev: named volume or UID guidance, healthcheck overrides, `cap_drop`, `no-new-privileges`, read-only root where practical, and base digest refresh automation.

## Full Recommended Action Plan

### Immediate

1. Fix static asset traversal.
2. Prevent gzip/SMUGGLE large-file buffering from defeating streaming.
3. Enforce inbound WebSocket masking.
4. Fix the inspector asset and redaction leaks.
5. Repair the `pip-audit` workflow command.
6. Expand `.dockerignore` for runtime/secret-like files.

### Short Term

1. Normalize malformed request handling to `400 Bad Request` before dispatch.
2. Fail closed for advanced-upload AES-GCM decryption/authentication failures and reject AES mode when `cryptography` is unavailable.
3. Make hidden-file policy consistent across GET, INFO, FETCH, SMUGGLE, and DELETE.
4. Align pre-commit, constraints, and lockfile policy; add Dependabot pre-commit and Docker coverage where desired.
5. Update API/docs drift and regenerate mirrors.
6. Add focused regression tests for the high-risk findings.

### Medium Term

1. Stream standard upload bodies to disk and cap memory-heavy advanced upload transports.
2. Add WebSocket fragmentation/RSV/opcode/close validation and connection budgets.
3. Expand metrics into a useful operational surface.
4. Add benchmarks for large GET, gzip GET, upload, advanced upload, SMUGGLE, and slow WebSocket frames.
5. Add Python 3.14 CI coverage or narrow documented Python support.

### Long Term

1. Decide whether this server should remain a local/learning tool or support hardened public deployments; let that decision drive Docker, TLS/proxy, auth, WebSocket concurrency, and observability investments.
2. Move package resource serving to a byte/stream abstraction with explicit containment.
3. Add a stable client-facing API compatibility policy for custom methods, NOTE, WebSocket, errors, request IDs, and CORS.

## Open Questions for the Team

- Should hidden files under `uploads/` be completely inaccessible, or only hidden from GET/INFO?
- Is `--cors-origin` intended to support multiple origins, or should commas be rejected early?
- Should advanced upload remain best-effort on decryption failure, or fail closed?
- Is `uv.lock` intended to become the authoritative lockfile, or should `constraints/ci.txt` remain the only CI authority?
- Should Python 3.14 be officially supported now?
- Should raw inspector output be exact wire payload or safe-shareable by default?
- Should advanced-upload responses include the actual saved filename/path?
- Is the Docker example local-only, or should it be production-hardened?
- Should `CLAUDE.md` remain a maintained guide or become a redirect to canonical docs?

## Appendix: Source Reports

- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/security-auditor.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/python-pro.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/architect-reviewer.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/websocket-engineer.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/performance-engineer.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/qa-expert.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/devops-engineer.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/docker-expert.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/frontend-developer.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/documentation-engineer.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/dependency-manager.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/api-documenter.md`
