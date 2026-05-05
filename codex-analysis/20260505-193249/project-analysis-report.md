# Project Analysis Report
_Generated: 2026-05-05 20:49:50 Europe/Moscow_
_Agents used: 14_
_Output directory: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260505-193249_

## Executive Summary

ExperimentalHTTPServer has a coherent core architecture and a broad test suite, but the current dirty TLS/ACME/dependency change is not merge-ready. The strongest risks are clustered around four areas: Secure Notepad cryptographic contract drift, ACME/TLS operational edge cases, CI/release smoke reliability, and dependency/docs drift after moving crypto/ACME into runtime dependencies.

No CRITICAL issues were reported. The HIGH issues are actionable blockers: the Secure Notepad example/API contract can produce incompatible or unrecoverable notes, release smoke currently exits before browser/Docker validation, and the documented/container ACME path is incomplete enough that operators can follow it and still fail issuance.

Positive signals are also real: request framing rejects dangerous transfer/body combinations, path containment and hidden-file checks are strong, CORS/WebSocket origin checks are explicit, file downloads stream, dependency constraints are mostly coherent, generated docs mirrors are in sync, and the UI has targeted inspector redaction coverage.

## Scope & Coverage

The audit covered Python runtime code, CLI/TLS/ACME flow, request parsing, handlers, WebSocket/Secure Notepad, bundled frontend UI, tests, CI/security workflows, dependency constraints, Docker/Compose, public API docs, README/docs/ADR content, and the current dirty worktree.

Context7 or current docs checks were used by agents for `cryptography`, Certbot `acme`, `pytest`, Python `argparse`/`ThreadPoolExecutor`, browser WebSocket/CSP behavior, and dependency ecosystem guidance where needed. No Context7 blocker occurred.

Runtime limitations: live ACME issuance, full pytest, benchmark/load testing, browser smoke, and Docker image run were not executed by the parent Phase 3. Some subagents performed read-only validation commands such as pytest collect-only, docs sync, MkDocs strict build, Compose config, and Dockerfile check. The reviewer reported an internal read-only sandbox problem in its own nested attempt, but completed a host-side read-only review.

## Agents Used

| Agent | Role | Report | Status |
|---|---|---|---|
| security-auditor | Security boundaries, auth, TLS/ACME, CORS, file safety, UI exposure | `agent-reports/security-auditor.md` | completed |
| python-pro | Python runtime, packaging, typing, filesystem behavior | `agent-reports/python-pro.md` | completed |
| architect-reviewer | Module boundaries, storage boundaries, ADR/design drift | `agent-reports/architect-reviewer.md` | completed |
| websocket-engineer | WebSocket and Secure Notepad transport semantics | `agent-reports/websocket-engineer.md` | completed |
| performance-engineer | Buffering, concurrency, metrics, startup latency | `agent-reports/performance-engineer.md` | completed |
| cli-developer | CLI validation and TLS/ACME flag ergonomics | `agent-reports/cli-developer.md` | completed |
| qa-expert | Test strategy and coverage gaps | `agent-reports/qa-expert.md` | completed |
| devops-engineer | CI, release smoke, security workflow, pre-commit, process | `agent-reports/devops-engineer.md` | completed |
| dependency-manager | Constraints, dependency policy, Dependabot, local env drift | `agent-reports/dependency-manager.md` | completed |
| docker-expert | Dockerfile, Compose, non-root runtime, healthchecks, ACME in containers | `agent-reports/docker-expert.md` | completed |
| frontend-developer | Bundled UI safety, Notepad UX/state, smoke coverage | `agent-reports/frontend-developer.md` | completed |
| documentation-engineer | Docs/API/ADR/README/examples consistency | `agent-reports/documentation-engineer.md` | completed |
| api-documenter | Public API contract and examples | `agent-reports/api-documenter.md` | completed |
| reviewer | PR-style dirty diff risk ranking | `agent-reports/reviewer.md` | completed |

## Critical & High Issues

| # | Severity | Issue | Source Agent(s) | File / Area | Recommended Fix |
|---|---|---|---|---|---|
| 1 | HIGH | Secure Notepad key/API/example contract is inconsistent and recoverability is undefined | websocket-engineer, api-documenter, reviewer, qa-expert, documentation-engineer, frontend-developer | `examples/notepad_client.py`, `src/security/keys.py`, `src/data/static/ui/notepad.js`, `API.md` | Fix HKDF constants in the example; document exact salt/info, plaintext metadata, and recoverability limits; add interoperability tests. |
| 2 | HIGH | Release smoke fails before browser/Docker validation | devops-engineer, reviewer | `.github/workflows/ci.yml`, `docs/changelog.md` | Replace or narrow the stale-doc grep so valid changelog text does not abort smoke. |
| 3 | HIGH | Container ACME/sslip path is incomplete | docker-expert, devops-engineer, reviewer, api-documenter | `examples/docker/docker-compose.yml`, `Dockerfile`, `README.md`, `src/security/tls.py` | Add working Docker/NAT guidance or Compose profile with port 80/443 mapping, writable ACME state, and healthcheck override. |

## Architecture & Design

- Handler/server/request-pipeline boundaries are mostly coherent after TLS/ACME changes. `TLSManager` owns certificate acquisition/context setup, `server.py` owns lifecycle/socket display state, `RequestPipeline` owns parse/auth/dispatch/upgrade, and `NotepadService` owns storage.
- Storage boundaries are under-documented: architecture docs identify uploads, but not `<root>/notes`, `~/.exphttp/acme`, ACME account/domain keys, or legacy `~/.exphttp/letsencrypt` read behavior.
- Legacy `check_openssl_available()` and `check_certbot_available()` helpers remain exposed and can mislead contributors into thinking external binaries are runtime blockers.
- Secure Notepad needs an explicit product/architecture decision: durable notes across reload/restart require a recoverable key strategy; session-only notes need clear UI/API docs and behavior.

## Security & Compliance

- Strong controls: Basic Auth uses PBKDF2 plus dummy verification/rate limiting; path containment uses resolved paths and hidden-file checks; CORS is explicit and does not emit credentials; WebSocket upgrades validate origin and handshake headers; advanced upload verifies HMAC before decrypting.
- MEDIUM: `TLSManager._try_letsencrypt()` reuses a fresh `fullchain.pem` without checking `privkey.pem` exists, parses, or matches. This is fail-closed but not recoverable, and the reviewer marked it as a blocker unless fail-late behavior is explicitly accepted.
- MEDIUM: CLI TLS source validation can silently choose the wrong mode. `--key` alone can start plaintext because it does not enable TLS; cert/key combined with ACME is not rejected and ACME silently wins.
- MEDIUM: Secure Notepad title metadata is plaintext while UI/docs imply broad end-to-end encryption. Users may place sensitive data in titles.
- LOW: CSP still allows inline scripts/styles. No confirmed XSS was found, but this reduces containment if future `innerHTML` escaping regresses.

## Performance & Reliability

- MEDIUM: Advanced upload JSON body transport parses the full JSON body before applying the advanced-upload encoded-size cap, so it can consume avoidable CPU/memory under large bodies.
- MEDIUM: The worker pool has no global admission/backpressure. Slow uploads, idle keep-alive, and long WebSockets can occupy workers and queue normal requests.
- MEDIUM: Upload writes use check-then-open `"wb"` rather than exclusive creation; concurrent uploads of the same name can overwrite/truncate. Secure Notepad writes ciphertext and metadata non-atomically.
- LOW: ACME/sslip setup can block startup before the main server listens; metrics lack request latency, active worker/connection, timeout/drop, and upload rejection signals.

## Code Quality & Maintainability

- MEDIUM: CLI lower-bound validation is incomplete for `--port`, `--max-size`, and `--workers`; failures surface later from socket/thread/request code.
- MEDIUM: Runtime import boundary is heavy: importing package root reaches `src/security/tls.py` and therefore `acme`/`cryptography`/`josepy`.
- LOW: Connection-level exceptions in `_handle_client()` are swallowed without observability.
- LOW: CLI help omits supported methods such as `NOTE`, `HEAD`, `PATCH`, and `DELETE`.

## DevOps & Infrastructure

- HIGH: release smoke is currently blocked by its own stale-doc grep, preventing browser and Docker smoke from running.
- MEDIUM: pre-commit mypy uses an isolated dependency environment that lacks `acme`/`josepy` and pins `cryptography==46.0.5` while runtime requires `cryptography>=48.0`.
- MEDIUM: `pip-audit` audits `constraints/ci.txt`, but there is no installed-environment completeness check proving every installed package is pinned/audited.
- MEDIUM: Docker smoke checks `--version` and plain HTTP PING only. It does not verify runtime imports, TLS mode, or healthcheck override behavior.
- MEDIUM: ignored local files `tools/close_plan_stages.py` and `tests/test_close_plan_stages.py` are collected locally but absent in CI checkout, creating local/CI confidence drift.

## Frontend & UX

- MEDIUM: Notepad dirty edits can be lost if the user switches/creates notes before debounce save finishes.
- MEDIUM: WebSocket Notepad save has no operation id, ack tracking, retry, or fallback; reconnect can churn sockets and duplicate create side effects.
- MEDIUM: frontend strings still mention `exphttp[crypto]`, and smoke tests lock in that stale copy.
- LOW: TLS/sslip/ACME state is not surfaced in the UI; the header still says "Local console" even on public/TLS deployments.
- LOW: WebSocket `load` is implemented server-side but unused by the UI.
- LOW: Current `innerHTML` sites mostly escape or control data, but smoke coverage is not systematic for hostile filenames, note titles, paths, and inspector summaries.

## Data & ML

No database, ML pipeline, model-serving, or analytics data layer was found. The relevant persistence concerns are filesystem-backed uploads, notes, metadata sidecars, and ACME key/cert cache.

## Product & Growth

The server is feature-rich for an experimental HTTP tool, but public-facing confidence depends on matching claims to behavior. The Secure Notepad promise and ACME/sslip convenience story need tighter product wording: either implement durability/container-safe operations, or document the current constraints plainly.

## Documentation & Process

- MEDIUM: dependency-policy migration is only partially reflected. README/CLAUDE/docs still contain pure Python or zero-dependency claims, while `pyproject.toml` has runtime `acme` and `cryptography`.
- MEDIUM: runtime/UI/docs still tell users to install `exphttp[crypto]`, but `[crypto]` is an empty compatibility extra.
- MEDIUM: ACME/sslip docs omit `api.ipify.org`, global IPv4, Docker/NAT/volume requirements, unsupported wildcard/DNS-01, and cache repair behavior.
- LOW: MkDocs ADR-003 nav label still says "Optional cryptography"; architecture docs omit notes/ACME persistence boundaries.
- LOW: README upload response-header table omits POST/PUT/PATCH aliases documented correctly in `API.md`.

## Quick Wins Backlog

| Priority | Task | Source Agent(s) | Area | Estimated Effort |
|---|---|---|---|---|
| P0 | Fix release-smoke stale-doc grep false positive | devops-engineer, reviewer | CI | Small |
| P0 | Fix `examples/notepad_client.py` HKDF salt/info and add interoperability test | websocket-engineer, qa-expert, api-documenter, reviewer | Secure Notepad | Small/Medium |
| P0 | Validate ACME cert/key pair before reuse; add missing-key test | security-auditor, python-pro, architect-reviewer, qa-expert, reviewer | TLS/ACME | Medium |
| P0 | Add CLI validation for key/cert/ACME combinations and numeric lower bounds | cli-developer, python-pro, performance-engineer, reviewer | CLI | Medium |
| P1 | Replace `exphttp[crypto]` runtime/UI/docs strings | architect-reviewer, frontend-developer, documentation-engineer, dependency-manager | Docs/UI/runtime | Small |
| P1 | Update pre-commit mypy dependencies to match constraints | python-pro, devops-engineer, dependency-manager | Tooling | Small |
| P1 | Document ACME/sslip Docker/NAT ports, writable cache, `api.ipify.org`, healthcheck override | docker-expert, api-documenter, documentation-engineer | Ops docs | Small/Medium |
| P1 | Add README/CLAUDE/docs dependency wording fixes and MkDocs ADR label update | documentation-engineer, architect-reviewer | Docs | Small |
| P1 | Add tests for invalid `--port`, `--max-size`, `--workers`, and TLS source combinations | cli-developer, qa-expert | Tests | Small/Medium |
| P2 | Add hostile UI string smoke cases for filenames, note titles, paths, inspector summaries | frontend-developer, qa-expert, security-auditor | UI tests | Medium |

## Deeper Improvements Roadmap

- Define the Secure Notepad durability model. If durable notes are required, design client key persistence/recovery/migration. If not, make session-key-bound behavior explicit and prevent stale ciphertext from looking normally loadable.
- Add ACME operational hardening: configurable ACME cache directory, cert/key pair health command, manual staging smoke, and clear renewal/cache repair procedure.
- Add global connection admission/backpressure and expose resource/latency metrics.
- Make upload and note writes atomic/exclusive using same-directory temp files, `replace()`, or exclusive create/retry helpers.
- Stream standard uploads to disk instead of buffering full request bodies.
- Move high-risk frontend markup toward DOM builders or escaping-enforced helpers, then tighten CSP.
- Add installed-environment dependency completeness/audit checks and a documented constraints refresh process.

## Full Recommended Action Plan

### Immediate

1. Fix release smoke so browser/Docker validation can run.
2. Fix Secure Notepad HKDF mismatch and document exact key contract in `API.md`.
3. Add ACME cert/key pair validation before cache reuse.
4. Normalize CLI validation for TLS source combinations and numeric bounds.
5. Update stale `exphttp[crypto]` guidance in backend, UI, smoke expectations, and docs.

### Short Term

1. Add focused regression tests: ACME fresh cert/missing key, invalid CLI values, example Notepad interoperability, dirty Notepad note switching, and WS save retry behavior.
2. Update pre-commit mypy dependencies and add clean-env import/`pip check` smoke.
3. Add ACME/sslip Docker/NAT docs and healthcheck override guidance.
4. Resolve ignored local tests/tools by tracking them, moving them out of `tests/`, or explicitly ignoring them.
5. Add architecture persistence section for uploads, notes, ACME account/domain keys, and legacy cert cache.

### Medium Term

1. Add Docker TLS smoke and possibly a manual ACME staging workflow.
2. Add installed-environment audit/completeness checks beyond `pip-audit -r constraints/ci.txt`.
3. Add resource metrics and connection admission/backpressure.
4. Make upload/note writes atomic/exclusive.
5. Expand frontend/security smoke coverage for escaped UI render paths.

### Long Term

1. Decide whether ACME is a convenience mode or production-grade path; if production-grade, add config for cache directory, renewal checks, and operational runbooks.
2. Decide whether Secure Notepad should provide reload/restart durability; implement or document accordingly.
3. Generate selected API/README method/header tables from tests or a single source of truth.
4. Consider SBOM/license review for the expanded runtime dependency surface.

## Open Questions for the Team

- Should Secure Notepad titles be encrypted, or are they intentionally plaintext metadata?
- Should notes remain decryptable after browser reload and server restart?
- Should broken ACME cache auto-renew, or fail early with manual repair instructions to avoid rate-limit pressure?
- Should `--sslip` require or warn about public binding such as `-H 0.0.0.0`?
- Should ACME cache location be configurable for containers?
- Should `[crypto]` remain visible anywhere, or exist only as a silent compatibility extra?
- Are `tools/close_plan_stages.py` and `tests/test_close_plan_stages.py` project-supported files, local-only agent tooling, or files that should be excluded from local pytest?
- Is live ACME staging acceptable as a manual release gate with owned domain/port-80 infrastructure?

## Appendix: Source Reports

- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260505-193249/preflight.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260505-193249/agents-inventory.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260505-193249/analysis-plan.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260505-193249/agent-reports/security-auditor.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260505-193249/agent-reports/python-pro.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260505-193249/agent-reports/architect-reviewer.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260505-193249/agent-reports/websocket-engineer.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260505-193249/agent-reports/performance-engineer.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260505-193249/agent-reports/cli-developer.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260505-193249/agent-reports/qa-expert.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260505-193249/agent-reports/devops-engineer.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260505-193249/agent-reports/dependency-manager.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260505-193249/agent-reports/docker-expert.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260505-193249/agent-reports/frontend-developer.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260505-193249/agent-reports/documentation-engineer.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260505-193249/agent-reports/api-documenter.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260505-193249/agent-reports/reviewer.md`
