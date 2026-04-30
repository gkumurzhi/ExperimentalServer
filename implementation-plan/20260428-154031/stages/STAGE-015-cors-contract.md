# STAGE-015 — Make CORS Origin and Header Contract Valid

## Status
CLOSED

## Priority
MEDIUM

## Source findings
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/security-auditor.md` — comma-separated CORS allowlist emitted as invalid ACAO
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/api-documenter.md` — CORS methods/headers underspecified and inconsistent

## Goal
HTTP CORS responses emit browser-valid origins, methods, and exposed headers aligned with actual server behavior.

## Non-goals
- Do not redesign authentication.
- Do not change WebSocket origin behavior beyond keeping it consistent with parsed origins.

## Scope
### Likely files to inspect
- `src/http/response.py` — CORS headers
- `src/server.py` — WebSocket origin checks
- `src/handlers/files.py` — OPTIONS behavior
- `src/cli.py`/`src/config.py` — CORS config representation
- `API.md` docs deferred to STAGE-023

### Likely files to change
- `src/http/response.py` — reflect allowed request origin or reject comma ACAO output
- `src/server.py`/config — parse/store allowlist consistently
- `src/handlers/files.py` — preflight method/header behavior
- `tests/` — multi-origin, expose-header, and advanced-upload preflight regressions

### Files that must not be changed
- `uploads/**` — runtime user data; do not inspect contents unless an explicit disposable test fixture is created
- `notes/**` — encrypted runtime note data; do not inspect contents
- `.env*`, `*.key`, `*.pem`, `*.p12`, `*.pfx`, credential JSON — secret-heavy files
- `codex-analysis/**` — source analysis artifacts; read-only evidence only
- `implementation-plan/**` — planning artifacts; close-plan-stage may update status/report files only

## Dependencies
- Depends on: None
- Blocks: STAGE-023

## Implementation steps
1. Represent configured origins as a parsed allowlist or explicitly reject comma-separated origins at config/CLI level.
2. For allowlists, echo only the matching request `Origin` and set `Vary: Origin`.
3. Align allowed/exposed headers with `X-Request-Id`, `X-Smuggle-URL`, file metadata, and actual custom methods where appropriate.
4. Add tests for single origin, multi-origin, wildcard, and OPTIONS behavior with advanced upload on/off.

## Acceptance criteria
- [x] No HTTP response emits comma-separated `Access-Control-Allow-Origin`.
- [x] Allowed/exposed CORS headers match documented and implemented behavior.
- [x] Preflight responses do not imply unsupported unknown-method dispatch unless intentionally configured.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `pytest tests/test_server_methods.py tests/test_http/test_response.py -q -k "cors or options"` | CORS/OPTIONS tests pass |
| Type/lint/build | `python -m compileall src tests` | Compilation succeeds |
| Manual/static review | Inspect CORS headers for browser-valid values | ACAO is `*` or one origin only |

## Suggested subagents
- `api-documenter` — contract alignment.
- `security-auditor` — origin policy review.

## Risks and rollback
- Risk: Changing CORS reflection may affect clients configured with comma strings.
- Rollback: Revert CORS config/header/test changes for this stage.

## Completion notes
Closed 2026-04-29 20:54:06 MSK.

- Added a shared CORS contract helper module for origin parsing, methods, request headers, exposed headers, and preflight filtering.
- HTTP CORS now resolves per request `Origin`, echoes only a matching allowed origin, emits `Vary: Origin` for reflected origins, omits ACAO for missing/unlisted origins, and rejects mixed wildcard-plus-explicit origin configs.
- OPTIONS no longer advertises unknown methods unless `advanced_upload` is enabled, and preflight headers now include implemented auth/conditional/cache and advanced-upload request headers.
- Exposed headers now include implemented response metadata such as `X-Request-Id`, `X-Smuggle-URL`, `X-File-Modified`, and `ETag`.
- Verification passed: targeted CORS/OPTIONS tests (`15 passed`), scoped regression suite (`173 passed`), compileall, ruff, git diff check, and security/API/correctness verifier subagents.
