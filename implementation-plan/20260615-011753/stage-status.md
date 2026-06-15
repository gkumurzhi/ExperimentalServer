# Stage Status

| Stage | Status | Priority | Title | Last attempt | Result | Report |
|---|---|---|---|---|---|---|
| STAGE-001 | CLOSED | MEDIUM | Docs mirror and release hygiene | 2026-06-15 12:50:25 +0300 | Docs mirrors synced, local docs guardrails added, release/install wording clarified. | `stage-reports/STAGE-001-20260615-124223.md` |
| STAGE-002 | CLOSED | MEDIUM | Profile and exposure decision gate | 2026-06-15 13:04:45 +0300 | Profile/default ADR added; README, security, threat-model, and Docker status docs updated. | `stage-reports/STAGE-002-20260615-125438.md` |
| STAGE-003 | CLOSED | MEDIUM | Capability policy boundary | 2026-06-15 13:26:08 +0300 | Shared FeatureSet policy helpers now drive registry, CORS, mutation guard, and WebSocket admission; explicit feature setup added to handler tests. | `stage-reports/STAGE-003-20260615-130908.md` |
| STAGE-004 | CLOSED | MEDIUM | Safe default workspace migration | 2026-06-15 13:59:42 +0300 | Default profile migrated to workspace; deprecated advanced-upload alias maps to lab; docs and tests cover default-safe behavior plus explicit lab compatibility. | `stage-reports/STAGE-004-20260615-133030.md` |
| STAGE-005 | CLOSED | MEDIUM | Notepad UI and accessibility hardening | 2026-06-15 14:34:39 +0300 | Static Notepad UI now respects fine-grained delete/clear capabilities, exposes accessible warning/label text, announces detailed save errors, and verifies destructive focus behavior. | `stage-reports/STAGE-005-20260615-140638.md` |
| STAGE-006 | CLOSED | MEDIUM | Profile-aware smoke and risk test gates | 2026-06-15 15:00:26 +0300 | Browser smoke now gates lab/full plus workspace and serve disabled states; CI exposes named risk lanes for parser/framing, auth, CORS/profile, storage/quota, and WebSocket/Notepad. | `stage-reports/STAGE-006-20260615-144027.md` |
| STAGE-007 | CLOSED | MEDIUM | Python 3.14 readiness | 2026-06-15 15:39:55 +0300 | Python 3.14 added to constrained CI and package/security readiness; metadata/docs widened after local 3.14 smoke, audit, tests, and wheel install passed. | `stage-reports/STAGE-007-20260615-150708.md` |
| STAGE-008 | CLOSED | MEDIUM | Docker and rollback boundary | 2026-06-15 16:08:11 +0300 | Docker image/Compose now use explicit workspace profile, release artifacts retain for 90 days, docs state Python rollback and operator-owned container boundary, and Docker smoke asserts workspace profile. | `stage-reports/STAGE-008-20260615-154500.md` |
| STAGE-009 | CLOSED | MEDIUM | Workspace performance baseline | 2026-06-15 16:40:18 +0300 | Workspace hot-path benchmarks added, no-limit upload quota scan removed, and local pytest-benchmark baselines recorded. | `stage-reports/STAGE-009-20260615-161853.md` |
| STAGE-010 | OPEN | MEDIUM | API contract stability | - | - | - |
| STAGE-011 | OPEN | MEDIUM | WebSocket and Notepad safety | - | - | - |
