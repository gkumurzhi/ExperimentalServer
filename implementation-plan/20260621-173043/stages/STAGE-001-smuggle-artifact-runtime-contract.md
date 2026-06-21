# STAGE-001 - SMUGGLE artifact runtime contract

## Status
OPEN

## Priority
HIGH

## Source findings
- `codex-analysis/20260621-150449/project-analysis-report.md` - Critical & High issue #1: generated artifacts are browser-broken under the current CSP
- `codex-analysis/20260621-150449/agent-reports/security-auditor.md` - generated pages rely on inline script while served with `script-src 'self'`
- `codex-analysis/20260621-150449/agent-reports/qa-expert.md` - encrypted positive path is not verified today

## Goal
Make generated `SMUGGLE` artifacts execute correctly in the supported `lab` browser flow without weakening the global UI CSP, and prove plain plus encrypted behavior end-to-end.

## Non-goals
- Adding new payload encodings, delivery tricks, or bypass-oriented variants
- Expanding `SMUGGLE` beyond the `lab` profile
- Relaxing the global UI CSP for normal application pages

## Scope
### Likely files to inspect
- `src/utils/smuggling.py` - current renderer output and inline-script assumptions
- `src/handlers/files.py` - HTML response headers and CSP application
- `src/handlers/smuggle.py` - generated artifact response contract and temp-file flow
- `tools/browser_smoke.playwright.js` - current artifact generation/open assertions
- `tests/test_server_methods.py` - server-level SMUGGLE artifact lifecycle coverage

### Likely files to change
- `src/utils/smuggling.py` - align generated artifact behavior with the chosen runtime contract
- `src/handlers/files.py` - scope any artifact-specific header handling without broadening the UI surface
- `src/handlers/smuggle.py` - expose only the minimum artifact metadata needed for verification
- `tools/browser_smoke.playwright.js` - assert the generated page actually reaches the claimed result
- `tests/test_server_methods.py` - add regression coverage for plain and encrypted artifact access

### Files that must not be changed
- `src/features.py` - profile gating is already a strength and must remain intact
- `src/settings.py` - public-direct policy is not part of this fix
- `README.md` - operator framing belongs to STAGE-003

## Dependencies
- Depends on: `None`
- Blocks: `STAGE-002`, `STAGE-004`

## Implementation steps
1. Reproduce the broken generated-artifact flow in code-first tests so the fix proves actual browser-visible behavior instead of only temp-file creation.
2. Pick the narrow execution model for generated HTML artifacts and implement it without weakening the global UI CSP for regular app pages.
3. Extend browser smoke and server tests to cover the plain and encrypted artifact path plus disabled-profile expectations.

## Acceptance criteria
- [ ] Opening a generated plain artifact in the supported `lab` flow completes its advertised action instead of stalling on the loading text
- [ ] The encrypted artifact path is positively verified, not only its rejection/limit cases
- [ ] Existing `workspace` and `serve` disabled-state behavior remains unchanged

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `./.venv/bin/pytest -q tests/test_server_methods.py tests/test_server_live.py` | PASS with no SMUGGLE runtime regressions |
| Type/lint/build | `./.venv/bin/pytest -q tests/test_http/test_io.py` | PASS if any header/CSP path changes touch response handling |
| Manual/static review | `python tools/browser_smoke.py --profile lab --mode full` plus disabled-state smoke for `workspace` and `serve` | Generated artifacts work in `lab`; disabled profiles stay blocked |

## Suggested subagents
- `explorer` - map the current artifact-serving header path and pinpoint where CSP is applied
- `worker` - implement the narrow runtime/CSP fix and the paired tests

## Risks and rollback
- Risk: a broad CSP relaxation would accidentally enlarge the browser attack surface
- Rollback: revert the artifact-specific runtime/CSP change and keep only any non-invasive test additions

## Completion notes
Filled by `close-plan-stage`.
