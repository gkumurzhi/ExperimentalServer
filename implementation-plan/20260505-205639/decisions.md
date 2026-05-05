# Planning Decisions

| Decision | Rationale | Alternatives rejected |
|---|---|---|
| Create a fresh timestamped plan and update `implementation-plan/ACTIVE_PLAN.md` | User requested a new plan from a specific analysis report; preserving old plan directory avoids destructive changes | Reusing `implementation-plan/20260428-154031`; overwriting old plan files |
| Put release-smoke repair first | Current smoke exits before browser/Docker validation, so later changes need this signal restored | Starting with broader refactors while release smoke remains blocked |
| Treat reviewer merge blockers as HIGH stage priority even when some source agents labeled them MEDIUM | `reviewer.md` marked ACME cache and CLI TLS validation as blockers for the dirty TLS/ACME change | Deferring ACME/CLI fixes behind docs/tooling stages |
| Document current Secure Notepad session-key limitations instead of implementing durable recovery in STAGE-002 | Durability is an open product decision; the analysis gives enough evidence to fix interoperability and prevent overpromising | Designing persistent/recoverable client keys without owner decision |
| Split ACME cache validation from container ACME docs | Cache-pair correctness should be fixed before recommending persistent ACME volumes broadly | Combining code recovery and Docker/operator docs into one large stage |
| Keep live ACME staging in backlog | It requires external DNS/public port ownership and cannot be a default close-plan verification step | Making live CA issuance a required stage acceptance check |
| Merge upload exclusive writes and Notepad atomic writes into one user-data persistence stage | Both address same filesystem persistence root cause and may benefit from one shared helper | Splitting into two tiny stages with duplicated helper design |
| Defer global backpressure/metrics and streaming upload redesign | These are broader reliability/architecture changes and not needed to close immediate HIGH blockers | Including large behavioral redesign in the first implementation batch |
