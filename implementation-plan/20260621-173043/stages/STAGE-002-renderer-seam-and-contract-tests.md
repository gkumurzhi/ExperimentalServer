# STAGE-002 - Renderer seam and contract tests

## Status
OPEN

## Priority
HIGH

## Source findings
- `codex-analysis/20260621-150449/agent-reports/architect-reviewer.md` - `crypto_js_src` is accepted but ignored in encrypted mode
- `codex-analysis/20260621-150449/agent-reports/qa-expert.md` - renderer HTML structure and escaping are not directly pinned
- `codex-analysis/20260621-150449/project-analysis-report.md` - renderer logic is monolithic and hard to evolve safely

## Goal
Stabilize the public renderer contract behind focused tests and a small internal seam so later UI or template work cannot silently break generated artifacts.

## Non-goals
- Changing the external `SMUGGLE -> JSON URL -> one-shot artifact` contract
- Introducing a new template engine or arbitrary template loading
- Reworking UI copy or dialog behavior

## Scope
### Likely files to inspect
- `src/utils/smuggling.py` - public renderer surface and template composition
- `exphttp/__init__.py` - public re-export boundary
- `tests/test_server_methods.py` - current handler-level expectations
- `pyproject.toml` - package-data coverage only if templates are extracted

### Likely files to change
- `src/utils/smuggling.py` - add a minimal renderer context/options seam and honor or remove `crypto_js_src`
- `tests/test_utils/test_smuggling.py` - direct plaintext/encrypted renderer tests
- `tests/test_server_methods.py` - one handler-level regression that proves the renderer contract still feeds the existing response flow
- `exphttp/__init__.py` - only if public export comments or import wiring need cleanup

### Files that must not be changed
- `src/features.py` - feature policy is unrelated
- `src/data/static/ui/files.js` - UI follow-up belongs to STAGE-004
- `deploy/` - deployment samples are out of scope here

## Dependencies
- Depends on: `STAGE-001`
- Blocks: `STAGE-004`

## Implementation steps
1. Add direct renderer tests for plaintext output, encrypted output, escaping-sensitive filenames, and the `crypto_js_src` path behavior.
2. Introduce the smallest internal options/context seam needed to keep payload preparation separate from HTML rendering.
3. Clean up the misleading `crypto_js_src` behavior by honoring it or removing it intentionally, then pin the chosen contract in tests.

## Acceptance criteria
- [ ] `generate_smuggling_html()` has direct regression coverage for plain and encrypted output
- [ ] The encrypted renderer no longer silently ignores `crypto_js_src`
- [ ] Handler-level SMUGGLE tests still pass without changing the external JSON/temp-artifact contract

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `./.venv/bin/pytest -q tests/test_utils/test_smuggling.py tests/test_server_methods.py` | PASS with renderer contract explicitly pinned |
| Type/lint/build | `./.venv/bin/pytest -q tests/test_security/test_crypto.py` | PASS if encrypted-path helpers are touched |
| Manual/static review | Review generated HTML fixtures or string output from the new renderer tests | Output contains the expected script path, escaping, and encrypted/plain markers |

## Suggested subagents
- `explorer` - inventory renderer inputs/outputs and the exact public API assumptions
- `worker` - implement the seam and targeted tests without expanding the public surface

## Risks and rollback
- Risk: a well-meant cleanup could accidentally alter the generated HTML contract used by STAGE-001 browser verification
- Rollback: revert the seam change and keep only the safe direct tests that describe current behavior

## Completion notes
Filled by `close-plan-stage`.
