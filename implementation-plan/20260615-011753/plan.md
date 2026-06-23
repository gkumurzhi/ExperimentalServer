# Implementation Plan
_Generated: 2026-06-15 01:17:53 MSK_

## Source analysis

- `codex-analysis/20260614-225437/project-analysis-report.md`
- `codex-analysis/20260614-225437/agent-reports/product-manager.md`
- `codex-analysis/20260614-225437/agent-reports/architect-reviewer.md`
- `codex-analysis/20260614-225437/agent-reports/security-auditor.md`
- `codex-analysis/20260614-225437/agent-reports/api-designer.md`
- `codex-analysis/20260614-225437/agent-reports/qa-expert.md`
- `codex-analysis/20260614-225437/agent-reports/websocket-engineer.md`
- `codex-analysis/20260614-225437/agent-reports/performance-engineer.md`
- `codex-analysis/20260614-225437/agent-reports/devops-engineer.md`
- `codex-analysis/20260614-225437/agent-reports/dependency-manager.md`
- `codex-analysis/20260614-225437/agent-reports/documentation-engineer.md`
- `codex-analysis/20260614-225437/agent-reports/docker-expert.md`
- `codex-analysis/20260614-225437/agent-reports/frontend-developer.md`
- `codex-analysis/20260614-225437/agent-reports/accessibility-tester.md`
- `codex-analysis/20260614-225437/agent-reports/project-manager.md`

## Strategy

The analysis found no CRITICAL or HIGH severity issues, so the plan treats all closable work as MEDIUM priority and orders it by dependency and blast radius. The first stage removes the present docs/CI blocker. The next stages make the safe-by-default direction explicit, consolidate profile/capability policy, and only then allow default-profile migration and profile-aware UI/QA work.

Distribution, API platform, durable Notepad, and trusted-proxy support are intentionally not bundled into the default migration path. They remain separate bounded stages or backlog items so a future `$close-plan-stage` run can finish one area without re-planning the whole repository.

## Stage overview

| Stage | Priority | Status | Title | Depends on | Main verification | Expected files |
|---|---|---|---|---|---|---|
| STAGE-001 | MEDIUM | CLOSED | Docs mirror and release hygiene | None | `python tools/sync_docs.py --check` | `API.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `docs/`, `.pre-commit-config.yaml` |
| STAGE-002 | MEDIUM | CLOSED | Profile and exposure decision gate | STAGE-001 | `python tools/check_stale_docs.py` | `docs/ADR/`, `README.md`, `SECURITY.md`, `docs/threat-model.md` |
| STAGE-003 | MEDIUM | CLOSED | Capability policy boundary | STAGE-002 | `python -m pytest tests/test_handler_registry.py tests/test_server_methods.py tests/test_security/test_websocket_upgrade.py` | `src/features.py`, `src/server.py`, `src/http/cors.py`, `src/handlers/`, `tests/` |
| STAGE-004 | MEDIUM | CLOSED | Safe default workspace migration | STAGE-002, STAGE-003 | `python -m pytest tests/test_cli.py tests/test_server_methods.py tests/test_server_live.py` | `src/features.py`, `src/cli.py`, `README.md`, `API.md`, `tests/` |
| STAGE-005 | MEDIUM | CLOSED | Notepad UI and accessibility hardening | STAGE-003 | `python tools/check_static_ui_assets.py --repo-root .` | `src/data/index.html`, `src/data/static/ui/notepad.js`, `src/data/static/ui/core.js`, `tools/browser_smoke.playwright.js` |
| STAGE-006 | MEDIUM | CLOSED | Profile-aware smoke and risk test gates | STAGE-004, STAGE-005 | `python tools/browser_smoke.py --help` plus targeted pytest lanes | `tools/browser_smoke.py`, `tools/browser_smoke.playwright.js`, `.github/workflows/ci.yml`, `pyproject.toml` |
| STAGE-007 | MEDIUM | CLOSED | Python 3.14 readiness | STAGE-001 | Python 3.14 CI matrix and package smoke | `pyproject.toml`, `.github/workflows/ci.yml`, `README.md`, `CONTRIBUTING.md` |
| STAGE-008 | MEDIUM | CLOSED | Docker and rollback boundary | STAGE-002 | `docker compose -f examples/docker/docker-compose.yml config` | `Dockerfile`, `examples/docker/docker-compose.yml`, `.github/workflows/release.yml`, `README.md`, `CONTRIBUTING.md` |
| STAGE-009 | MEDIUM | CLOSED | Workspace performance baseline | STAGE-003 | `python -m pytest tests/benchmarks --benchmark-only` | `src/storage.py`, `src/handlers/info.py`, `src/notepad_service.py`, `tests/benchmarks/`, `tests/` |
| STAGE-010 | MEDIUM | CLOSED | API contract stability | STAGE-002 | `python tools/sync_docs.py --check` | `API.md`, `docs/api.md`, `README.md`, `tests/` |
| STAGE-011 | MEDIUM | CLOSED | WebSocket and Notepad safety | STAGE-003, STAGE-010 | `python -m pytest tests/test_websocket.py tests/test_websocket_handlers.py tests/test_security/test_websocket_upgrade.py` | `src/handlers/notepad.py`, `src/server.py`, `src/websocket.py`, `API.md`, `tests/` |

## How to close a stage

Use:

```text
$close-plan-stage STAGE-001
$close-plan-stage next
$close-plan-stage STAGE-003 --no-subagents
```

## Definition of closed

A stage is CLOSED only when all acceptance criteria are met, verification is completed, and `stage-status.md` plus a stage report are updated.
