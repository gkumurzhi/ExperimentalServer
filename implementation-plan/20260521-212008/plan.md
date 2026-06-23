# Implementation Plan
_Generated: 2026-05-21 21:20:08 MSK_

## Source analysis

- `stash@{0}^3:codex-analysis/20260521-144908/project-analysis-report.md`
- `implementation-plan/20260505-205639/stage-status.md`
- Current source snapshot: `main` at `c68474f`

## Strategy

The previous active plan closed the stop-the-line and feature-development blockers:
Notepad UI/WS idempotency, advanced-upload JSON guardrails, atomic user-data writes,
and local/CI pytest collection drift. This follow-up plan targets the remaining
operation-readiness risks in dependency boundaries, request admission, browser
mutation policy, observability, CI gates, and operator documentation.

## Stage overview

| Stage | Priority | Status | Title | Depends on | Main verification | Expected files |
|---|---|---|---|---|---|---|
| STAGE-001 | HIGH | CLOSED | Untangle package import and ACME dependency boundaries | None | Minimal import checks and dependency audit | `src/__init__.py`, `src/security/__init__.py`, `pyproject.toml`, tests |
| STAGE-002 | HIGH | CLOSED | Add receive-layer header caps and parser telemetry | STAGE-001 | HTTP parser limit tests | `src/http/io.py`, `src/server.py`, CLI/config/tests |
| STAGE-003 | HIGH | CLOSED | Add bounded request admission before worker submission | STAGE-002 | Saturation and keep-alive tests | `src/server.py`, `src/metrics.py`, tests |
| STAGE-004 | HIGH | CLOSED | Add Notepad payload size limits | STAGE-001 | HTTP and WS oversized note tests | `src/notepad_service.py`, `src/handlers/notepad.py`, docs/tests |
| STAGE-005 | HIGH | CLOSED | Add browser-origin guardrails for mutating HTTP requests | STAGE-001 | Origin/Sec-Fetch mutation tests | request pipeline, handlers, CLI/docs/tests |
| STAGE-006 | MEDIUM | CLOSED | Expand operational metrics and worker exception visibility | STAGE-003 | Metrics snapshot and worker failure tests | `src/metrics.py`, `src/server.py`, docs/tests |
| STAGE-007 | MEDIUM | CLOSED | Harden UI validation and CSP release gates | STAGE-005 | JS syntax, browser smoke, CSP tests | static UI, browser smoke, CI/tests |
| STAGE-008 | MEDIUM | CLOSED | Refresh operator docs and semantic contract guards | STAGE-002, STAGE-004, STAGE-005, STAGE-007 | stale-doc and semantic guard tests | README, SECURITY, API/docs, tools/tests |

## How to close a stage

Use:

```text
$close-plan-stage STAGE-001
$close-plan-stage next
```

## Definition of closed

A stage is CLOSED only when all acceptance criteria are met, verification is
completed, and `stage-status.md` plus a stage report are updated.
