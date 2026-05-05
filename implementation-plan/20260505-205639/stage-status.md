# Stage Status

| Stage | Status | Priority | Title | Last attempt | Result | Report |
|---|---|---|---|---|---|---|
| STAGE-001 | CLOSED | HIGH | Restore release-smoke stale-doc guard | 2026-05-05 21:25:59 MSK | Replaced brittle stale-doc grep with active-doc checker; release-smoke sanity block passes locally. | `stage-reports/STAGE-001-20260505-212559.md` |
| STAGE-002 | CLOSED | HIGH | Fix Secure Notepad key contract and example interoperability | 2026-05-05 21:43:24 MSK | Aligned the example HKDF contract with server/browser constants, documented recovery/metadata limits, added interoperability regression, and synced docs. | `stage-reports/STAGE-002-20260505-213422.md` |
| STAGE-003 | CLOSED | HIGH | Validate ACME cert/key cache pairs before reuse | 2026-05-05 22:08:12 MSK | Added sanitized ACME cert/key pair validation before primary, legacy, and newly obtained cache reuse; targeted TLS/security verification passed. | `stage-reports/STAGE-003-20260505-214641.md` |
| STAGE-004 | CLOSED | HIGH | Normalize CLI TLS source and numeric validation | 2026-05-05 22:22:27 MSK | Added bounded CLI numeric validation, explicit TLS source rejection for invalid cert/key and ACME combinations, and server constructor primary-limit guards; targeted verification passed. | `stage-reports/STAGE-004-20260505-221247.md` |
| STAGE-005 | CLOSED | HIGH | Complete container ACME/sslip operator path | 2026-05-05 22:41:47 MSK | Added opt-in ACME Compose profile, documented Docker/NAT/sslip prerequisites, and preserved the default plain HTTP container path; verification passed. | `stage-reports/STAGE-005-20260505-223234.md` |
| STAGE-006 | CLOSED | MEDIUM | Remove stale crypto/dependency copy drift | 2026-05-05 23:06:14 MSK | Removed stale crypto-extra/runtime dependency guidance from active runtime/UI/docs/smoke copy, documented compatibility-only references, and added active stale-reference guards; verification passed. | `stage-reports/STAGE-006-20260505-224442.md` |
| STAGE-007 | OPEN | MEDIUM | Align pre-commit and dependency completeness checks | - | - | - |
| STAGE-008 | OPEN | MEDIUM | Add Docker TLS and runtime import smoke | - | - | - |
| STAGE-009 | OPEN | MEDIUM | Guard Notepad plaintext title and dirty transitions | - | - | - |
| STAGE-010 | OPEN | MEDIUM | Make Notepad WebSocket saves idempotent | - | - | - |
| STAGE-011 | OPEN | MEDIUM | Add advanced-upload JSON body guardrails | - | - | - |
| STAGE-012 | OPEN | MEDIUM | Make user-data writes exclusive and atomic | - | - | - |
| STAGE-013 | OPEN | MEDIUM | Resolve local-only pytest collection drift | - | - | - |
