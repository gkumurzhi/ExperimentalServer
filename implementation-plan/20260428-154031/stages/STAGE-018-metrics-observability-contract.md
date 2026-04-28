# STAGE-018 — Clarify Metrics and Error Counting

## Status
OPEN

## Priority
MEDIUM

## Source findings
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/python-pro.md` — MEDIUM: `/metrics` under-reports handler-produced 5xx
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/performance-engineer.md` — MEDIUM: metrics lack performance investigation signals

## Goal
Metrics semantics are explicit and reflect client-visible failures and basic performance/resource signals.

## Non-goals
- Do not integrate an external metrics system.
- Do not add expensive tracing.

## Scope
### Likely files to inspect
- `src/metrics.py` — counters and rendering
- `src/request_pipeline.py` — record calls
- `src/server.py` — response finalization and WS upgrades
- `docs/api.md`/`API.md` — metrics docs deferred or included if contract changes

### Likely files to change
- `src/metrics.py` — status/error semantics and optional gauges
- `src/request_pipeline.py`/`src/server.py` — record handler 5xx, direct errors, WS events
- `tests/test_request_pipeline.py` and metrics-related tests — expected counters
- `API.md`/`docs/api.md` if metrics contract changes are documented here or in STAGE-023

### Files that must not be changed
- `uploads/**` — runtime user data; do not inspect contents unless an explicit disposable test fixture is created
- `notes/**` — encrypted runtime note data; do not inspect contents
- `.env*`, `*.key`, `*.pem`, `*.p12`, `*.pfx`, credential JSON — secret-heavy files
- `codex-analysis/**` — source analysis artifacts; read-only evidence only
- `implementation-plan/**` — planning artifacts; close-plan-stage may update status/report files only

## Dependencies
- Depends on: STAGE-002
- Blocks: None

## Implementation steps
1. Define whether `total_errors` means exceptions, `>=500`, or `>=400`; prefer explicit `client_errors`/`server_errors` if needed.
2. Record handler-produced 5xx and direct auth/413/upgrade failures according to that contract.
3. Add lightweight latency/bytes/active connection or WS counters only if they can be maintained cheaply.
4. Update tests and docs for the selected metrics contract.

## Acceptance criteria
- [ ] Handler-returned 5xx responses are not invisible in metrics.
- [ ] Metrics docs/examples match implementation.
- [ ] Tests cover handler error, direct error, and normal response recording.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `pytest tests/test_request_pipeline.py tests/test_server_methods.py -q -k "metrics or error"` | Metrics/error tests pass |
| Type/lint/build | `python -m compileall src tests` | Compilation succeeds |
| Manual/static review | Review all `metrics.record` call sites | Each response path records consistently |

## Suggested subagents
- `performance-engineer` — operational signal review.
- `python-pro` — metrics contract implementation.

## Risks and rollback
- Risk: Existing dashboards/tests may rely on old `total_errors` semantics.
- Rollback: Revert metrics/pipeline/test/doc changes for this stage.

## Completion notes
Filled by `close-plan-stage`.
