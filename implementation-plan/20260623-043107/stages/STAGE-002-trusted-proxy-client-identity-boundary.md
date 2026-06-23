# STAGE-002 - Trusted proxy and client identity boundary

## Status
OPEN

## Priority
MEDIUM

## Source findings
- `implementation-plan/20260615-011753/findings.md` - F-005: reverse-proxy throttling and identity semantics remain under-specified.
- `implementation-plan/20260615-011753/findings.md` - F-014: trusted-proxy support is strategic work that should not be bundled casually.
- `implementation-plan/20260615-011753/backlog.md` - trusted-proxy support is deferred pending a CIDR/model design.

## Goal
Document the maintained boundary for client identity: what “direct-peer semantics” mean today, when proxy-side throttling is required, and what prerequisites would have to be met before any trusted-proxy implementation work could begin.

## Non-goals
- Implementing `--trusted-proxy-cidr` or trusting forwarded headers.
- Changing current auth throttling code.
- Adding reverse-proxy runtime features.

## Scope
### Likely files to inspect
- `SECURITY.md` - security and deployment guidance.
- `README.md` - operator-facing deployment wording.
- `docs/threat-model.md` - trust-boundary and attacker-model language.
- `API.md` - any client-visible semantics tied to peer identity or deployment assumptions.
- `docs/ADR/` - decision record target for proxy identity policy.

### Likely files to change
- `docs/ADR/` - new or updated trusted-proxy boundary decision.
- `SECURITY.md` - clarify direct-peer semantics and proxy responsibilities.
- `README.md` - align deployment guidance with the decision.
- `docs/threat-model.md` - reflect the same boundary in security analysis.

### Files that must not be changed
- `src/**` - this stage must not add proxy-trust runtime behavior.
- `tests/**` - no code-path expansion is intended in this stage.

## Dependencies
- Depends on: STAGE-001
- Blocks: `None`

## Implementation steps
1. Gather every current reference to reverse proxying, peer IPs, throttling, and deployment trust boundaries across docs and ADRs.
2. Record the maintained policy in an ADR: either direct-peer-only support, or explicit prerequisites for future trusted-proxy support.
3. Align SECURITY, README, threat-model, and any API wording with that recorded policy.

## Acceptance criteria
- [ ] The repository has one explicit decision record for trusted-proxy/client-identity policy.
- [ ] Docs clearly distinguish current direct-peer semantics from any future trusted-proxy idea.
- [ ] `python tools/check_stale_docs.py` passes with the new wording.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `python tools/check_stale_docs.py` | Docs and security wording checks pass. |
| Type/lint/build | `python tools/sync_docs.py --check` | Mirrored docs remain synchronized if any mirrored files change. |
| Manual/static review | Review ADR, README, SECURITY, and threat model together | Proxy identity and throttling expectations are consistent and do not imply unsupported trust behavior. |

## Suggested subagents
- `explorer` - locate all current proxy/peer-identity wording and assumptions.
- `worker` - draft the ADR and related docs changes.
- `reviewer` - challenge ambiguities that could be misread as trusted-header support.

## Risks and rollback
- Risk: Wording may accidentally sound like partial trusted-proxy support even if the intent is deferral.
- Rollback: Revert the doc/ADR commit and restage with stricter direct-peer language.

## Completion notes
Filled by `close-plan-stage`.
