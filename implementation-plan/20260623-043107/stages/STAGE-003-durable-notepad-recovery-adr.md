# STAGE-003 - Durable Notepad recovery ADR

## Status
OPEN

## Priority
MEDIUM

## Source findings
- `implementation-plan/20260615-011753/findings.md` - F-014: durable Notepad recovery remains a strategic open question with security implications.
- `implementation-plan/20260615-011753/backlog.md` - durable recovery needs an ADR covering envelope encryption, key wrapping, metadata privacy, nonces, recovery, and test vectors before implementation.

## Goal
Decide whether durable Secure Notepad recovery stays out of scope for now or moves forward later under a written cryptographic and product contract that is strong enough to support a future implementation plan.

## Non-goals
- Implementing durable recovery, sync, or multi-device key storage.
- Persisting current in-memory session keys.
- Expanding `/notes/ws` into a collaboration protocol.

## Scope
### Likely files to inspect
- `SECURITY.md` - current Notepad safety framing.
- `docs/threat-model.md` - storage, recovery, and key-handling assumptions.
- `API.md` - current Notepad and WebSocket behavior contracts.
- `README.md` - user-facing explanation of Secure Notepad scope.
- `docs/ADR/` - destination for the durable-recovery decision.

### Likely files to change
- `docs/ADR/` - new or updated durable-recovery decision record.
- `SECURITY.md` - align key-handling and persistence claims.
- `docs/threat-model.md` - capture the accepted or rejected recovery model.
- `README.md` - keep user-facing scope honest if recovery remains deferred.

### Files that must not be changed
- `src/**` - no persistence or cryptographic code changes belong in this stage.
- `tests/**` - the deliverable is a decision contract, not an implementation.

## Dependencies
- Depends on: STAGE-001
- Blocks: `None`

## Implementation steps
1. Gather current Secure Notepad scope, persistence assumptions, and deferred recovery notes from docs, threat model, and backlog artifacts.
2. Write an ADR that either explicitly rejects durable recovery for now or defines the minimum acceptable cryptographic/product model for a future implementation.
3. Align README, SECURITY, threat model, and any Notepad contract wording with that decision.

## Acceptance criteria
- [ ] The repository has one explicit durable-recovery ADR or equivalent decision record.
- [ ] Docs no longer leave ambiguous whether current Secure Notepad supports durable recovery.
- [ ] `python tools/check_stale_docs.py` passes after the scope wording is updated.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `python tools/check_stale_docs.py` | Secure Notepad scope wording remains coherent. |
| Type/lint/build | `python tools/sync_docs.py --check` | Mirrored docs stay synchronized if mirrored files change. |
| Manual/static review | Review ADR, SECURITY, threat model, README, and API Notepad wording together | Recovery stance, key-handling assumptions, and non-goals are explicit and internally consistent. |

## Suggested subagents
- `explorer` - collect current Notepad persistence/recovery statements and gaps.
- `worker` - draft the recovery ADR and aligned docs updates.
- `reviewer` - challenge any unsafe persistence shortcut or vague cryptographic promise.

## Risks and rollback
- Risk: The ADR could drift into implementation detail without enough product commitment.
- Rollback: Revert the ADR/docs commit and restage with a narrower decision statement focused on scope and prerequisites.

## Completion notes
Filled by `close-plan-stage`.
