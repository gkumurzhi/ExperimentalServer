# STAGE-010 - API contract stability

## Status
OPEN

## Priority
MEDIUM

## Source findings
- `codex-analysis/20260614-225437/agent-reports/api-designer.md` - Summary: current API should be treated as legacy v0 before adding clients or broader publication.
- `codex-analysis/20260614-225437/agent-reports/documentation-engineer.md` - P2: API contract docs need a stability boundary before clients/v1.
- `codex-analysis/20260614-225437/project-analysis-report.md` - API Train: document current behavior as legacy v0 and design opt-in v1 only before SDK/client work.

## Goal
Document the current API as a legacy v0 contract with clear stability, discovery, retry, note ID, transport-error, and future v1 boundaries.

## Non-goals
- Do not implement `/api/v1` endpoints.
- Do not normalize existing legacy error shapes.
- Do not remove custom methods, advanced upload, SMUGGLE, NOTE, or WebSocket notes.

## Scope
### Likely files to inspect
- `API.md` and `docs/api.md` - current custom methods, `PING`, profiles/capabilities, NOTE, WebSocket, receive-layer errors.
- `src/features.py` - profile/capability public contract.
- `src/handlers/base.py`, `src/server.py`, `src/handlers/notepad.py` - current HTTP and WS error shapes.
- `tests/test_websocket_handlers.py`, `tests/test_server_methods.py`, `tests/test_handlers/test_notepad.py` - existing contract examples.
- `README.md` - external/client positioning.

### Likely files to change
- `API.md` and `docs/api.md` - add "Contract Stability" section for legacy v0, stable fields, non-stable metrics, retry/idempotency limits, note ID behavior, and v1 scope.
- `README.md` or `docs/index.md` - link or summarize API stability stance if public-client wording exists.
- `tests/**` - only if docs uncover an inconsistent example or a low-risk additive discovery field is approved.

### Files that must not be changed
- `src/handlers/**`, `src/server.py`, `src/websocket.py` - no API behavior changes in this documentation stage unless a verified docs bug requires a trivial example correction.
- SDK/client directories - none should be added.
- `.github/workflows/**` - CI changes are out of scope.
- `.env*`, credentials, keys, certificates - secrets are out of scope.

## Dependencies
- Depends on: STAGE-002
- Blocks: STAGE-011

## Implementation steps
1. Add an API contract stability section that names the current behavior legacy v0.
2. Document stable discovery fields: `profile`, `capabilities`, supported methods, and safe additive capability keys.
3. Document non-goals and non-stable areas: mixed legacy errors, advanced upload client ergonomics, SMUGGLE public API status, and metrics if not operator-facing.
4. Clarify note ID length/shape, retry/idempotency limits, and `opId` as correlation rather than dedupe unless STAGE-011 later changes behavior.
5. Document receive-layer transport close semantics separately from HTTP handler responses.
6. Keep v1 as opt-in future scope and list the smallest proposed surface without implementing it.

## Acceptance criteria
- [ ] `API.md` declares current behavior legacy v0 and states compatibility promises.
- [ ] Docs explain `PING`/capabilities as discovery and how capability keys may evolve.
- [ ] Docs clarify retry/idempotency limits, note ID behavior, and WebSocket `opId` semantics.
- [ ] Docs distinguish transport closes from HTTP error responses.
- [ ] v1 is described as future opt-in work, not implemented behavior.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Docs mirror check | `python tools/sync_docs.py --check` | Exits 0. |
| Stale-doc check | `python tools/check_stale_docs.py` | Exits 0. |
| Targeted tests | `python -m pytest tests/test_server_methods.py tests/test_websocket_handlers.py tests/test_handlers/test_notepad.py` | Exits 0 if any examples/contracts are touched. |
| Manual/static review | Compare API docs against current handler/server behavior | Docs describe existing behavior without promising unimplemented v1 behavior. |

## Suggested subagents
- `explorer` - map current API error/discovery examples.
- `worker` - draft API stability docs and sync mirrors.
- `api-reviewer` - review v0/v1 boundaries if available.

## Risks and rollback
- Risk: docs may accidentally promise v1 behavior or stronger stability than current tests support.
- Rollback: revert API docs to legacy-only language and move detailed v1 design into backlog.

## Completion notes
Filled by `close-plan-stage`.
