# Risks and Blockers

| Risk | Affected stages | Mitigation |
|---|---|---|
| Working tree was dirty before planning, including source, docs, tests, Docker, and constraints files | All implementation stages | `close-plan-stage` must inspect existing diffs before editing and avoid reverting unrelated user changes |
| Existing `implementation-plan/ACTIVE_PLAN.md` pointed to an older plan in a non-template format | Plan discovery | This run updated `ACTIVE_PLAN.md` to the parseable required format and preserved the older plan directory |
| No live ACME issuance, browser smoke, full pytest, benchmark/load test, or Docker image run was executed by the source analysis parent phase | STAGE-003, STAGE-005, STAGE-008, STAGE-010, STAGE-012 | Keep live ACME as manual/optional; require targeted local tests and Docker/browser checks where available |
| Secure Notepad durability is an open product decision | STAGE-002, STAGE-009, STAGE-010 | Implement and document the current session-key-bound contract first; defer durable key design unless the owner chooses it |
| `--port 0` behavior is undecided | STAGE-004 | Stage owner must choose and document either rejection or actual bound-port reporting before implementing tests |
| Broken ACME cache recovery policy is undecided: auto-renew vs fail early | STAGE-003, STAGE-005 | Prefer pair validation plus clear behavior; avoid unbounded renewal/rate-limit risk without explicit owner decision |
| Historical docs/changelog may contain intentionally stale terms | STAGE-001, STAGE-006 | Use narrow deny patterns and explicit allowlists rather than broad repo-wide grep |
| Docker may be unavailable in a local closing run | STAGE-005, STAGE-008 | Provide CI-ready commands and run Docker checks when available; otherwise record unverified Docker checks in stage closure |
| Context7/current documentation was not newly queried during this planning pass | All stages involving third-party APIs | Rely on the source analysis documentation checks already recorded; if implementation changes third-party API usage, verify docs then |
| Local Python environment may be stale relative to declared dependencies | Verification stages | Use constrained clean env or existing `.venv` before treating import failures as code failures |
