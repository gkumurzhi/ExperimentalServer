# Implementation Plan
_Generated: 2026-05-25 13:36:07 MSK_

## Source analysis

- `codex-analysis/20260525-121051/project-analysis-report.md`
- `codex-analysis/20260525-121051/agent-reports/security-auditor.md`
- `codex-analysis/20260525-121051/agent-reports/architect-reviewer.md`
- `codex-analysis/20260525-121051/agent-reports/performance-engineer.md`
- `codex-analysis/20260525-121051/agent-reports/qa-expert.md`
- `codex-analysis/20260525-121051/agent-reports/docker-expert.md`
- `codex-analysis/20260525-121051/agent-reports/devops-engineer.md`
- `codex-analysis/20260525-121051/agent-reports/python-pro.md`
- `codex-analysis/20260525-121051/agent-reports/reviewer.md`

## Strategy

The plan follows the audit priority order: resource and storage safety first, then auth secret handling, feature profiles, CORS trust policy, Docker operations, and release/package hardening. The first four stages reduce disk, memory, and worker exhaustion risks before any broader deployment work. Later stages convert unsafe defaults and release paths into explicit, testable contracts.

No source code changes are part of this planning run. Existing implementation plans are preserved; `ACTIVE_PLAN.md` points to this new run.

## Stage overview

| Stage | Priority | Status | Title | Depends on | Main verification | Expected files |
|---|---|---|---|---|---|---|
| STAGE-001 | HIGH | OPEN | Upload storage policy and atomic commits | None | `python -m pytest tests/test_handlers/test_files.py tests/test_server_methods.py` | `src/server.py`, `src/http/utils.py`, `src/handlers/files.py`, `src/handlers/advanced_upload.py`, `tests/` |
| STAGE-002 | HIGH | OPEN | Notes and SMUGGLE storage policy | STAGE-001 | `python -m pytest tests/test_handlers/test_notepad.py tests/test_websocket_handlers.py tests/test_server_methods.py` | `src/notepad_service.py`, `src/handlers/notepad.py`, `src/handlers/smuggle.py`, `tests/` |
| STAGE-003 | HIGH | OPEN | In-flight body memory budget | STAGE-001 | `python -m pytest tests/test_http/test_io.py tests/test_request_pipeline.py tests/test_server_live.py` | `src/http/io.py`, `src/http/request.py`, `src/request_pipeline.py`, `src/server.py`, `src/cli.py` |
| STAGE-004 | HIGH | OPEN | Slow body and transfer deadlines | STAGE-003 | `python -m pytest tests/test_http/test_io.py tests/test_server_live.py tests/test_metrics.py` | `src/http/io.py`, `src/server.py`, `src/metrics.py`, `src/cli.py` |
| STAGE-005 | HIGH | OPEN | Auth secret files and auth invariants | None | `python -m pytest tests/test_cli.py tests/test_security/test_auth.py tests/test_request_pipeline.py` | `src/cli.py`, `src/server.py`, `src/security/auth.py`, `README.md`, `SECURITY.md`, `examples/docker/docker-compose.yml` |
| STAGE-006 | HIGH | OPEN | Feature profiles and capability gates | STAGE-001, STAGE-005 | `python -m pytest tests/test_handler_registry.py tests/test_server_methods.py tests/test_server_live.py` | `src/server.py`, `src/cli.py`, `src/handlers/__init__.py`, `src/http/cors.py`, `src/data/static/ui/*` |
| STAGE-007 | MEDIUM | OPEN | Wildcard CORS read-only policy | STAGE-006 | `python -m pytest tests/test_server_methods.py tests/test_security/test_websocket_upgrade.py` | `src/http/cors.py`, `src/server.py`, `src/request_pipeline.py`, `API.md`, `tests/` |
| STAGE-008 | MEDIUM | OPEN | Docker and operational readiness | STAGE-005, STAGE-006 | `docker compose -f examples/docker/docker-compose.yml config` | `Dockerfile`, `examples/docker/docker-compose.yml`, `.github/workflows/ci.yml`, `README.md`, `SECURITY.md` |
| STAGE-009 | MEDIUM | OPEN | Release artifacts and provenance lane | STAGE-008 | `python -m build --sdist --wheel --outdir /tmp/exphttp-dist` | `.github/workflows/`, `tools/`, `pyproject.toml`, `README.md` |
| STAGE-010 | MEDIUM | OPEN | Public package identity migration | STAGE-009 | `python -m pytest tests/test_import_boundaries.py tests/test_cli.py` | `pyproject.toml`, `src/`, `tests/`, `tools/`, docs |
| STAGE-011 | MEDIUM | OPEN | WebSocket operations and failure semantics | STAGE-006 | `python -m pytest tests/test_websocket.py tests/test_websocket_handlers.py tests/test_server_live.py` | `src/server.py`, `src/websocket.py`, `src/cli.py`, `tests/` |

## How to close a stage

Use:

```text
$close-plan-stage STAGE-001
$close-plan-stage next
$close-plan-stage STAGE-003 --no-subagents
```

## Definition of closed

A stage is CLOSED only when all acceptance criteria are met, verification is completed, and `stage-status.md` plus a stage report are updated.

