# Planning Decisions

| Decision | Rationale | Alternatives rejected |
|---|---|---|
| Create a new timestamped plan and update `ACTIVE_PLAN.md` to `implementation-plan/20260615-011753`. | User requested a new implementation plan from the 2026-06-15 analysis report; the prior active plan is reported closed and its directory is preserved. | Editing the closed `20260525-133607` plan in place. |
| Treat all staged work as MEDIUM priority. | The source report explicitly found no CRITICAL or HIGH issues; the important findings are medium operational/product/API/performance risks. | Inflating P0 roadmap items into HIGH severity. |
| Put docs mirror/release hygiene first. | `sync_docs.py --check` is the only confirmed current blocker and affects CI/doc consistency. | Starting with the default-profile migration before the docs blocker is cleared. |
| Make profile/default decision a separate stage before code migration. | The analysis identifies `workspace` as the recommended new-user direction but flags compatibility and Docker/security implications. | Flipping `DEFAULT_PROFILE` immediately without a recorded compatibility and exposure policy. |
| Require a capability policy boundary before default migration. | Capability behavior currently spans server, CORS, handlers, UI, docs, and tests; centralization reduces regression risk. | Adding more profile-specific conditionals across existing surfaces. |
| Defer durable Notepad recovery, public API implementation, trusted-proxy support, and registry publishing to backlog. | Each item needs product/support/security commitment beyond the current safe-workspace train. | Bundling strategic tracks into the default-profile migration. |
| No fresh Context7 documentation verification was performed during plan generation. | The stage plan is based on repository analysis artifacts; implementation-time docs checks should be performed if a stage depends on current external behavior. | Claiming external docs were checked by this planning run. |
