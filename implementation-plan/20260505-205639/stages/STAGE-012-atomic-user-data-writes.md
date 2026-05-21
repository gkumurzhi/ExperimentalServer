# STAGE-012 - Make user-data writes exclusive and atomic

## Status
CLOSED

## Priority
MEDIUM

## Source findings
- `codex-analysis/20260505-193249/project-analysis-report.md` - Performance & Reliability: uploads use check-then-open `"wb"`; Notepad writes ciphertext and metadata non-atomically.
- `codex-analysis/20260505-193249/agent-reports/python-pro.md` - MEDIUM: upload writes can overwrite under concurrent requests and Notepad save is not atomic across sidecar files.
- `codex-analysis/20260505-193249/agent-reports/performance-engineer.md` - MEDIUM: concurrent uploads of same name can overwrite/truncate.

## Goal
Prevent concurrent upload overwrite/truncation and partial Notepad persistence by using exclusive creation and same-directory atomic replacement patterns for user data.

## Non-goals
- Do not stream standard uploads directly from sockets.
- Do not change encryption/HMAC algorithms.
- Do not migrate existing user data.

## Scope
### Likely files to inspect
- `src/handlers/files.py` - standard upload path selection and writes.
- `src/handlers/advanced_upload.py` - advanced upload path selection and writes.
- `src/notepad_service.py` - encrypted blob and metadata sidecar writes.
- `tests/test_handlers/test_files.py`, `tests/test_handlers/test_notepad.py`, `tests/test_server_live.py` - persistence behavior coverage.

### Likely files to change
- `src/handlers/files.py` - reserve unique destinations with exclusive creation or retry.
- `src/handlers/advanced_upload.py` - reserve/write final files atomically.
- `src/notepad_service.py` - write ciphertext/metadata through same-directory temp files and `replace()`.
- `src/handlers/base.py` or new utility module - optional shared atomic/exclusive write helper.
- `tests/` - concurrent same-name upload and Notepad failure-injection tests.

### Files that must not be changed
- `uploads/**`, `notes/**` - do not edit existing runtime/user data.
- `src/http/io.py` - streaming body redesign is out of scope.
- `.env*`, credentials, keys, certificates - never read or edit secrets.

## Dependencies
- Depends on: STAGE-011
- Blocks: `None`

## Implementation steps
1. Identify common write semantics needed for standard upload, advanced upload, and Notepad sidecars.
2. Add a small helper only if it reduces duplication without broad abstraction.
3. For uploads, reserve destination names with exclusive creation or a retrying same-directory temp/replace pattern that cannot truncate an existing concurrent file.
4. For Notepad, write ciphertext and metadata in an order that never leaves a successful response with mismatched files, and cleans temp files on failure.
5. Add concurrency/failure-injection tests for same-name uploads and metadata-write failure after ciphertext write.

## Acceptance criteria
- [ ] Two concurrent uploads targeting the same name cannot both truncate/write the same destination.
- [ ] Advanced upload destination handling has the same overwrite protection as standard upload.
- [ ] Notepad save does not leave new ciphertext paired with stale/missing metadata after a failed save.
- [ ] Temp files are same-directory and cleaned or harmless after failures.
- [ ] Existing upload and Notepad API responses remain compatible.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Upload tests | `pytest -q tests/test_handlers/test_files.py tests/test_server_live.py` | Passes with concurrent overwrite regression |
| Notepad tests | `pytest -q tests/test_handlers/test_notepad.py tests/test_websocket_handlers.py` | Passes with failure-injection regression |
| Cross-platform review | Inspect use of `Path.replace`, exclusive open, and temp naming | Works on supported Python/OS targets |
| Static data review | Confirm no tests write outside temp dirs | Runtime `uploads/**` and `notes/**` are untouched |

## Suggested subagents
- `explorer` - map existing upload/notepad write tests and temp-dir fixtures.
- `worker` - implement atomic/exclusive writes and tests.
- `python-pro` - review filesystem semantics and cross-platform behavior.

## Risks and rollback
- Risk: Atomic rename semantics differ on Windows if destination exists or files are open.
- Rollback: Revert helper and write-path changes; keep tests as skipped/xfail evidence until cross-platform approach is chosen.

## Completion notes
- 2026-05-21 20:39:40 MSK: Added exclusive destination reservation for standard and advanced uploads via `xb` file creation with retrying unique suffixes.
- 2026-05-21 20:39:40 MSK: Reworked Notepad persistence to write ciphertext and metadata through same-directory temporary files, replace final files atomically, and roll back to the prior pair on failed replacement.
- 2026-05-21 20:39:40 MSK: Added deterministic concurrent upload regressions and Notepad metadata-failure regressions. Required persistence suites, `ruff`, compile checks, and focused `mypy` passed.
