# Backlog and Needs-Investigation Items

| Item | Source | Why not staged now | Suggested next step |
|---|---|---|---|
| Full external-exposure hardening certification | Audit operation-readiness findings | Requires policy decisions, deployment target, reverse proxy choice, and threat model beyond repo-local changes. | After STAGE-008, run a deployment-specific threat model. |
| Docker image vulnerability scanning | Audit release-gate findings | Useful, but lower priority than request admission, origin policy, and dependency boundaries. | Add to a later supply-chain plan once core runtime gates are stable. |
| Removing the compatibility-only `crypto` extra | Audit dependency findings | Could be a breaking packaging change; this plan can clarify it but should not remove compatibility without release decision. | Decide in STAGE-001 whether to keep documented compatibility or plan a major-version cleanup. |
| ACME staging/live drill | Audit devops findings | Needs network/DNS/ACME environment decisions not available from repo alone. | Add a manual/scheduled validation stage after docs and dependency boundaries are stable. |
