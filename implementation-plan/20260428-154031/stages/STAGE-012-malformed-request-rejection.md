# STAGE-012 — Reject Malformed Request Lines

## Status
CLOSED

## Priority
MEDIUM

## Source findings
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/python-pro.md` — MEDIUM: malformed request lines can reach handler dispatch and advanced-upload writes

## Goal
Malformed HTTP request lines return `400 Bad Request` before auth, dispatch, or upload side effects.

## Non-goals
- Do not replace the entire HTTP parser.
- Do not broaden advanced-upload semantics.

## Scope
### Likely files to inspect
- `src/http/request.py` — parse behavior and empty method/path defaults
- `src/request_pipeline.py` — parse/auth/dispatch order
- `src/handlers/__init__.py` — advanced-upload fallback routing
- `tests/test_http/` and `tests/test_handlers/test_handler_integration.py` — malformed/advanced-upload tests

### Likely files to change
- `src/http/request.py` — expose parse validity or raise controlled parse error
- `src/request_pipeline.py` — return 400 on invalid parse before dispatch
- `tests/` — add malformed request and advanced-upload side-effect regressions

### Files that must not be changed
- `uploads/**` — runtime user data; do not inspect contents unless an explicit disposable test fixture is created
- `notes/**` — encrypted runtime note data; do not inspect contents
- `.env*`, `*.key`, `*.pem`, `*.p12`, `*.pfx`, credential JSON — secret-heavy files
- `codex-analysis/**` — source analysis artifacts; read-only evidence only
- `implementation-plan/**` — planning artifacts; close-plan-stage may update status/report files only

## Dependencies
- Depends on: None
- Blocks: STAGE-013

## Implementation steps
1. Define a parser validity signal such as `parse_error`/`is_valid` or a controlled parse exception.
2. Update pipeline handling to return 400 for invalid method/path/version before advanced-upload routing.
3. Add tests for malformed request lines with and without body, including `advanced_upload=True`.
4. Verify valid unusual/custom methods still route according to advanced-upload rules.

## Acceptance criteria
- [x] Malformed request lines cannot create files through advanced upload.
- [x] Invalid parse failures return 400 consistently.
- [x] Valid standard and documented custom methods still work.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `pytest tests/test_http tests/test_handlers/test_handler_integration.py tests/test_request_pipeline.py -q` | Malformed request and pipeline tests pass |
| Type/lint/build | `python -m compileall src tests` | Compilation succeeds |
| Manual/static review | Inspect pipeline order | Invalid parse is handled before auth/dispatch side effects |

## Suggested subagents
- `python-pro` — parser contract implementation.
- `qa-expert` — regression design.

## Risks and rollback
- Risk: Some permissive malformed-client behavior may become rejected.
- Rollback: Revert parser/pipeline/test changes for this stage.

## Completion notes
- Closed: 2026-04-29 17:35:16 MSK
- Report: `stage-reports/STAGE-012-20260429-171354.md`
- Summary: `HTTPRequest` now exposes parser validity and rejects malformed request lines, invalid HTTP versions, invalid method tokens, and literal control/whitespace in request targets. `RequestPipeline` returns `400 Bad Request` immediately for invalid parses before keep-alive, auth, dispatch, or upload side effects, with a defense-in-depth guard before advanced-upload fallback in handler dispatch.
- Verification: `.venv/bin/python -m pytest tests/test_http tests/test_handlers/test_handler_integration.py tests/test_request_pipeline.py -q` (`147 passed`); `.venv/bin/python -m pytest tests/test_property/test_request_parser.py -q` (`2 passed`); `python -m compileall src tests`; scoped `ruff check`; `git diff --check`; explorer, QA, security, and repeat correctness verifier subagents passed after fixing an intermediate request-target whitespace bypass.
