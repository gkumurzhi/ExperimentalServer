# Backlog and Needs-Investigation Items

| Item | Source | Why not staged now | Suggested next step |
|---|---|---|---|
| Decide durable Secure Notepad key strategy across reload/restart | `project-analysis-report.md`; `websocket-engineer.md`; `api-documenter.md` | Requires product/security decision beyond a bounded implementation stage; STAGE-002 documents current limits | Choose session-only vs durable recoverable keys, then create a follow-up design stage |
| Encrypt note titles | `security-auditor.md`; `frontend-developer.md` | Open product decision; STAGE-009 makes plaintext metadata explicit | Decide whether titles are metadata or encrypted content |
| Live ACME staging workflow | `security-auditor.md`; `devops-engineer.md`; `docker-expert.md` | Needs controlled domain, public port 80, and secrets/routing ownership | Add manual `workflow_dispatch` checklist once infrastructure owner exists |
| Configurable ACME cache directory | `docker-expert.md`; `reviewer.md` | Useful after STAGE-003/STAGE-005, but broader config surface | Design `--acme-dir` or `EXPHTTP_ACME_DIR` with migration docs |
| Global connection admission/backpressure and resource metrics | `performance-engineer.md`; `project-analysis-report.md` | Larger behavioral change; not a first-pass merge blocker | Create a separate reliability plan covering worker queueing, WS budget, latency/drop metrics |
| Stream standard uploads from socket to disk | `performance-engineer.md` | Touches request pipeline contract more deeply than current atomic-write stage | Prototype streaming request body API and migration tests |
| Tighten CSP and remove inline scripts/styles | `security-auditor.md`; `frontend-developer.md` | Requires frontend/smuggle markup refactor; no confirmed XSS found | First add hostile-string smoke cases, then reduce inline script/style allowances |
| Systematic hostile UI string smoke matrix | `frontend-developer.md`; `qa-expert.md` | Useful P2 coverage, but lower priority than current Notepad state and CI blockers | Add smoke cases for filenames, note titles, paths, inspector summaries, and HTML metacharacters |
| Lighten package root import boundary | `python-pro.md`; `project-analysis-report.md` | Maintainability improvement after dependency/tooling drift is fixed | Defer eager TLS/ACME imports from `src.__init__` and add import smoke |
| Runtime ACME health command | `security-auditor.md`; `project-analysis-report.md` | Operational feature, not needed to close current cache reuse bug | Design `exphttp acme-check` or similar command after STAGE-003 |
| Generate README/API tables from tests or one source of truth | `api-documenter.md`; `project-analysis-report.md` | Documentation maintainability improvement | Add docs-generation stage after current docs drift is closed |
