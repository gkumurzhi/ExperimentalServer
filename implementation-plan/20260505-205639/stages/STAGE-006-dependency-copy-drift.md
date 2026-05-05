# STAGE-006 - Remove stale crypto/dependency copy drift

## Status
CLOSED

## Priority
MEDIUM

## Source findings
- `codex-analysis/20260505-193249/project-analysis-report.md` - Documentation & Process: dependency-policy migration is partially reflected and `[crypto]` guidance is stale.
- `codex-analysis/20260505-193249/agent-reports/dependency-manager.md` - LOW/MEDIUM: empty `[crypto]` extra is compatible but user-facing text is stale.
- `codex-analysis/20260505-193249/agent-reports/documentation-engineer.md` - MEDIUM: README/CLAUDE/docs/runtime errors/UI strings retain old assumptions.
- `codex-analysis/20260505-193249/agent-reports/frontend-developer.md` - MEDIUM: frontend strings and smoke tests lock stale `exphttp[crypto]` copy.
- `codex-analysis/20260505-193249/agent-reports/security-auditor.md` - LOW: Secure Notepad failure messages recommend empty extra.

## Goal
Align source, UI, docs, and smoke expectations with the current dependency policy: `cryptography` and `acme` are default runtime dependencies; `[crypto]` is only a no-op compatibility extra if kept.

## Non-goals
- Do not remove the `[crypto]` extra from package metadata unless the owner explicitly chooses a breaking change.
- Do not change dependency pins; STAGE-007 owns tooling dependency alignment.
- Do not change Notepad key contract; STAGE-002 owns cryptographic interoperability.

## Scope
### Likely files to inspect
- `pyproject.toml` - declared runtime dependencies and empty compatibility extra.
- `src/request_pipeline.py` - WebSocket/Notepad crypto-unavailable runtime message.
- `src/handlers/notepad.py` - NOTE crypto-unavailable runtime message.
- `src/data/static/ui/core.js` - UI copy and localized/unavailable strings.
- `tools/browser_smoke.playwright.js` - smoke expectations for unavailable Notepad text.
- `README.md`, `CLAUDE.md`, `docs/index.md`, `docs/ADR/ADR-003-cryptography-optional.md`, `mkdocs.yml`, `CONTRIBUTING.md` - stale dependency wording.

### Likely files to change
- `src/request_pipeline.py` - replace `install exphttp[crypto]` remediation.
- `src/handlers/notepad.py` - replace `install exphttp[crypto]` remediation.
- `src/data/static/ui/core.js` - replace stale UI strings.
- `tools/browser_smoke.playwright.js` - update expected copy.
- `README.md`, `CLAUDE.md`, `docs/index.md`, `CONTRIBUTING.md`, `mkdocs.yml` - reword default dependency policy and ADR nav label.
- `.github/workflows/ci.yml` or a new checker - optional stale-reference guard enhancement after STAGE-001.

### Files that must not be changed
- `constraints/ci.txt` and `.pre-commit-config.yaml` - dependency tooling alignment is STAGE-007.
- `API.md` Notepad key details - STAGE-002 owns exact key contract.
- `.env*`, credentials, keys, certificates - never read or edit secrets.

## Dependencies
- Depends on: STAGE-001
- Blocks: STAGE-007

## Implementation steps
1. Enumerate all active `exphttp[crypto]`, "zero external dependencies", "pure Python", and "Optional cryptography" references.
2. Classify references as active guidance vs historical/changelog/ADR context.
3. Replace active guidance with wording that says default install includes required crypto/ACME runtime dependencies and broken environments should be repaired/reinstalled.
4. Update browser smoke expectations that intentionally assert the old UI message.
5. Add or update stale-reference checks with allowlists for historical mentions.
6. Sync docs and build the docs site.

## Acceptance criteria
- [x] Active runtime/UI messages no longer tell users to install `exphttp[crypto]` as a fix.
- [x] Active README/docs setup text no longer claims zero external dependencies for the current default runtime.
- [x] `[crypto]` is documented, if mentioned, as compatibility-only/no-op.
- [x] Browser smoke expectations match the new UI copy.
- [x] Historical references are either allowed explicitly or reworded without breaking changelog/ADR meaning.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Stale-reference scan | `rg -n "exphttp\\[crypto\\]|zero external|Optional cryptography|pure Python" README.md API.md docs examples CLAUDE.md src tools .github` | Only approved historical/compatibility references remain |
| Docs sync | `python tools/sync_docs.py --check` | Reports mirrors in sync |
| Docs build | `mkdocs build --strict` | Passes |
| UI smoke target | `python tools/browser_smoke.py` if browser tooling is available | Passes with new strings |

## Suggested subagents
- `explorer` - list active vs historical stale dependency references.
- `worker` - update source/UI/docs/smoke copy in a single bounded patch.
- `documentation-engineer` - review wording consistency and docs sync.

## Risks and rollback
- Risk: Removing every `[crypto]` mention can hide compatibility-extra intent.
- Rollback: Restore a single explicitly labeled compatibility note while keeping runtime remediation text accurate.

## Completion notes
Closed 2026-05-05 23:06:14 MSK. Runtime, UI, setup docs, CI/PR install examples, MkDocs navigation, and browser smoke expectations now describe crypto/ACME as default runtime dependencies and direct broken environments to repair or reinstall the default runtime install. The `[crypto]` extra remains only as empty compatibility metadata/context. Verification passed: stale-reference checker, targeted stale-check tests, docs sync, MkDocs strict build, ruff, JS syntax check, full browser smoke, and subagent verification.
