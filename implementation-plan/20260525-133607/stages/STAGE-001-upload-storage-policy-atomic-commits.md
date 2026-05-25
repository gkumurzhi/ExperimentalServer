# STAGE-001 - Upload storage policy and atomic commits

## Status
CLOSED

## Priority
HIGH

## Source findings
- `codex-analysis/20260525-121051/project-analysis-report.md` - Critical & High Issues #1: repeated valid uploads can fill disk because `--max-size` is per request.
- `codex-analysis/20260525-121051/agent-reports/performance-engineer.md` - HIGH storage issue: standard and advanced uploads create files without aggregate quota or retention.
- `codex-analysis/20260525-121051/agent-reports/python-pro.md` - MEDIUM atomicity issue: upload writes open the final path directly, so partial files can become visible.

## Goal
Add a shared upload storage policy that rejects over-quota writes before commit and publishes standard/advanced upload files atomically.

## Non-goals
- Notepad quota enforcement; that is STAGE-002.
- Full streaming request-body receive refactor; that is STAGE-003.
- Docker volume quota configuration; that is STAGE-008.

## Scope
### Likely files to inspect
- `src/server.py` - owns upload directory creation and CLI-provided limits.
- `src/http/utils.py` - contains `write_unique_file_exclusive()` and path helpers.
- `src/handlers/files.py` - standard upload write path and upload clear behavior.
- `src/handlers/advanced_upload.py` - advanced upload write path.
- `tests/test_handlers/test_files.py` - file handler regression coverage.
- `tests/test_server_methods.py` - method-level upload behavior.

### Likely files to change
- `src/server.py` - construct and expose storage policy/service.
- `src/http/utils.py` or new `src/storage.py` - implement reservation, accounting, and atomic publish helpers.
- `src/handlers/files.py` - reserve quota and commit uploaded files atomically.
- `src/handlers/advanced_upload.py` - use same policy/atomic publish path.
- `src/cli.py` - add upload storage limit flags if policy is configured from CLI.
- `tests/` - add quota, rollback, concurrent naming, and atomic visibility tests.
- `docs/threat-model.md`, `README.md` - correct `--max-size` wording and document aggregate upload limits.

### Files that must not be changed
- `.env`, credentials, private keys, certificates - secrets must not be read or stored.
- `codex-analysis/**` - analysis artifacts are source evidence, not implementation targets.

## Dependencies
- Depends on: `None`
- Blocks: STAGE-002, STAGE-003, STAGE-006

## Implementation steps
1. Define the smallest storage policy/service API needed for upload files: total bytes, file count, reserved free space, and rejection result.
2. Add CLI/server configuration for upload aggregate limits and documented defaults.
3. Replace direct final-path writes with same-directory hidden temp writes followed by atomic rename.
4. Ensure quota reservations are released on handler errors and temp files are cleaned on failed writes.
5. Add regression tests for normal upload, over-quota rejection, no final file after write failure, and advanced upload parity.
6. Update docs that currently imply per-request `--max-size` mitigates disk fill.

## Acceptance criteria
- [ ] Standard and advanced uploads check aggregate upload policy before final publish.
- [ ] Over-quota upload attempts return a clear client error such as `413` or `507` and leave no final or stale temp artifact.
- [ ] Upload final files are published atomically from same-directory temp files.
- [ ] Existing concurrent unique-name behavior remains intact.
- [ ] Docs distinguish per-request size from aggregate disk quota.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `python -m pytest tests/test_handlers/test_files.py tests/test_server_methods.py` | Upload, advanced upload, and method tests pass with new quota cases |
| Type/lint/build | `ruff check src tests && ruff format --check src tests && mypy src` | No lint, format, or type regressions |
| Manual/static review | Review temp-file path generation and rename directory | Temp files are same-directory, hidden or clearly scoped, and not externally served before publish |

## Suggested subagents
- `explorer` - inspect current upload write paths and existing tests.
- `worker` - implement the storage policy and upload handler changes.
- `qa` - add quota and atomicity regression tests.

## Risks and rollback
- Risk: Overly strict default limits could break existing local workflows.
- Rollback: Keep new limits configurable and document defaults; revert the policy wiring while leaving atomic helper tests as guidance if needed.

## Completion notes
Closed 2026-05-25 14:09:57 MSK.

- Added shared upload storage policy/service with opt-in aggregate byte, file-count, and reserved-free-space limits.
- Standard and advanced upload handlers now publish through hidden same-directory temp files and atomic no-clobber links.
- Added CLI/server wiring, docs, quota/atomicity regression tests, and preserved concurrent unique-name behavior.
- Verification passed for targeted upload/server/CLI tests and ruff checks. Full-suite pytest and mypy were limited by missing/corrupt local optional dependencies unrelated to this stage; details are in the stage report.
