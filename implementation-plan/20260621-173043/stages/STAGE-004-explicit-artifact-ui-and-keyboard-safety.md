# STAGE-004 - Explicit artifact UI and keyboard safety

## Status
OPEN

## Priority
HIGH

## Source findings
- `codex-analysis/20260621-150449/project-analysis-report.md` - current UI makes the `SMUGGLE` flow harder to inspect safely than it needs to be
- `codex-analysis/20260621-150449/agent-reports/frontend-developer.md` - current flow jumps from a terse row action to an immediate popup before the user can inspect the result
- `codex-analysis/20260621-150449/agent-reports/accessibility-tester.md` - initial focus lands on the side-effect action and success auto-opens before the result is inspectable

## Goal
Replace the current auto-open artifact flow with an explicit, keyboard-safe generated-result state that preserves the existing capability, dialog, and live-region contracts.

## Non-goals
- Introducing new artifact types or delivery variants
- Reworking the whole request panel or method matrix
- Changing server-side `SMUGGLE` capability policy

## Scope
### Likely files to inspect
- `src/data/index.html` - dialog/result-state structure and accessible labels
- `src/data/static/ui/files.js` - current artifact action, dialog behavior, focus, and success handling
- `src/data/static/ui/core.js` - dialog helpers, status announcements, and label text
- `tools/browser_smoke.playwright.js` - current focus, popup, and artifact assertions

### Likely files to change
- `src/data/index.html` - add or reshape the generated artifact result state
- `src/data/static/ui/files.js` - rename the action, change primary semantics to generate, stop auto-open, and add explicit follow-up actions
- `src/data/static/ui/core.js` - update any shared status text or accessible copy needed by the result state
- `tools/browser_smoke.playwright.js` - assert the new focus/result/open flow and preserved disabled-profile states

### Files that must not be changed
- `src/features.py` - supported-method gating must stay as-is
- `src/handlers/smuggle.py` - server contract changes belong to STAGE-001 or STAGE-002 only
- `README.md` - operator framing belongs to STAGE-003

## Dependencies
- Depends on: `STAGE-002`
- Blocks: `None`

## Implementation steps
1. Change the visible artifact action and dialog labels so the flow clearly means “generate artifact” rather than “open immediately”.
2. Render an explicit post-generation state with the generated URL, encryption state, and keyboard-focusable `Copy URL`, `Open`, and `Save` actions.
3. Update focus behavior and smoke coverage so keyboard users land on a safe first control, can tab through the result state, and still get correct focus restoration and disabled-profile behavior.

## Acceptance criteria
- [ ] The artifact flow no longer auto-opens on success
- [ ] Initial dialog focus no longer lands on the side-effect action
- [ ] Browser smoke proves the generated-result state and keyboard path in `lab`, while `workspace` and `serve` stay unavailable

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `python tools/browser_smoke.py --profile lab --mode full` | PASS with the updated artifact UI flow |
| Type/lint/build | `python tools/browser_smoke.py --profile workspace --mode disabled-state` and `python tools/browser_smoke.py --profile serve --mode disabled-state` | PASS with disabled profiles unchanged |
| Manual/static review | Keyboard-only pass through the artifact dialog/result state | Focus trap, Escape, Tab order, and return-focus behavior remain intact |

## Suggested subagents
- `explorer` - inventory current focus assumptions and smoke assertions around the artifact dialog
- `worker` - implement the result-state UI and matching smoke updates without regressing accessibility contracts

## Risks and rollback
- Risk: changing dialog/result structure can regress focus trap, live regions, or file-action accessible names
- Rollback: revert the UI flow change and keep only any safe label/status improvements that do not alter interaction order

## Completion notes
Filled by `close-plan-stage`.
