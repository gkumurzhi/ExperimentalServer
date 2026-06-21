# Backlog and Needs-Investigation Items

| Item | Source | Why not staged now | Suggested next step |
|---|---|---|---|
| Add ADR-006 to `mkdocs.yml` navigation | `project-analysis-report.md`, `documentation-engineer.md` | Useful discoverability work, but it does not block the runtime, guardrail, or policy fixes above | Revisit after STAGE-003 if docs navigation still hides the profile decision |
| Re-group request methods or switch summary view to the default first-screen mode | `frontend-developer.md` | The current high-signal UI risk is the artifact flow; broader request-panel reshaping is larger and more subjective | Reassess after STAGE-004 with updated smoke and manual UX review |
| Add a derived `effective_tls` field to `--print-config` | `cli-developer.md` | This is an output-schema change that could affect automation consumers | Decide after STAGE-006 if documentation-only clarification is insufficient |
| Extract smuggling templates into package resources | `architect-reviewer.md` | Safe only after direct renderer tests exist and the runtime contract is pinned | Re-evaluate after STAGE-002 |
| Run a screen-reader pass for the updated artifact flow | `accessibility-tester.md` | Static analysis and smoke can cover keyboard/focus first; assistive-tech validation is a follow-up hardening step | Run after STAGE-004 lands |
