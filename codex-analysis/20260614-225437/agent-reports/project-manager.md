# project-manager Report
_Generated: 2026-06-15 00:55:01 Europe/Moscow_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/analysis-plan.md_

## Summary
Read-only synthesis complete; no files modified. The next dominant path should be safe-by-default `workspace` / file-workspace hardening, with `lab` preserved as explicit opt-in. This is supported by the product recommendation to make `workspace` the new-user default and keep `lab` for compatibility ([product-manager.md](/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/agent-reports/product-manager.md:6)).

The critical path is: fix docs drift, decide profile/default policy, centralize capability policy, then harden UI/QA/Docker/docs around that decision. API v1, public distribution, and durable Notepad should stay optional strategic tracks until the default-profile and support-boundary decisions are explicit.

## Proposed Roadmap
Immediate fixes:
- Repair docs mirror drift and changelog/release boundary. Docs drift is confirmed across reports and blocks docs CI ([documentation-engineer.md](/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/agent-reports/documentation-engineer.md:8)).
- Add pre-commit/PR guardrails for docs sync and stale-doc checks.
- Add explicit Docker/profile/security wording so examples do not rely on implicit `lab`.

Short-term stages:
- Decide `workspace` default vs continued `lab` default.
- Centralize capability/profile policy before changing defaults; policy is currently scattered across server, CORS, handlers, and UI ([architect-reviewer.md](/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/agent-reports/architect-reviewer.md:37)).
- Add profile-aware browser smoke, Notepad UI warning/capability fixes, and accessibility gates.
- Add risk-specific QA lanes for auth, parser, CORS/profile, storage, WebSocket/Notepad ([qa-expert.md](/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/agent-reports/qa-expert.md:47)).
- Add Python 3.14 readiness as a separate stage before metadata widening ([dependency-manager.md](/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/agent-reports/dependency-manager.md:49)).

Medium-term options:
- File-workspace reliability: benchmarks, bounded listing strategy, quota-scan mitigation, richer local metrics.
- API platform: declare legacy v0, then design opt-in v1 before SDK/client work ([api-designer.md](/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/agent-reports/api-designer.md:35)).
- Distribution/ops: durable GitHub Release assets first; PyPI/GHCR only after SLA, rollback, support, and publishing controls are owned ([devops-engineer.md](/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/agent-reports/devops-engineer.md:47)).
- Secure Notepad: ADR first; do not persist the current session model as recovery ([security-auditor.md](/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/agent-reports/security-auditor.md:52)).

Long-term decisions:
- Is the project lab-first, safe workspace, public API platform, or packaged ops product?
- Is Notepad ephemeral scratchpad or durable encrypted workspace?
- Is reverse-proxy deployment unsupported, proxy-owned, or app-supported with trusted proxy identity?
- Is Docker a local/operator example or a supported registry artifact?

## Stage Candidates
| Stage | Phase | Owner | Objective |
|---|---|---|---|
| STAGE-001 Docs And Release Hygiene | Immediate | Docs/maintainer | Sync `docs/api.md` and `docs/contributing.md`, add dated changelog boundary, clarify artifact-only release/docs. |
| STAGE-002 Profile Decision Gate | Immediate | Maintainer/product/security | Record `workspace` default vs continued `lab`, compatibility window, migration notes, Docker/default posture. |
| STAGE-003 Capability Policy Boundary | Short | Backend/architecture | Centralize profile-derived policy for methods, CORS exposure, browser mutation, WS route enablement, destructive gates. |
| STAGE-004 Safe Default Migration | Short | Backend/QA/docs | If approved, make new-user default `workspace`; keep `--profile lab` fully compatible. |
| STAGE-005 UI And A11y Capability Hardening | Short | Frontend/a11y | Fix Notepad delete/clear capability checks, visible ephemeral warning, labels, quota/error announcements. |
| STAGE-006 Risk-Specific Test Gates | Short | QA | Add named CI lanes and/or coverage baselines for parser/auth/CORS/profile/storage/WS/Notepad. |
| STAGE-007 Python 3.14 Readiness | Short | Dependency/devops | Add 3.14 CI first, then metadata/docs/classifier update if clean. |
| STAGE-008 Docker And Rollback Boundary | Short | DevOps/Docker | Explicit safe profiles in examples, retention/GitHub Release decision, timeout/grace alignment. |
| STAGE-009 Workspace Performance Baseline | Medium | Performance/backend | Bench uploads, quota scans, large `INFO`, Notepad list/save, WS slots; fix no-limit quota scan. |
| STAGE-010 API Contract Stability | Medium option | API/backend/docs | Document v0 contract, add additive discovery/error codes, design v1 only if API path is chosen. |
| STAGE-011 WebSocket/Notepad Safety | Medium option | WS/security/frontend | Message-level delete/clear checks, opId semantics docs/tests, send-failure handling, binary-frame decision. |
| STAGE-012 Strategic Product ADRs | Long | Maintainer/product/security | Decide durable Notepad, public publishing, API clients, trusted proxy model. |

## Dependencies and Sequencing
Critical path:
1. STAGE-001 first. Current docs drift is a present CI/documentation blocker.
2. STAGE-002 before any default change, public distribution, or API v1.
3. STAGE-003 before STAGE-004 to reduce multi-surface regression risk.
4. STAGE-004, STAGE-005, STAGE-006 should land as one coordinated release train if `workspace` becomes default.
5. STAGE-007 can run in parallel after STAGE-001, but must not combine with dependency refresh.
6. STAGE-008 depends on STAGE-002 if examples change default profile.
7. STAGE-010, STAGE-011 durable work, and publishing lanes depend on strategic ADRs.

Alternative paths:
- If maintainer keeps `lab` default: skip STAGE-004 default flip, but still do startup warnings, explicit safe Docker examples, profile docs, and profile smoke.
- If distribution is prioritized: STAGE-008 becomes critical path, but still requires profile-default decision and durable rollback assets.
- If API is prioritized: STAGE-010 must precede SDK/client work; keep legacy v0 behavior for `lab`.
- If Notepad is prioritized: STAGE-011 safety comes before durable recovery ADR and crypto design.

## Acceptance Criteria
- STAGE-001: `sync_docs --check` and stale-doc checks pass; changelog has a dated boundary; install/publish docs no longer conflict.
- STAGE-002: ADR or decision doc states default profile, compatibility plan, migration warning, Docker stance, and owner approval.
- STAGE-003: one profile change is tested through `PING`, registry, CORS preflight, browser mutation guard, and UI capability mapping.
- STAGE-004: default reports `workspace`; ordinary file upload/browse/delete works; lab-only capabilities are false by default; `--profile lab` preserves old behavior.
- STAGE-005: Notepad warning is visible and accessible; delete/clear obey `note_delete`/`note_clear`; quota/server errors surface useful text; profile-disabled UI is smoke-tested.
- STAGE-006: named risk lanes exist in CI; baseline coverage or no-regression thresholds are recorded for critical modules.
- STAGE-007: Python 3.14 constrained CI, `pip check`, import smoke, security audit, and package smoke pass before metadata changes.
- STAGE-008: Docker examples pass explicit safe profile or documented `lab`; rollback artifact policy is durable enough for the docs.
- STAGE-009: benchmarks exist with recorded baselines; no-limit upload path avoids unnecessary usage scan.
- STAGE-010: API docs declare v0 stability, retry semantics, note ID behavior, and v1 scope if chosen.
- STAGE-011: WS destructive actions re-check capabilities; opId/retry limits are documented/tested; send failure is observable.

## Risks and Open Decisions
- Default-profile decision is the main schedule gate; delaying it amplifies docs, UI, Docker, and API churn.
- Changing default may break scripts relying on implicit `lab`; mitigation is explicit `--profile lab`, migration docs, and release notes.
- Docker `docker run -p` can expose `lab` behavior if defaults are unchanged ([docker-expert.md](/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/agent-reports/docker-expert.md:31)).
- Notepad durability is high-risk crypto/product work; current sessions are intentionally not recovery tokens.
- API clients are premature until v0/v1 boundary and error semantics are stable.
- Performance confidence is limited because upload/listing/Notepad hot paths lack benchmarks ([performance-engineer.md](/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/agent-reports/performance-engineer.md:8)).

## Quick Wins
- Run docs mirror regeneration in an implementation pass.
- Add docs sync/stale-doc pre-commit hooks.
- Add profile decision table: `serve`, `workspace`, `lab`.
- Add `SECURITY.md` client-IP/proxy section.
- Make Docker examples pass explicit `--profile workspace` or `serve`.
- Add visible Notepad ephemeral warning and textarea label.
- Add WS delete/clear capability regression tests.
- Add Python support table with 3.14 pending and 3.10 EOL timing.

## Deeper Improvements
- Declarative capability/action manifest shared by server, UI, docs, and tests.
- API v1 with normalized errors, idempotency, pagination, and contract tests.
- Durable Notepad with envelope-encryption ADR, test vectors, recovery model, and migration plan.
- Streaming uploads or cached quota accounting if workspace scale grows.
- Cursor-style large directory listing if exact `INFO.total_items` becomes expensive.
- GHCR/PyPI publishing only with promotion gates, SBOM/provenance, scan gates, rollback, and maintainer SLA.
