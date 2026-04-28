# STAGE-002 — Preserve Streaming for Gzip Responses

## Status
CLOSED

## Priority
HIGH

## Source findings
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/performance-engineer.md` — HIGH: `_maybe_gzip_response()` reads `response.stream_path.read_bytes()`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/python-pro.md` — HIGH: streamed files become buffered bodies under gzip
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/qa-expert.md` — HIGH: tests currently assert buffering behavior

## Goal
Large streamed file responses are not read fully into memory when clients request gzip.

## Non-goals
- Do not implement full streaming gzip unless it remains bounded and testable in one run.
- Do not change upload storage format.

## Scope
### Likely files to inspect
- `src/server.py` — `_maybe_gzip_response()` and `_send_response()`
- `src/http/response.py` — stream/body representation
- `tests/test_server_methods.py` and `tests/test_server_live.py` — gzip/file-serving coverage

### Likely files to change
- `src/server.py` — skip or bound gzip for `stream_path` responses
- `tests/test_server_methods.py` — update regression away from buffering assertion
- `CHANGELOG.md` only if behavior/user contract changes must be documented in a later docs stage

### Files that must not be changed
- `uploads/**` — runtime user data; do not inspect contents unless an explicit disposable test fixture is created
- `notes/**` — encrypted runtime note data; do not inspect contents
- `.env*`, `*.key`, `*.pem`, `*.p12`, `*.pfx`, credential JSON — secret-heavy files
- `codex-analysis/**` — source analysis artifacts; read-only evidence only
- `implementation-plan/**` — planning artifacts; close-plan-stage may update status/report files only

## Dependencies
- Depends on: None
- Blocks: STAGE-017, STAGE-018

## Implementation steps
1. Decide the minimal policy: skip gzip for `response.stream_path` responses, or only gzip below a conservative size threshold.
2. Implement the policy without converting large `stream_path` responses to `body`.
3. Adjust tests that currently assert streamed files become buffered gzip bodies.
4. Add a regression that a large compressible streamed file remains streamed or is explicitly uncompressed.

## Acceptance criteria
- [x] No large `stream_path` response path calls `read_bytes()` solely for gzip.
- [x] Small in-memory responses can still be gzip-compressed where supported.
- [x] Tests assert bounded-memory behavior rather than the old buffering behavior.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `pytest tests/test_server_methods.py tests/test_server_live.py -q` | Gzip and file-serving tests pass |
| Type/lint/build | `python -m compileall src tests` | Compilation succeeds |
| Manual/static review | Search for `read_bytes()` in response post-processing | No unbounded read remains for streamed gzip path |

## Suggested subagents
- `performance-engineer` — review memory behavior.
- `qa-expert` — ensure regression captures the old risk.

## Risks and rollback
- Risk: Clients expecting gzip for uploaded large text files may now receive identity encoding.
- Rollback: Revert gzip policy and test updates for this stage.

## Completion notes
Closed 2026-04-28 18:32:48 MSK. `_maybe_gzip_response()` now leaves `stream_path` responses streamed instead of reading them into memory for gzip. Buffered body gzip remains supported. Regression coverage now includes a `Path.read_bytes` failure guard for streamed gzip and a live GET with `Accept-Encoding: gzip` that confirms streamed text files are returned uncompressed with the original body.

Verification passed:
- `uv run --extra dev pytest tests/test_server_methods.py -q -k 'gzip or send_response_streams_file'`
- `uv run --extra dev pytest tests/test_server_live.py -q -k 'streamed_text_file_ignores_gzip'`
- `uv run --extra dev pytest tests/test_server_methods.py tests/test_server_live.py -q`
- `uv run --extra dev python -m compileall src tests`
- `uv run --extra lint ruff check src/server.py tests/test_server_methods.py tests/test_server_live.py`
- static search for `read_bytes()`, `gzip`, and `stream_path`
- performance, QA, and final verifier subagents passed.
