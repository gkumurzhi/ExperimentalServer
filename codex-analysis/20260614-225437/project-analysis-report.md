# Project Analysis Report
_Generated: 2026-06-15 00:58:23 Europe/Moscow_
_Agents used: 14_
_Output directory: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437_

## Executive Summary

The previous remediation plan, `implementation-plan/20260525-133607`, is closed. The next useful work is not another broad cleanup pass; it is choosing the product direction and then tightening the project around that choice.

The strongest recommendation across agents is to pursue a safe-by-default file workspace path: make `workspace` the new-user direction, preserve `lab` as explicit opt-in for compatibility, and postpone public API, durable Notepad, and registry publishing until support boundaries are explicit.

No CRITICAL or HIGH severity exploit/regression was found. The important findings are Medium-level operational, product, API, performance, and documentation risks that become serious if the project is promoted beyond trusted lab usage.

The immediate blocker is concrete: `python tools/sync_docs.py --check` fails because `API.md -> docs/api.md` and `CONTRIBUTING.md -> docs/contributing.md` are out of sync.

## Scope & Coverage

This audit used the confirmed `analysis-plan.md` and 14 subagent reports. The source tree was kept read-only; only generated analysis artifacts were written under this run directory.

Context7 was available and used during planning for current `cryptography`, `pytest`, and Docker guidance. Python release status was checked because interpreter support is date-sensitive. Most subagents did not need fresh Context7 calls because their recommendations were repository-local.

Validation signals observed during the audit:
- `python tools/sync_docs.py --check` failed on docs mirrors.
- `python tools/check_stale_docs.py` passed.
- `python tools/check_pytest_collection_policy.py` passed.
- `python tools/check_static_ui_assets.py --repo-root .` passed in frontend/a11y passes.

## Agents Used

| Agent | Role | Report | Status |
|---|---|---|---|
| product-manager | Product direction and prioritization | `agent-reports/product-manager.md` | completed |
| architect-reviewer | Architecture and boundaries | `agent-reports/architect-reviewer.md` | completed |
| security-auditor | Security posture and abuse paths | `agent-reports/security-auditor.md` | completed |
| api-designer | API contract and compatibility | `agent-reports/api-designer.md` | completed |
| qa-expert | Test strategy and release gates | `agent-reports/qa-expert.md` | completed |
| websocket-engineer | WebSocket/Notepad transport | `agent-reports/websocket-engineer.md` | completed |
| performance-engineer | Runtime hot paths and metrics | `agent-reports/performance-engineer.md` | completed |
| devops-engineer | CI/release/ops control plane | `agent-reports/devops-engineer.md` | completed |
| dependency-manager | Python/dependency policy | `agent-reports/dependency-manager.md` | completed |
| documentation-engineer | Docs consistency and release notes | `agent-reports/documentation-engineer.md` | completed |
| docker-expert | Container build/runtime posture | `agent-reports/docker-expert.md` | completed |
| frontend-developer | Static UI product behavior | `agent-reports/frontend-developer.md` | completed |
| accessibility-tester | Accessibility and interaction coverage | `agent-reports/accessibility-tester.md` | completed |
| project-manager | Staged roadmap synthesis | `agent-reports/project-manager.md` | completed |

## Critical & High Issues

No CRITICAL or HIGH issues were identified by the specialist reports.

| # | Severity | Issue | Source Agent(s) | File / Area | Recommended Fix |
|---|---|---|---|---|---|
| 1 | None | No CRITICAL/HIGH finding | all | repository | Focus first on Medium roadmap blockers below |

## Key Medium Issues

| Priority | Issue | Source Agent(s) | File / Area | Recommended Fix |
|---|---|---|---|---|
| P0 | Docs mirrors are out of sync | product-manager, qa-expert, documentation-engineer, devops-engineer | `API.md`, `docs/api.md`, `CONTRIBUTING.md`, `docs/contributing.md` | Regenerate mirrors, add local pre-commit/PR guardrails |
| P0 | `lab` default conflicts with safe new-user posture | product-manager, security-auditor, docker-expert | `src/features.py`, `src/cli.py`, `Dockerfile`, README/SECURITY | Decide default policy; likely migrate new-user path to `workspace` with `lab` opt-in |
| P1 | Capability/profile policy is scattered | architect-reviewer | `src/features.py`, `src/server.py`, handlers, UI | Centralize profile-derived policy before default migration |
| P1 | Reverse-proxy client identity is under-specified | security-auditor | `src/server.py`, `src/security/auth.py`, SECURITY docs | Document direct-peer IP semantics; add trusted-proxy model only if officially supported |
| P1 | Release rollback artifacts expire too quickly | devops-engineer | `.github/workflows/release.yml`, CONTRIBUTING | Use durable GitHub Release assets or longer retention |
| P1 | Python 3.14 support is blocked by policy, not known failures | dependency-manager | `pyproject.toml`, CI matrix, docs | Add 3.14 CI first, then widen metadata if clean |
| P1 | Browser/UI smoke is lab-only | qa-expert, frontend-developer, accessibility-tester | `tools/browser_smoke.py`, UI | Add minimal `serve`/`workspace` disabled-state smoke |
| P1 | Notepad UI under-surfaces capability and recovery risk | frontend-developer, accessibility-tester | `src/data/static/ui/notepad.js`, `index.html`, API docs | Gate `note_delete`/`note_clear`; render ephemeral warning; improve labels/errors |
| P2 | API lacks explicit v0/v1 boundary | api-designer | `API.md`, `PING`, error shapes, WebSocket messages | Document current API as legacy v0; design v1 before clients |
| P2 | Upload/listing hot paths lack benchmarks and some bounds | performance-engineer | `src/storage.py`, `src/handlers/info.py`, metrics | Add benchmarks; avoid quota scan when no limits; improve metrics |
| P2 | WebSocket is lab-grade, not workspace sync-grade | websocket-engineer | `src/websocket.py`, `src/server.py`, `src/handlers/notepad.py` | Document `opId`; add capability checks and send-failure visibility |

## Architecture & Design

The architecture is coherent after the previous remediation plan. The server lifecycle, request pipeline, handler registry, package shims, upload storage, Notepad storage, and WebSocket helpers are understandable and tested.

The main architecture risk is policy sprawl. Profile capability decisions are defined in `src/features.py`, then interpreted across `src/server.py`, CORS handling, handlers, static UI, docs, and tests. Before changing the default profile, create a small capability-policy boundary or strengthen `FeatureSet` helpers so one profile change flows consistently through:
- `PING`/capabilities.
- handler registry.
- CORS preflight.
- browser-origin mutation guard.
- WebSocket route admission.
- static UI affordances.

SMUGGLE temporary files are another boundary to watch. They live under `uploads/` but have their own lifecycle/quota logic. This is acceptable for lab usage, but should be clarified before upload storage becomes a stronger product promise.

## Security & Compliance

Current controls are consistent with trusted-lab/local usage. No immediate severe exploit was identified.

The security posture changes if the project is packaged or exposed broadly. `lab` enables destructive and experimental methods. Docker's raw default command binds `0.0.0.0` without profile/auth/TLS arguments. Compose mitigates this with loopback binding, but simple `docker run -p` usage can expose the full lab surface.

Basic Auth rate limiting keys on the direct socket peer IP. Behind a reverse proxy, the app will see the proxy IP unless a trusted-proxy model is added. The safest current position is to document that app-side auth throttling is direct-peer only, and that proxied deployments require proxy-side per-client throttling.

Durable Secure Notepad is not a small feature. Existing ECDH sessions are short-lived and audit-only. Recovery must be designed with envelope encryption, key wrapping, unique AES-GCM nonces, metadata versioning, and test vectors. Do not persist current session AES keys as a shortcut.

## Performance & Reliability

The reliability envelope is much better than before the closed plan: body admission, quotas, slow-body controls, WebSocket slots, and metrics exist.

The next performance work should be evidence gathering and targeted fixes:
- Add benchmarks for upload publish paths, quota scans, large `INFO` listings, Notepad save/list near limits, slow body behavior under worker pressure, and WebSocket slot saturation.
- Short-circuit upload quota scans when aggregate upload limits are disabled.
- Decide whether `INFO.total_items` must remain exact for very large directories.
- Add phase timings or latency buckets only if `/metrics` becomes an operator-facing contract.

## Code Quality & Maintainability

The package identity migration to `exphttp` appears coherent. Public shims and compatibility paths are in place.

The strongest maintainability improvement is not a broad refactor. It is making capability/profile behavior declarative enough that server, handlers, UI, CORS, docs, and smoke tests share one contract. Handler DI and an upgrade router can wait until extension pressure is real.

## DevOps & Infrastructure

CI is broad: Python matrix, docs, cross-platform smoke, release smoke, browser smoke, Docker smoke, security audit, and Bandit are present.

The release lane builds wheel/sdist, runs installed-package smoke, generates dependency SBOM, and creates attestations. It does not publish. That is acceptable if intentional, but docs should avoid implying durable public artifacts unless GitHub Releases, PyPI, or GHCR are actually used.

Python 3.14 should be handled as a separate readiness stage: add it to CI under constraints first; only then update metadata/classifiers/docs. Do not combine interpreter support, dependency refresh, and default-profile migration in one change.

Docker should remain an example/operator convenience unless ownership is expanded. A published image needs image scan, SBOM/provenance, digest rollback, tag policy, and clear CVE response ownership.

## Frontend & UX

The static no-build UI is reasonable for the current scope. It has clear module boundaries and uses `PING` capabilities for many affordances.

Before a `workspace` default migration, fix these UI gaps:
- Notepad controls should honor `note_delete` and `note_clear`, not only coarse `note_http` availability.
- The Notepad ephemeral/recovery warning exists in translation text but is not rendered.
- Notepad textarea needs an explicit accessible label.
- Upload progress and per-file failures need better live/status feedback.
- Browser smoke should cover minimal `serve` and `workspace` disabled states.

Do not add a frontend build pipeline solely for a default-profile migration. A small frontend capability/action manifest is enough for the next stage.

## Data & ML

No database, cache, queue, analytics pipeline, or ML component exists in this repository. The data layer is local filesystem storage for uploads, notes, and generated temporary artifacts.

## Product & Growth

The next product path should be:

1. Safe file workspace first.
2. Lab features preserved as explicit opt-in.
3. Distribution, public API, and durable Notepad as separate strategic tracks.

Recommended paths:
- **Conservative hardening:** keep trusted-lab positioning, fix docs and tests, keep `lab` default for now.
- **Safe-by-default workspace:** migrate new-user default to `workspace`, keep `--profile lab`, and harden UI/docs/CI around profiles. This is the recommended primary path.
- **Distribution/ops:** publish durable artifacts only after support, rollback, and ownership are clear.
- **API platform:** declare legacy v0 first; build v1 only if clients/SDKs are a real goal.
- **Durable secure workspace:** write a Notepad crypto/product ADR before implementation.

## Documentation & Process

Docs drift is the immediate fix. After mirrors are regenerated:
- Add docs sync/stale-doc checks to pre-commit or PR requirements.
- Move the completed remediation work out of an indefinite `[Unreleased]` changelog block or add a dated migration boundary.
- Add a first-path profile decision table: `serve`, `workspace`, `lab`.
- Add API contract stability language: current behavior is v0/legacy; v1 is future opt-in work.
- Add `SECURITY.md` guidance for direct-peer IP rate limiting and reverse proxies.
- Update architecture docs to include `features.py`, `storage.py`, and capability flow.

## Quick Wins Backlog

| Priority | Task | Source Agent(s) | Area | Estimated Effort |
|---|---|---|---|---|
| 1 | Run `python tools/sync_docs.py --write`, then verify `--check` | product, QA, docs, DevOps | Docs | Small |
| 2 | Add docs sync/stale-doc hooks to pre-commit/PR checklist | QA, docs, DevOps | Process | Small |
| 3 | Add profile/default ADR or decision note | product, security, project | Product | Small |
| 4 | Add `SECURITY.md` "Client IP and proxies" section | security, docs | Security docs | Small |
| 5 | Render Notepad ephemeral warning and add textarea label | frontend, accessibility | UI/a11y | Small |
| 6 | Gate Notepad UI and WS delete/clear with destructive capabilities | security, WS, frontend | UI/backend | Small/Medium |
| 7 | Add one `workspace` browser smoke path | QA, frontend, accessibility | CI/UI | Medium |
| 8 | Add Python support table and 3.14 CI readiness stage | dependency, DevOps | Dependencies | Medium |
| 9 | Make Docker examples explicit about safe profile and loopback binding | Docker, security, docs | Docker/docs | Small |
| 10 | Add upload/listing benchmarks and no-limit quota-scan test | performance | Performance | Medium |

## Deeper Improvements Roadmap

### Safe Workspace Train
- Centralize capability policy.
- Migrate default to `workspace` if approved.
- Keep `--profile lab` compatibility.
- Add profile-aware browser smoke and a11y checks.
- Add risk-specific QA lanes and coverage baselines.

### Reliability Train
- Benchmark uploads, listings, Notepad storage, and WebSocket slots.
- Remove unnecessary quota scans for unlimited policies.
- Decide whether directory listing should use cursor/bounded semantics.
- Add metrics only where they inform operator decisions.

### API Train
- Document current behavior as legacy v0.
- Add additive discovery fields and stable error codes.
- Design opt-in `/api/v1` only before SDK/client work.
- Keep SMUGGLE and advanced upload lab-only unless product direction changes.

### Distribution Train
- Decide whether GitHub Releases are the durable artifact of record.
- Add release promotion gates before PyPI/GHCR.
- For GHCR, add image scan, image SBOM/provenance, digest rollback, and tag policy.

### Secure Notepad Train
- Write crypto/product ADR first.
- Define recovery model, key wrapping, metadata privacy, and test vectors.
- Only then consider durable notes, revisions, conflict handling, and WebSocket resume.

## Full Recommended Action Plan

### Immediate
- Fix docs mirrors.
- Add docs drift prevention.
- Record profile/default decision.
- Clarify Docker and reverse-proxy safety docs.
- Add dated changelog/release boundary.

### Short Term
- Centralize capability policy.
- If approved, migrate default to `workspace`.
- Harden UI/a11y around Notepad and profile-disabled states.
- Add risk-specific QA lanes.
- Add Python 3.14 CI readiness.
- Make Docker examples explicit and safe.

### Medium Term
- Add performance benchmarks and fix no-limit quota scan.
- Document API v0 and design optional v1.
- Improve WebSocket Notepad safety around capability checks, `opId`, send failures, and binary-frame policy.
- Create durable artifact/rollback policy if release maturity increases.

### Long Term
- Decide whether the project is a safe workspace, API platform, durable encrypted workspace, or packaged ops product.
- Add trusted-proxy support only if reverse-proxy deployment becomes officially supported.
- Add PyPI/GHCR publishing only with ownership and rollback guarantees.

## Open Questions for the Team

- Should `workspace` become the new-user default, and when?
- Should Docker defaults diverge from CLI defaults?
- Is untrusted internet exposure unsupported, proxy-owned, or app-supported?
- Is Secure Notepad ephemeral or durable?
- Should release artifacts become durable GitHub Release assets?
- Does the project promise compatibility with unconstrained PyPI installs or only pinned CI/release dependencies?
- What workload defines "wider use" for files, upload sizes, clients, and directories?
- Should API clients target legacy custom methods or future standard v1 endpoints?

## Appendix: Source Reports

- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/preflight.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/agents-inventory.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/analysis-plan.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/agent-reports/product-manager.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/agent-reports/architect-reviewer.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/agent-reports/security-auditor.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/agent-reports/api-designer.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/agent-reports/qa-expert.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/agent-reports/websocket-engineer.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/agent-reports/performance-engineer.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/agent-reports/devops-engineer.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/agent-reports/dependency-manager.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/agent-reports/documentation-engineer.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/agent-reports/docker-expert.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/agent-reports/frontend-developer.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/agent-reports/accessibility-tester.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/agent-reports/project-manager.md`
