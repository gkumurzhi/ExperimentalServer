# STAGE-011 - Add advanced-upload JSON body guardrails

## Status
CLOSED

## Priority
MEDIUM

## Source findings
- `codex-analysis/20260505-193249/project-analysis-report.md` - Performance & Reliability: JSON body transport parses full JSON before advanced-upload cap.
- `codex-analysis/20260505-193249/agent-reports/performance-engineer.md` - MEDIUM: advanced upload JSON body can consume large memory before its 16 MiB cap.
- `codex-analysis/20260505-193249/agent-reports/api-documenter.md` - LOW: docs overstate early rejection for JSON bodies.

## Goal
Reject oversized advanced-upload JSON body transport before expensive JSON decoding/parsing and update docs/tests to match the actual guardrail.

## Non-goals
- Do not stream the request body from socket to disk in this stage.
- Do not change the standard upload global `max_upload_size` contract.
- Do not redesign advanced upload cryptography or HMAC order.

## Scope
### Likely files to inspect
- `src/handlers/advanced_upload.py` - body/header/url extraction and `_advanced_upload_encoded_size_limit`.
- `src/http/io.py` - global receive cap and body buffering.
- `tests/test_handlers/test_files.py` or advanced-upload tests - existing upload behavior.
- `API.md` and `docs/api.md` - advanced upload cap wording.

### Likely files to change
- `src/handlers/advanced_upload.py` - pre-parse body size guard for JSON transport.
- `tests/` advanced upload coverage - add oversized body transport test that proves JSON parse is avoided or rejected early.
- `API.md` - clarify JSON body guard and global receive cap relationship if needed.
- `docs/api.md` - regenerate/sync from `API.md`.

### Files that must not be changed
- `src/http/io.py` - no socket/body streaming redesign.
- `src/security/crypto.py` - no crypto behavior change.
- `uploads/**` - runtime/user data.
- `.env*`, credentials, keys, certificates - never read or edit secrets.

## Dependencies
- Depends on: STAGE-001
- Blocks: STAGE-012

## Implementation steps
1. Identify the encoded-size cap for body transport and the expected small JSON envelope overhead.
2. Add a pre-`json.loads` guard using `len(request.body)` for body transport.
3. Return the same kind of 413/error response as other advanced-upload cap violations.
4. Add a test that would fail if `json.loads` is called for a body far above the advanced-upload encoded cap.
5. Update API wording if it currently promises stronger early rejection than the implementation can provide.

## Acceptance criteria
- [x] Oversized advanced-upload JSON bodies are rejected before JSON parsing.
- [x] Header and URL transports keep their existing limits and behavior.
- [x] HMAC-before-decrypt ordering remains unchanged.
- [x] Tests cover the oversized JSON body transport path.
- [x] Docs accurately describe advanced-upload cap timing.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted advanced-upload tests | `pytest -q tests/test_handlers tests/test_server_methods.py` or the specific advanced-upload test file | Passes with new oversized body case |
| Docs sync | `python tools/sync_docs.py --check` if API docs changed | Reports mirrors in sync |
| Static review | Inspect `src/handlers/advanced_upload.py` | `json.loads` is not reached for bodies over the body-transport cap plus envelope |
| Regression check | Existing upload/advanced upload tests | Existing valid uploads still pass |

## Suggested subagents
- `explorer` - locate current advanced-upload tests and response conventions.
- `worker` - implement body guard and tests.
- `performance-engineer` - review guardrail placement and memory behavior.

## Risks and rollback
- Risk: A too-tight envelope allowance can reject valid JSON bodies near the cap.
- Rollback: Increase the documented envelope allowance or revert to previous behavior with docs warning.

## Completion notes
Closed 2026-05-21 20:24:32 MSK. Added a pre-parse JSON body size guard using the advanced-upload encoded payload cap plus a 4 KB JSON envelope allowance, leaving header and URL transport limits unchanged and preserving HMAC-before-decrypt ordering. Added regression coverage proving oversized JSON body transport returns 413 before `json.loads`, plus a valid JSON-at-limit case. Updated API docs and synced `docs/api.md`; targeted handler/server tests, docs sync, compile, ruff, whitespace diff, and static order checks passed.
