# STAGE-019 — Reduce Upload Memory Spikes

## Status
OPEN

## Priority
MEDIUM

## Source findings
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/performance-engineer.md` — MEDIUM: upload receive path buffers/copies full request bodies
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/performance-engineer.md` — MEDIUM: advanced upload and notepad transports multiply payload memory

## Goal
Request upload paths reject oversized bodies earlier and cap memory-heavy base64/header/url transports.

## Non-goals
- Do not rewrite all request I/O to true streaming unless it fits this stage.
- Do not alter cryptographic fail-closed behavior already owned by STAGE-013.

## Scope
### Likely files to inspect
- `src/http/io.py` — receive loop and Content-Length handling
- `src/http/request.py` — raw/body split
- `src/request_pipeline.py` — payload-size check timing
- `src/handlers/advanced_upload.py` and `src/notepad_service.py` — base64/transports

### Likely files to change
- `src/http/io.py` — early Content-Length rejection after headers
- `src/handlers/advanced_upload.py` — lower caps for header/url/base64 transports
- `tests/test_http/test_content_length_smuggling.py` and advanced upload tests — regressions

### Files that must not be changed
- `uploads/**` — runtime user data; do not inspect contents unless an explicit disposable test fixture is created
- `notes/**` — encrypted runtime note data; do not inspect contents
- `.env*`, `*.key`, `*.pem`, `*.p12`, `*.pfx`, credential JSON — secret-heavy files
- `codex-analysis/**` — source analysis artifacts; read-only evidence only
- `implementation-plan/**` — planning artifacts; close-plan-stage may update status/report files only

## Dependencies
- Depends on: STAGE-012, STAGE-013
- Blocks: None

## Implementation steps
1. Reject declared oversized `Content-Length` before reading the full body when possible.
2. Set explicit limits for advanced-upload header/url transports and decoded payload sizes.
3. Ensure over-limit behavior returns a clear response or connection handling consistent with existing parser constraints.
4. Add tests for early rejection and transport-specific caps.

## Acceptance criteria
- [ ] Oversized declared bodies are rejected before full allocation where headers are parseable.
- [ ] Header/url/base64 advanced upload paths have explicit documented limits.
- [ ] Valid near-normal-size uploads continue to work.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `pytest tests/test_http/test_content_length_smuggling.py tests/test_handlers/test_handler_integration.py -q` | Upload/framing tests pass |
| Type/lint/build | `python -m compileall src tests` | Compilation succeeds |
| Manual/static review | Inspect receive and advanced-upload allocation paths | Large allocations are rejected or bounded earlier |

## Suggested subagents
- `performance-engineer` — memory path review.
- `security-auditor` — over-limit behavior review.

## Risks and rollback
- Risk: Some clients using large header/url advanced uploads may be rejected.
- Rollback: Revert upload cap/receive-loop/test changes for this stage.

## Completion notes
Filled by `close-plan-stage`.
