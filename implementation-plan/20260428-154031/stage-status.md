# Stage Status

| Stage | Status | Priority | Title | Last attempt | Result | Report |
|---|---|---|---|---|---|---|
| STAGE-001 | CLOSED | HIGH | Constrain Static Resource Paths | 2026-04-28 16:10:40 MSK | Static resource traversal blocked; targeted tests, compile, ruff, and verifier subagents passed. | `stage-reports/STAGE-001-20260428-155734.md` |
| STAGE-002 | CLOSED | HIGH | Preserve Streaming for Gzip Responses | 2026-04-28 18:32:48 MSK | Streamed gzip no longer buffers files; targeted tests, compile, ruff, and verifier subagents passed. | `stage-reports/STAGE-002-20260428-182050.md` |
| STAGE-003 | CLOSED | HIGH | Bound SMUGGLE Memory Use | 2026-04-28 20:46:27 MSK | SMUGGLE source reads are capped and temp HTML streams with one-shot cleanup; targeted tests, compile, ruff, and verifier subagents passed. | `stage-reports/STAGE-003-20260428-203152.md` |
| STAGE-004 | CLOSED | HIGH | Enforce WebSocket Client Masking | 2026-04-28 21:08:00 MSK | Inbound WebSocket client frames now require masks; unmasked `/notes/ws` frames close with `1002` before NOTE dispatch; targeted tests, compile, ruff, and verifier subagents passed. | `stage-reports/STAGE-004-20260428-205905.md` |
| STAGE-005 | CLOSED | HIGH | Make Inspector Asset Intentional | 2026-04-28 21:26:57 MSK | Inspector asset is intentionally tracked, package-covered, served, and browser-smoke verified; targeted tests, compile, ruff, wheel asset probe, and verifier subagents passed. | `stage-reports/STAGE-005-20260428-211543.md` |
| STAGE-006 | CLOSED | HIGH | Redact Inspector Raw and Copy Output | 2026-04-28 21:46:30 MSK | Inspector render, copy source, and stored state now redact advanced-upload and notepad sensitive fields; targeted tests, compile, JS syntax, browser smoke, static review, and verifier subagents passed. | `stage-reports/STAGE-006-20260428-213004.md` |
| STAGE-007 | CLOSED | HIGH | Harden Docker Build Context Ignores | 2026-04-28 22:40:57 MSK | Docker build context now excludes runtime data and secret-like files; runtime build, dummy-context checks, diff check, and verifier subagents passed. | `stage-reports/STAGE-007-20260428-223152.md` |
| STAGE-008 | OPEN | HIGH | Repair pip-audit Security Workflow | — | — | — |
| STAGE-009 | OPEN | HIGH | Correct SMUGGLE API Contract Docs | — | — | — |
| STAGE-010 | OPEN | HIGH | Correct API Error Contract Docs | — | — | — |
| STAGE-011 | OPEN | HIGH | Remove Stale CLAUDE Guidance | — | — | — |
| STAGE-012 | OPEN | MEDIUM | Reject Malformed Request Lines | — | — | — |
| STAGE-013 | OPEN | MEDIUM | Fail Closed for Advanced Upload Crypto Errors | — | — | — |
| STAGE-014 | OPEN | MEDIUM | Enforce Hidden Upload Policy Consistently | — | — | — |
| STAGE-015 | OPEN | MEDIUM | Make CORS Origin and Header Contract Valid | — | — | — |
| STAGE-016 | OPEN | MEDIUM | Validate WebSocket Frame Semantics | — | — | — |
| STAGE-017 | OPEN | MEDIUM | Bound WebSocket Resource Use | — | — | — |
| STAGE-018 | OPEN | MEDIUM | Clarify Metrics and Error Counting | — | — | — |
| STAGE-019 | OPEN | MEDIUM | Reduce Upload Memory Spikes | — | — | — |
| STAGE-020 | OPEN | MEDIUM | Align CI and Local Toolchain Pins | — | — | — |
| STAGE-021 | OPEN | MEDIUM | Set Dependency Authority and Update Coverage | — | — | — |
| STAGE-022 | OPEN | MEDIUM | Improve Docker Runtime Examples | — | — | — |
| STAGE-023 | OPEN | MEDIUM | Align UI Capabilities, A11y, and Smoke Checks | — | — | — |
| STAGE-024 | OPEN | MEDIUM | Clean Remaining Documentation Drift | — | — | — |
| STAGE-025 | OPEN | MEDIUM | Protect Runtime Note Data from Accidental Commit | — | — | — |
