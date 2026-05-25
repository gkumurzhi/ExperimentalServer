# STAGE-007 - Wildcard CORS read-only policy

## Status
OPEN

## Priority
MEDIUM

## Source findings
- `codex-analysis/20260525-121051/agent-reports/security-auditor.md` - MEDIUM wildcard CORS issue: wildcard allows browser mutations and WebSocket upgrades.
- `codex-analysis/20260525-121051/agent-reports/qa-expert.md` - MEDIUM tests currently assert wildcard mutation and WebSocket allow.
- `codex-analysis/20260525-121051/project-analysis-report.md` - Security section: make wildcard CORS read-only and require exact origins for mutations and WebSocket.

## Goal
Preserve wildcard read CORS responses while requiring exact configured origins for browser state-changing requests and WebSocket upgrades.

## Non-goals
- Reworking all profile capability gates; STAGE-006 owns that.
- Implementing credentialed CORS cookies or sessions.
- Browser UI redesign beyond text/capability updates needed for correctness.

## Scope
### Likely files to inspect
- `src/http/cors.py` - origin parsing and response header selection.
- `src/server.py` - browser mutation and WebSocket origin checks.
- `src/request_pipeline.py` - origin guard ordering.
- `tests/test_server_methods.py` - existing wildcard mutation/WS tests.
- `tests/test_security/test_websocket_upgrade.py` - WebSocket origin coverage.
- `API.md`, `README.md`, `SECURITY.md` - CORS docs.

### Likely files to change
- `src/server.py` - reject wildcard for mutation and WebSocket trust checks.
- `src/http/cors.py` - expose helpers if needed to distinguish read CORS from trusted origins.
- `tests/` - update wildcard mutation/WS tests to expect rejection and add exact-origin positive tests.
- `API.md`, `README.md`, `SECURITY.md` - document read-only wildcard semantics.

### Files that must not be changed
- Auth secret files or Docker secrets - out of scope.
- Handler profile model except consuming STAGE-006 capability method lists.

## Dependencies
- Depends on: STAGE-006
- Blocks: STAGE-008

## Implementation steps
1. Identify all code paths that treat `("*",)` as trusted browser origin.
2. Keep `Access-Control-Allow-Origin: *` for read-only CORS responses.
3. Require exact configured origins for browser mutations and WebSocket upgrade origins.
4. Update tests that currently assert wildcard mutation/WS allow.
5. Add exact-origin positive tests for mutations and WebSocket upgrades.
6. Update API/security docs and stale-doc guards if they reference wildcard write behavior.

## Acceptance criteria
- [ ] `--cors-origin *` does not authorize browser mutations.
- [ ] `--cors-origin *` does not authorize WebSocket upgrades.
- [ ] Exact configured origins still authorize intended mutations and WebSocket upgrades.
- [ ] Read-only wildcard CORS responses remain available.
- [ ] Documentation no longer says wildcard opts into browser write/WS trust.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `python -m pytest tests/test_server_methods.py tests/test_security/test_websocket_upgrade.py tests/test_request_pipeline.py` | Wildcard write/WS tests reject; exact-origin positive tests pass |
| Docs guard | `python tools/check_stale_docs.py` | No stale docs for wildcard mutation semantics |
| Type/lint/build | `ruff check src tests tools && ruff format --check src tests tools && mypy src` | No lint, format, or type regressions |

## Suggested subagents
- `explorer` - locate wildcard-origin behavior and stale docs.
- `worker` - implement policy and update tests.
- `qa` - add browser-origin regression coverage.

## Risks and rollback
- Risk: Lab users may rely on wildcard write behavior.
- Rollback: Require explicit exact origins for writes and document how lab users can list trusted origins; avoid restoring wildcard write trust.

## Completion notes
Filled by `close-plan-stage`.

