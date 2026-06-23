# Planning Decisions

| Decision | Rationale | Alternatives rejected |
|---|---|---|
| Create a fresh timestamped plan and update `ACTIVE_PLAN.md` to `implementation-plan/20260623-043107`. | The prior active plan is fully CLOSED, while the remaining work is strategic backlog rather than incomplete implementation. | Reopening `implementation-plan/20260621-173043` and mixing closed SMUGGLE work with new decisions. |
| Treat this run as a decision-first roadmap instead of a code-first roadmap. | Remaining items are blocked by product/support/security boundaries, not by missing code mechanics. | Forcing fake implementation stages for trusted proxy, durable recovery, or API v1 without first recording the boundaries. |
| Put supported-surface and publishing policy first. | Distribution/support stance influences trusted proxy, durable recovery expectations, and whether a supported API/client contract is even meaningful. | Starting with durable Notepad or API v1 decisions before the project states what it supports publicly. |
| Keep request-panel density, frontend build pipeline, and speculative performance work in backlog. | Those items are lower-confidence or lower-urgency than the unresolved product/security boundaries. | Promoting UI polish or optimization work above support-surface, proxy, and recovery decisions. |
| Do not claim fresh external documentation verification in this planning run. | This run is based on existing repository analysis and preserved plan artifacts. | Pretending current Docker/PyPI/GitHub/OIDC behavior was re-validated during plan generation. |
