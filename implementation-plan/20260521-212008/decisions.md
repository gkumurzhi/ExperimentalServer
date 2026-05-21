# Planning Decisions

| Decision | Rationale | Alternatives rejected |
|---|---|---|
| Do not apply `stash@{0}` code changes. | They contain an obsolete partial Notepad `clientNoteId` / `operationId` implementation and an old corrupted UI artifact, while current `main` has closed STAGE-010 through STAGE-013. | Applying the stash or cherry-picking code from it would risk regressing closed stages. |
| Use the stashed audit report as a source without restoring it into the worktree. | It preserves evidence while keeping the repo clean and avoiding stale artifacts in the active tree. | Restoring `codex-analysis/` would dirty the repo with partially stale analysis artifacts. |
| Create a fresh active plan instead of extending `20260505-205639`. | The old plan is now fully CLOSED; a new plan makes remaining operation-readiness scope explicit. | Reopening old stages would blur completed history. |
| Split request controls into receive caps and worker admission. | They affect different code paths and have different regression tests. | A single large "resource controls" stage would be harder to verify safely. |
| Keep operator documentation last. | Docs should reflect implemented behavior, especially admission, Notepad limits, origin policy, and CSP behavior. | Updating public-run guidance first risks another stale-doc pass. |
