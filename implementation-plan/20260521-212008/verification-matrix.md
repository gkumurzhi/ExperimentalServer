# Verification Matrix

| Stage | Required checks | Optional checks | Known blockers | Baseline needed? |
|---|---|---|---|---|
| STAGE-001 | Minimal import checks, dependency audit, targeted tests | `pip check` in fresh env | None known | Yes - capture current import behavior |
| STAGE-002 | HTTP parser tests for header caps, oversized/slow header behavior | property parser cases | None known | Yes - receive path behavior |
| STAGE-003 | Admission saturation tests, keep-alive/WebSocket capacity tests | local socket stress smoke | None known | Yes - current worker metrics |
| STAGE-004 | NOTE HTTP/WS oversized payload tests, docs sync | browser smoke Notepad save | None known | Yes - current max-size/frame behavior |
| STAGE-005 | Origin/Sec-Fetch tests for mutating requests, compatibility tests | browser smoke with same-origin UI | Policy defaults must be explicit | Yes - current CORS/origin behavior |
| STAGE-006 | Metrics unit tests, worker exception logging tests | manual `/metrics` smoke | Depends on STAGE-003 signals | Yes - current metrics snapshot |
| STAGE-007 | `node --check`, package-data UI smoke, browser pageerror/console checks | CSP report-only trial | CSP tightening may need UI refactor | Yes - current CSP and smoke output |
| STAGE-008 | stale-doc/semantic guard tests, docs sync | README rendering/link check | Depends on final behavior from earlier stages | Yes - current docs wording |
