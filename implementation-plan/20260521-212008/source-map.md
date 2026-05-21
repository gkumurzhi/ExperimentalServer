# Source Map

| Source | Type | Notes |
|---|---|---|
| `stash@{0}^3:codex-analysis/20260521-144908/project-analysis-report.md` | deep project analysis report | Primary source. The report itself is still in the preserved stash rather than the working tree. |
| `implementation-plan/20260505-205639/stage-status.md` | completed prior implementation plan | Used to filter out STAGE-010 through STAGE-013 findings that are now closed. |
| `git log --oneline -n 8` | repository state | Confirmed `main` and `origin/main` include `c68474f Close STAGE-013`. |
| Current read-only inspection | source snapshot | Checked import boundaries, dependencies, request receive/admission paths, metrics, docs, and tests to scope stages. |
