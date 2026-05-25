# Backlog and Needs-Investigation Items

| Item | Source | Why not staged now | Suggested next step |
|---|---|---|---|
| Trusted reverse-proxy client IP model for auth rate limiting | `security-auditor.md` F-018 | Requires deployment topology and trusted CIDR policy; wrong design can create spoofing risk | Decide whether app should honor proxy headers or document proxy-level rate limiting only |
| Notepad durable recovery and per-user authorization model | `security-auditor.md`, `qa-expert.md` F-019 | Product contract is unresolved: current docs describe ephemeral session-bound keys | Choose scratchpad vs durable secure notes before changing crypto/session UX |
| Module-specific coverage gates | `devops-engineer.md`, `qa-expert.md` F-020 | Useful after resource/auth/profile stages add tests; doing first would mostly reshuffle thresholds | Revisit after STAGE-007 and set risk-targeted gates for parser, auth, CORS, storage, Notepad, WebSocket |
| Constraint and tool-pin parity checks | `devops-engineer.md` F-021 | Lower severity than operational safety and release artifact gaps | Add a small script after release workflow shape is known |
| WebSocket/API/frontend/documentation specialist follow-up audits | `project-analysis-report.md` incomplete agent reports | Several specialist agents did not return structured reports in the analysis run | Run targeted follow-up after feature profiles stabilize |
| Method-level roles beyond coarse profiles | `security-auditor.md`, `architect-reviewer.md` | Coarse profiles give most risk reduction with less complexity | Reassess after STAGE-006 usage feedback |
| Long-running ACME in-process renewal/reload | `qa-expert.md`, `security-auditor.md` | Stage 008 can document restart-before-expiry and health behavior; in-process renewal is larger | Decide supported ACME operational model after Docker readiness stage |

