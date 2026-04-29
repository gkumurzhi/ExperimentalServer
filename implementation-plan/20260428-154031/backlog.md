# Backlog and Needs-Investigation Items

| Item | Source | Why not staged now | Suggested next step |
|---|---|---|---|
| Package resource serving as bytes/streams | architect-reviewer LOW | Requires design beyond path traversal fix; not needed before STAGE-001 containment. | After high-risk fixes, design a byte/stream package asset helper that avoids `as_file()` lifetime issues. |
| HandlerContext protocol | architect-reviewer deeper improvement | Architecture cleanup, not required to close immediate security/reliability risks. | Consider after parser/metrics stages to make implicit server attributes explicit. |
| Full streaming uploads to disk | performance-engineer deeper improvement | Larger refactor than early Content-Length/cap stage. | Plan a separate stage after STAGE-019 if upload scale remains a target. |
| WebSocket save idempotency and normalized WS error schema | websocket-engineer MEDIUM/LOW | Needs product decision on client request IDs and client-visible protocol compatibility. | Design WS operation IDs and error schema after protocol validation stages. |
| Full benchmark suite | performance-engineer LOW | Useful but not needed before memory-risk fixes. | Add benchmarks after STAGE-002/STAGE-003/STAGE-019 establish desired behavior. |
| GitHub Actions SHA pinning | devops-engineer LOW | Supply-chain hardening polish after functional CI issues. | Add full-length SHA pinning once workflow commands are stable. |
| Coverage artifact retention guardrails | devops-engineer LOW | Small process hardening but not higher than audit command/dependency drift. | Add `if-no-files-found: error` and retention when touching CI workflow. |
| Compose production hardening beyond example defaults | docker-expert LOW | Requires decision whether Docker example is local-only or production-ready. | Extend STAGE-022 or create follow-up based on deployment intent. |
| MkDocs edit-link customization | documentation-engineer LOW | Contributor polish, not blocking correctness. | Adjust edit links after docs drift stages if generated pages still confuse contributors. |
| Advanced-upload response should include saved filename/path | documentation-engineer open question | API behavior change requiring compatibility decision. | Decide API change; if accepted, create a focused handler/docs/test stage. |
| Normalize API error response bodies | STAGE-010 follow-up | STAGE-010 documents existing mixed behavior only; changing handler responses may break clients relying on legacy `text/plain`, empty-body, or endpoint-specific JSON errors. | Decide whether to migrate toward a uniform JSON error envelope and, if accepted, stage handler changes with compatibility tests. |
