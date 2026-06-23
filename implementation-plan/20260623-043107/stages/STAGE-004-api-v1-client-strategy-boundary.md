# STAGE-004 - API v1 and client strategy boundary

## Status
CLOSED

## Priority
MEDIUM

## Source findings
- `implementation-plan/20260615-011753/findings.md` - F-011: the current custom-method surface is effectively a legacy v0 contract without a supported public-client roadmap.
- `implementation-plan/20260615-011753/findings.md` - F-014: API-client strategy needs product commitment before implementation.
- `implementation-plan/20260615-011753/backlog.md` - API v1 and SDK/client work are explicitly deferred pending a boundary decision.

## Goal
Define the supported API/client boundary: keep legacy v0 honest, record whether public clients are in scope, and state the acceptance bar for any future `/api/v1` or official SDK work.

## Non-goals
- Implementing `/api/v1`.
- Shipping an SDK or client library.
- Expanding handler behavior or error envelopes in code.

## Scope
### Likely files to inspect
- `API.md` - current legacy contract wording.
- `docs/api.md` - mirrored API surface.
- `README.md` - client-facing examples and expectations.
- `SECURITY.md` - support and exposure assumptions for clients.
- `docs/ADR/` - destination for the API/client strategy decision.

### Likely files to change
- `docs/ADR/` - new or updated API/client strategy ADR.
- `API.md` - clarify legacy v0 boundary and public-client stance.
- `docs/api.md` - mirrored contract updates.
- `README.md` - align examples and scope wording.

### Files that must not be changed
- `src/**` - this stage must not add API code or public-client features.
- `tests/**` - no implementation regression work belongs here.

## Dependencies
- Depends on: STAGE-001, STAGE-002
- Blocks: `None`

## Implementation steps
1. Audit the current legacy-v0 wording, examples, and client expectations across API docs, README, and security docs.
2. Write an ADR that records whether public clients are supported now, deferred, or out of scope, and what must be true before `/api/v1` or an SDK is planned.
3. Align API.md, docs/api.md, and README with that recorded boundary.

## Acceptance criteria
- [ ] The repository has one explicit API/client strategy decision record.
- [ ] API docs and README consistently describe the current surface as legacy v0 unless and until a future v1 plan is approved.
- [ ] `python tools/sync_docs.py --check` passes after the API doc updates.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `python tools/sync_docs.py --check` | Root and mirrored API docs stay in sync. |
| Type/lint/build | `python tools/check_stale_docs.py` | Client/public-surface wording remains consistent with safety guardrails. |
| Manual/static review | Review ADR, API.md, docs/api.md, README, and SECURITY together | Legacy v0 boundary, client expectations, and v1 entry criteria are explicit and non-contradictory. |

## Suggested subagents
- `explorer` - trace current API/client wording and example scope.
- `worker` - draft the ADR plus API/README updates.
- `reviewer` - check that the final wording does not accidentally promise a public stable client surface prematurely.

## Risks and rollback
- Risk: Docs may overcommit to a future v1/SDK direction that maintainers do not actually support.
- Rollback: Revert the ADR/docs commit and restage with a stricter legacy-v0-only boundary.

## Completion notes
- Added `ADR-010` to record the supported legacy-v0 client boundary and the entry criteria for any future `/api/v1` or official SDK work.
- Aligned `API.md`, `README.md`, and `SECURITY.md` so the built-in UI/examples remain documented as reference consumers of the legacy surface rather than an official public-client program.
- Added a `tools/check_stale_docs.py` semantic guard requiring the README to keep the legacy-v0 and no-`/api/v1` boundary explicit.
