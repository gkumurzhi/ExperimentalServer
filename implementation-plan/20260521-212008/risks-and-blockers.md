# Risks and Blockers

| Risk | Affected stages | Mitigation |
|---|---|---|
| The source audit report is preserved in `stash@{0}` instead of the working tree. | All | This plan cites the stash source and current prior-stage status. Do not drop the stash until the user decides whether to preserve old audit artifacts. |
| Origin/CSRF defaults can break non-browser or scripted clients if too strict. | STAGE-005, STAGE-008 | Add explicit compatibility mode, document defaults, and cover API clients in tests. |
| Admission control can introduce false 503s or deadlock if sockets are not released. | STAGE-003, STAGE-006 | Use bounded semaphores/queues with finally-release tests and socket stress cases. |
| CSP tightening can break existing inline UI behavior. | STAGE-007 | Start with validation and smoke capture, then tighten only with tests proving UI behavior. |
| Docs must not claim operation beyond the implemented controls. | STAGE-008 | Tie docs updates to accepted behavior from STAGE-002 through STAGE-007. |
