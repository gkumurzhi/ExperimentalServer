# Implementation Plan
_Generated: 2026-06-23 04:32:02 MSK_

## Source analysis
- `codex-analysis/20260621-150449/project-analysis-report.md`
- `implementation-plan/20260621-173043/findings.md`
- `implementation-plan/20260621-173043/backlog.md`
- `implementation-plan/20260615-011753/findings.md`
- `implementation-plan/20260615-011753/backlog.md`
- `implementation-plan/20260615-011753/risks-and-blockers.md`

## Strategy
The repository no longer has open implementation stages in historical `stage-status.md` files, but it does have a real remaining backlog: supported distribution surface, trusted-proxy stance, durable Notepad recovery, and API/public-client strategy. These are not good candidates for opportunistic code edits. This run turns them into bounded decision/ADR stages so later implementation work starts from explicit product and security boundaries instead of recurring backlog prose.

## Stage overview
| Stage | Priority | Status | Title | Depends on | Main verification | Expected files |
|---|---|---|---|---|---|---|
| STAGE-001 | MEDIUM | OPEN | Supported surface and publishing boundary | `None` | `python tools/check_stale_docs.py` | `docs/ADR/`, `README.md`, `SECURITY.md`, `CONTRIBUTING.md`, `.github/workflows/release.yml` |
| STAGE-002 | MEDIUM | OPEN | Trusted proxy and client identity boundary | `STAGE-001` | `python tools/check_stale_docs.py` | `docs/ADR/`, `SECURITY.md`, `README.md`, `docs/threat-model.md`, `API.md` |
| STAGE-003 | MEDIUM | OPEN | Durable Notepad recovery ADR | `STAGE-001` | `python tools/check_stale_docs.py` | `docs/ADR/`, `SECURITY.md`, `docs/threat-model.md`, `API.md`, `README.md` |
| STAGE-004 | MEDIUM | OPEN | API v1 and client strategy boundary | `STAGE-001`, `STAGE-002` | `python tools/sync_docs.py --check` | `docs/ADR/`, `API.md`, `docs/api.md`, `README.md`, `SECURITY.md` |

## How to close a stage
Use:

```text
$close-plan-stage STAGE-001
$close-plan-stage next
$close-plan-stage STAGE-003 --no-subagents
```

## Definition of closed
A stage is CLOSED only when all acceptance criteria are met, verification is completed, and `stage-status.md` plus a stage report are updated.
