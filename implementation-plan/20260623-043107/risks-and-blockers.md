# Risks and Blockers

| Risk | Affected stages | Mitigation |
|---|---|---|
| Maintainers may prefer to keep the project intentionally local-only, which would collapse some future publishing/API tracks. | STAGE-001, STAGE-004 | Treat explicit non-support as a valid successful outcome; the stage goal is a written boundary, not forced expansion. |
| Trusted-proxy and API-client expectations can sprawl into implementation details if the ADRs are not kept bounded. | STAGE-002, STAGE-004 | Keep these stages decision/documentation-only and defer code work to later dedicated plans. |
| Durable Notepad recovery can invite unsafe “just persist the current key” shortcuts. | STAGE-003 | Require an explicit cryptographic model, metadata/privacy constraints, and recovery UX before any implementation plan is allowed. |
| Docs-only stages can drift unless guardrails are updated where wording is safety-critical. | STAGE-001 through STAGE-004 | Include `check_stale_docs.py` and mirrored-doc verification where relevant so the recorded boundaries stay enforceable. |
| This planning run did not perform fresh external documentation lookups for packaging, publishing, or proxy behavior. | STAGE-001 through STAGE-004 | Require implementation-time official-doc verification if a future code stage depends on current external platform behavior. |
