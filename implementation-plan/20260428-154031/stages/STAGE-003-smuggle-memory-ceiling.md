# STAGE-003 — Bound SMUGGLE Memory Use

## Status
CLOSED

## Priority
HIGH

## Source findings
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/performance-engineer.md` — HIGH: SMUGGLE creates multiple full-size representations
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/project-analysis-report.md` — Immediate action: prevent SMUGGLE large-file buffering

## Goal
SMUGGLE generation has an explicit source-size ceiling and avoids unnecessary full-file rereads where practical.

## Non-goals
- Do not redesign the entire HTML smuggling feature.
- Do not change static traversal handling; STAGE-001 owns that.

## Scope
### Likely files to inspect
- `src/handlers/smuggle.py` — SMUGGLE handler
- `src/utils/smuggling.py` — generated HTML and base64/XOR behavior
- `src/handlers/files.py` — serving temporary smuggle artifacts
- `tests/test_server_methods.py` — SMUGGLE coverage

### Likely files to change
- `src/handlers/smuggle.py` — enforce source-size limit and clear error
- `src/utils/smuggling.py` — avoid avoidable copies if feasible
- `tests/test_server_methods.py` — add over-limit and normal SMUGGLE tests
- `API.md` documentation deferred to STAGE-008/STAGE-023

### Files that must not be changed
- `uploads/**` — runtime user data; do not inspect contents unless an explicit disposable test fixture is created
- `notes/**` — encrypted runtime note data; do not inspect contents
- `.env*`, `*.key`, `*.pem`, `*.p12`, `*.pfx`, credential JSON — secret-heavy files
- `codex-analysis/**` — source analysis artifacts; read-only evidence only
- `implementation-plan/**` — planning artifacts; close-plan-stage may update status/report files only

## Dependencies
- Depends on: None
- Blocks: STAGE-008

## Implementation steps
1. Choose a conservative SMUGGLE source-size cap lower than general upload max, or derive one from configuration.
2. Reject over-cap SMUGGLE requests with a documented status/body shape.
3. Avoid serving generated temporary HTML through another full read if feasible within the existing response model.
4. Add tests for cap enforcement and ordinary small-file SMUGGLE behavior.

## Acceptance criteria
- [ ] SMUGGLE cannot process files near the full upload limit without an explicit cap decision.
- [ ] Over-cap requests return a predictable error without generating temp artifacts.
- [ ] Small-file SMUGGLE behavior remains functional.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `pytest tests/test_server_methods.py -q -k smuggle` | SMUGGLE tests pass |
| Type/lint/build | `python -m compileall src tests` | Compilation succeeds |
| Manual/static review | Inspect SMUGGLE code path for full-size duplicate reads | Remaining full-size copies are bounded by the new cap |

## Suggested subagents
- `performance-engineer` — validate memory ceiling.
- `api-documenter` — note contract details for later docs stage.

## Risks and rollback
- Risk: A cap may reject legitimate large SMUGGLE usage.
- Rollback: Revert SMUGGLE cap and tests for this stage.

## Completion notes
Closed 2026-04-28 20:46:27 MSK by `close-plan-stage`.

- Added an explicit 10 MiB SMUGGLE source-size cap, bounded by `max_upload_size` when lower.
- Rejects over-cap plaintext and encrypted SMUGGLE requests with 413 JSON before temp artifact creation.
- Bounded the source read to `limit + 1` bytes to avoid unbounded reads if the file grows after `stat()`.
- Streams temporary SMUGGLE HTML through `HTTPResponse.set_file()` with a cleanup callback instead of full-reading it into the response body.
- Ensured one-shot cleanup runs for streamed GET, bodyless HEAD, and conditional 304 responses.
- Verification passed: targeted SMUGGLE tests, full `tests/test_server_methods.py`, existing SMUGGLE routing tests, response tests, compileall, scoped ruff, diff check, and verifier subagents.
