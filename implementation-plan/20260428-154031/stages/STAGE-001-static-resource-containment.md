# STAGE-001 — Constrain Static Resource Paths

## Status
CLOSED

## Priority
HIGH

## Source findings
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/security-auditor.md` — HIGH: `/static/...` can resolve outside bundled assets via `get_package_resource()`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/project-analysis-report.md` — Critical & High #1: static asset path traversal

## Goal
Requests for `/static/...` cannot resolve outside the packaged UI asset root, including encoded traversal attempts.

## Non-goals
- Do not redesign all file serving or upload path handling.
- Do not change runtime contents of `uploads/` or `notes/`.

## Scope
### Likely files to inspect
- `src/handlers/base.py` — package resource resolver
- `src/handlers/files.py` — static path routing
- `src/http/utils.py` — URL/path normalization helpers
- `tests/test_handlers/test_path_traversal.py` and `tests/test_http/test_path_traversal_prefix.py` — existing traversal coverage

### Likely files to change
- `src/handlers/base.py` — reject unsafe package resource paths and enforce asset root containment
- `src/handlers/files.py` — route static names through safe resolver behavior if needed
- `tests/**/test_*path*traversal*.py` or `tests/test_server_routing.py` — add encoded and raw `/static/../` regressions

### Files that must not be changed
- `uploads/**` — runtime user data; do not inspect contents unless an explicit disposable test fixture is created
- `notes/**` — encrypted runtime note data; do not inspect contents
- `.env*`, `*.key`, `*.pem`, `*.p12`, `*.pfx`, credential JSON — secret-heavy files
- `codex-analysis/**` — source analysis artifacts; read-only evidence only
- `implementation-plan/**` — planning artifacts; close-plan-stage may update status/report files only

## Dependencies
- Depends on: None
- Blocks: STAGE-014

## Implementation steps
1. Add a static-resource path validator that rejects empty parts, `.`, `..`, absolute paths, and platform separators after URL decoding.
2. Ensure the resolved package resource remains under the intended bundled data/static root before serving.
3. Return 404 or 400 for invalid static paths without leaking normalized filesystem paths.
4. Add regression tests for `/static/../../server.py`, encoded dot segments, and normal `/static/ui/...` assets.

## Acceptance criteria
- [x] Traversal attempts through `/static/...` cannot read repo/source files.
- [x] Valid bundled UI assets still resolve and serve normally.
- [x] Regression tests cover raw and URL-encoded traversal inputs.
- [x] No runtime user-data contents are read or changed.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `pytest tests/test_handlers/test_path_traversal.py tests/test_http/test_path_traversal_prefix.py tests/test_server_routing.py -q` | Traversal regressions pass and normal static serving remains green |
| Type/lint/build | `python -m compileall src tests` | Compilation succeeds |
| Manual/static review | Inspect resolver containment logic | No `startswith()` string-prefix containment is used |

## Suggested subagents
- `security-auditor` — validate containment and disclosure risk.
- `python-pro` — review pathlib/importlib.resources behavior.

## Risks and rollback
- Risk: Breaking packaged UI static assets if containment root is too narrow.
- Rollback: Revert resolver/routing changes and tests for this stage only.

## Completion notes
Closed at 2026-04-28 16:10:40 MSK. `get_package_resource()` now rejects unsafe decoded resource paths before package lookup and enforces resolved containment for filesystem-backed package and development resource paths. It does not return temporary `importlib.resources.as_file()` paths for non-filesystem resources. Added direct resolver and GET routing regressions for raw and URL-encoded `/static/...` traversal while preserving valid `/static/ui/app.js` serving.

Verification passed:
- `uv run --extra dev pytest tests/test_handlers/test_path_traversal.py tests/test_http/test_path_traversal_prefix.py tests/test_server_routing.py -q` (`52 passed`)
- `uv run python -m compileall src tests`
- `uv run --extra lint ruff check src/handlers/base.py tests/test_handlers/test_path_traversal.py tests/test_server_routing.py`
- Automatic verifier subagents: `security-auditor`, `python-pro`, and final `reviewer` passed with no blocking findings. An intermediate verifier found a non-filesystem `as_file()` lifetime issue; it was fixed and re-verified.

Report: `stage-reports/STAGE-001-20260428-155734.md`
