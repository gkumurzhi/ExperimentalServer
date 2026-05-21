# Findings

| Finding ID | Source | Severity | Area | Evidence | Root cause | Proposed outcome | Confidence |
|---|---|---:|---|---|---|---|---:|
| F-001 | `project-analysis-report.md` - Import and Dependency Boundaries Need Cleanup | MEDIUM | dependencies | Importing `src.http` currently executes package root/security imports, and TLS helpers import ACME dependencies at module import time. | Package `__init__` files eagerly re-export heavy subsystems. | Lightweight imports work without unrelated TLS/ACME side effects; direct dependencies are explicit. | High |
| F-002 | `project-analysis-report.md` - Request Admission and Pre-Auth Resource Controls Are Too Weak | HIGH | receive path | Request reading buffers headers/body before enough hard limits, and default upload cap also acts as practical header cap. | Receive-layer limits are coupled to upload limits. | Add explicit header caps, parser rejection telemetry, and tests for slow/oversized headers. | High |
| F-003 | `project-analysis-report.md` - Request Admission and Pre-Auth Resource Controls Are Too Weak | HIGH | concurrency | Accepted sockets are submitted to `ThreadPoolExecutor` without global admission/backpressure. | The stdlib executor queue is unbounded. | Add bounded admission before submit and preserve capacity for non-WebSocket work. | High |
| F-004 | `project-analysis-report.md` - Before Operation Beyond Trusted Local Use | HIGH | Notepad | Audit recommended Notepad encoded/decoded size limits for operation readiness. | Notepad encrypted blobs are governed mostly by transport/frame caps, not domain limits. | Add explicit note payload limits across HTTP and WS with docs/tests. | Medium |
| F-005 | `project-analysis-report.md` - Browser-Origin/CSP/UI Hardening Is Incomplete | MEDIUM | browser security | Mutating HTTP handlers rely on Basic Auth but do not enforce same-origin/CSRF policy. | Browser-driven mutation policy is not centralized. | Add Origin/Sec-Fetch or token guardrails for state-changing browser requests. | High |
| F-006 | `project-analysis-report.md` - Observability and Release Gates Are Not Enough for Operation | MEDIUM | operations | Metrics lack active/queued work, receive-layer drops, timeout/limit rejections, latency, and worker exception visibility. | Metrics are request-result counters, not admission/pressure observability. | Expose operational pressure and worker-failure signals. | High |
| F-007 | `project-analysis-report.md` - Browser-Origin/CSP/UI Hardening Is Incomplete; Observability and Release Gates | MEDIUM | frontend/release | CSP still allows inline script/style and CI lacked fast UI syntax/package-data gates in the audit. | UI validation and browser smoke gates were incomplete. | Add fast UI/package-data validation, pageerror/console capture, and staged CSP tightening. | Medium |
| F-008 | `project-analysis-report.md` - Public-Run and API Documentation Are Unsafe or Stale | HIGH | docs | README public-run examples and threat model wording can overstate operational safety. | Operator modes and semantic contract guards are not explicit enough. | Separate localhost/trusted-lab/external guidance and add semantic docs guards. | High |

## Already addressed by prior plan

The following source findings were intentionally not restaged because
`implementation-plan/20260505-205639` closed them:

- Corrupted bundled Notepad UI asset: STAGE-010 and later verification restored/validated the UI path.
- Notepad WebSocket idempotency: STAGE-010 closed with `opId` and `createIfMissing`.
- Advanced-upload JSON body guardrails: STAGE-011 closed.
- User-data atomic/exclusive writes: STAGE-012 closed.
- Local-only pytest collection drift: STAGE-013 closed.
