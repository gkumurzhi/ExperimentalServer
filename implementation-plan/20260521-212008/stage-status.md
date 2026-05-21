# Stage Status

| Stage | Status | Priority | Title | Last attempt | Result | Report |
|---|---|---|---|---|---|---|
| STAGE-001 | CLOSED | HIGH | Untangle package import and ACME dependency boundaries | 2026-05-21T22:35:20+03:00 | Lazy package/security exports keep HTTP imports independent from TLS/ACME; targeted verification passed. | `stage-reports/STAGE-001-20260521-222446.md` |
| STAGE-002 | CLOSED | HIGH | Add receive-layer header caps and parser telemetry | 2026-05-21T23:01:52+03:00 | Configurable receive-layer header cap and rejection metrics added; reviewer boundary finding fixed; targeted parser/server/CLI/docs verification passed. | `stage-reports/STAGE-002-20260521-223742.md` |
| STAGE-003 | CLOSED | HIGH | Add bounded request admission before worker submission | 2026-05-21T23:13:56+03:00 | Request admission now bounds socket submission before worker enqueue; release and saturation verification passed. | `stage-reports/STAGE-003-20260521-230426.md` |
| STAGE-004 | OPEN | HIGH | Add Notepad payload size limits | - | - | - |
| STAGE-005 | OPEN | HIGH | Add browser-origin guardrails for mutating HTTP requests | - | - | - |
| STAGE-006 | OPEN | MEDIUM | Expand operational metrics and worker exception visibility | - | - | - |
| STAGE-007 | OPEN | MEDIUM | Harden UI validation and CSP release gates | - | - | - |
| STAGE-008 | OPEN | MEDIUM | Refresh operator docs and semantic contract guards | - | - | - |
