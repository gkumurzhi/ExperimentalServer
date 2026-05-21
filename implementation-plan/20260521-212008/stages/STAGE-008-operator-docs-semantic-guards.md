# STAGE-008 - Refresh operator docs and semantic contract guards

## Status
CLOSED

## Priority
MEDIUM

## Source findings
- `project-analysis-report.md` - F-008: public-run examples, threat model wording, and semantic API guards can lead operators to overestimate safety.

## Goal
Align README, SECURITY, API, threat model, and stale-doc guards with implemented operation-readiness behavior and clearly separate localhost, trusted-lab, and external-exposure modes.

## Non-goals
- Do not document controls that earlier stages did not implement.
- Do not create deployment-specific instructions for a particular reverse proxy unless already present.

## Scope
### Likely files to inspect
- `README.md`, `SECURITY.md`, `API.md`, `docs/api.md`, `docs/security.md`, `docs/threat-model.md`.
- `tools/check_stale_docs.py`, `tools/sync_docs.py`.
- `.github/workflows/ci.yml`, `CONTRIBUTING.md` if relevant.

### Likely files to change
- Operator-facing docs and mirrored docs.
- Semantic stale-doc guards for protocol fields and exposure guidance.
- CI/docs check wiring if missing.

### Files that must not be changed
- Source behavior except small semantic guard scripts/tests.

## Dependencies
- Depends on: STAGE-002, STAGE-004, STAGE-005, STAGE-007
- Blocks: None

## Implementation steps
1. Review behavior implemented by STAGE-002 through STAGE-007.
2. Rewrite public-run guidance around localhost, trusted lab, and external exposure prerequisites.
3. Correct threat-model wording for duplicate identical versus conflicting `Content-Length`.
4. Add semantic docs guards for finalized protocol fields, request caps, origin policy, and exposure warnings.
5. Sync docs mirrors and update contributor/release check instructions.

## Acceptance criteria
- [x] README quick-start does not imply safe internet exposure without prerequisites.
- [x] SECURITY and threat model match implemented controls.
- [x] API docs describe finalized Notepad, request-cap, origin, metrics, and CSP behavior.
- [x] Semantic docs guards fail on stale protocol/exposure wording.
- [x] Docs mirrors are in sync.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Docs sync | `python tools/sync_docs.py --check` | Pass. |
| Stale docs | `python tools/check_stale_docs.py` | Pass. |
| Semantic guard tests | `pytest -q tests/test_check_stale_docs.py` or new docs guard tests | Pass. |
| Static review | Read README/SECURITY/API threat-model sections | No stale or overbroad operational claims. |

## Suggested subagents
- `documentation-engineer` - update docs faithfully to implementation.
- `security-auditor` - review exposure guidance and threat model.

## Risks and rollback
- Risk: Docs may get ahead of implementation if dependencies are skipped.
- Rollback: Revert docs claims to conservative experimental/trusted-local wording.

## Completion notes
Closed 2026-05-22T00:23:17+03:00. README now separates localhost,
trusted-lab, and external-exposure modes and the quick-start no longer labels a
bare `0.0.0.0` bind as public access. SECURITY and the threat model now document
external-exposure prerequisites and the implemented Content-Length behavior.
API docs describe request framing caps, Notepad blob limits, browser-origin
mutation policy, operational metrics, and the current CSP contract. Semantic
stale-doc guards and tests cover exposure wording, Content-Length wording, and
required API/security contract sections; generated docs mirrors are in sync.
