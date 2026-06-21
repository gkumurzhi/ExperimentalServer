# Risks and Blockers

| Risk | Affected stages | Mitigation |
|---|---|---|
| `close-plan-stage` and `close-plan-stages` expect a clean worktree, while `codex-analysis/20260621-150449/` is intentionally untracked | STAGE-001 through STAGE-006 | Keep the analysis directory out of commits and add a local-only ignore before running the stage runner |
| The easiest-looking fix for broken generated artifacts is to loosen the global UI CSP, which would widen the browser surface | STAGE-001, STAGE-002, STAGE-004 | Treat the existing UI CSP as a protected baseline and verify disabled profiles plus browser smoke after each change |
| The browser smoke suite has dense focus and label assertions around dialogs and file actions | STAGE-004 | Update smoke intentionally, preserve focus trap/return-focus/live-region behavior, and add targeted manual keyboard review |
| Plugin method-name reservation touches both runtime behavior and user-facing docs | STAGE-005 | Keep the change bounded to built-in method names and explicit override intent; add regression coverage before doc edits |
| `--print-config` output is consumed as a normalized settings view today | STAGE-006 | Prefer doc/test clarification first; if a new derived field is needed, keep it additive and add regression coverage |
