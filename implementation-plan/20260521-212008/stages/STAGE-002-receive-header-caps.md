# STAGE-002 - Add receive-layer header caps and parser telemetry

## Status
CLOSED

## Priority
HIGH

## Source findings
- `project-analysis-report.md` - F-002: request headers are effectively bounded by upload cap and pre-auth parsing can spend memory before rejection.

## Goal
Enforce a hard, configurable HTTP header size cap before body buffering and record receive-layer rejection reasons without changing normal request behavior.

## Non-goals
- Do not implement worker admission/backpressure in this stage.
- Do not redesign the request parser protocol.

## Scope
### Likely files to inspect
- `src/http/io.py` - socket read loop and header/body framing.
- `src/server.py` - `_receive_request`, max-size plumbing, metrics hooks.
- `src/cli.py` - operator-facing cap option if needed.
- `tests/test_http/test_io.py`, `tests/test_http/test_content_length_smuggling.py` - parser coverage.

### Likely files to change
- `src/http/io.py` - explicit header byte limit and rejection reason.
- `src/server.py` / `src/metrics.py` - receive rejection metric hook.
- `tests/test_http/*` - oversized/slow header regression tests.
- Docs only if a new operator flag is introduced.

### Files that must not be changed
- Static UI files - unrelated.

## Dependencies
- Depends on: STAGE-001
- Blocks: STAGE-003, STAGE-008

## Implementation steps
1. Add tests for oversized headers below/above body cap and before body reads.
2. Add a default header cap such as 64 KiB with a bounded CLI/config path if appropriate.
3. Ensure conflicting/invalid `Content-Length` behavior remains unchanged.
4. Add receive-layer telemetry for header-too-large, body-too-large, timeout, and framing rejection where practical.
5. Update API/operator docs only for observable behavior.

## Acceptance criteria
- [x] Headers over the cap are rejected before body buffering.
- [x] Body upload cap and header cap are independent.
- [x] Existing duplicate/conflicting `Content-Length` tests still pass.
- [x] Receive rejection reasons can be observed or tested.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Parser tests | `pytest -q tests/test_http/test_io.py tests/test_http/test_content_length_smuggling.py` | Pass. |
| Server helper tests | `pytest -q tests/test_server_methods.py -k 'payload_size or metrics or keep_alive'` | Pass or update selector to relevant tests. |
| Static review | Inspect read loop | No body read occurs after header cap violation. |

## Suggested subagents
- `explorer` - trace receive path and current rejection semantics.
- `backend-developer` - implement parser/server plumbing.

## Risks and rollback
- Risk: Too-low default header cap can reject legitimate clients.
- Rollback: Raise cap default or keep cap configurable while preserving tests.

## Completion notes
Closed 2026-05-21T23:01:52+03:00. Added a configurable receive-layer HTTP header cap (`--max-header-size`, default 64 KiB), parser rejection callbacks, metrics `receive_rejections` counters, and focused parser/server/CLI/docs coverage. A reviewer subagent found and re-checked a body/header boundary fix; targeted verification passed. Broad suite/typecheck failures were unrelated local dependency gaps (`hypothesis`, `acme`, `mypy`, older `cryptography`).
