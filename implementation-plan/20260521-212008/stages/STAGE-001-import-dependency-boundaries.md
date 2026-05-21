# STAGE-001 - Untangle package import and ACME dependency boundaries

## Status
CLOSED

## Priority
HIGH

## Source findings
- `project-analysis-report.md` - F-001: lightweight imports currently traverse package root/security/TLS and can pull ACME dependencies into unrelated paths.

## Goal
Make lightweight imports such as `import src.http` and HTTP parser tests independent of unrelated TLS/ACME modules, while keeping public package exports and dependency declarations explicit.

## Non-goals
- Do not remove TLS or ACME functionality.
- Do not make a breaking release decision about the compatibility-only `crypto` extra unless documented as a separate follow-up.

## Scope
### Likely files to inspect
- `src/__init__.py` - package root eager imports.
- `src/security/__init__.py` - TLS re-export import side effects.
- `src/security/tls.py` - direct ACME/josepy imports.
- `pyproject.toml` and `constraints/ci.txt` - dependency declarations.
- `tests/` - import-boundary and dependency completeness tests.

### Likely files to change
- `src/__init__.py` - make exports lazy or narrow.
- `src/security/__init__.py` - avoid eager TLS imports where not needed.
- `pyproject.toml` / constraints - declare direct runtime dependencies if direct API usage remains.
- `tests/test_import_boundaries.py` or adjacent tests - add regression coverage.

### Files that must not be changed
- `src/security/tls.py` ACME behavior - keep behavior intact unless only moving imports.

## Dependencies
- Depends on: None
- Blocks: STAGE-002, STAGE-004, STAGE-005

## Implementation steps
1. Capture current import graph for `src.http`, `src.security`, and `src.server`.
2. Add tests that fail if importing HTTP-only modules imports TLS/ACME modules.
3. Refactor package/security exports to avoid unrelated eager imports.
4. Decide whether direct `josepy` usage requires explicit dependency declaration; update dependency checks accordingly.
5. Preserve existing public import compatibility or document intentional changes.

## Acceptance criteria
- [x] `import src.http` does not import TLS/ACME modules.
- [x] HTTP parser tests can collect without TLS/ACME side effects.
- [x] Direct runtime dependency usage is declared or removed.
- [x] Existing package-level imports covered by tests still work or have documented compatibility notes.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Import boundary | `python -c "import sys, src.http; print(any(m.startswith('acme') for m in sys.modules))"` | Prints `False`. |
| Targeted tests | `pytest -q tests/test_import_boundaries.py tests/test_http/test_io.py` | Pass. |
| Dependency audit | `python tools/check_installed_dependencies.py` or existing dependency guard | Pass with no missing direct deps. |
| Static review | Inspect `src/__init__.py`, `src/security/__init__.py` | No unrelated eager TLS imports in HTTP-only paths. |

## Suggested subagents
- `explorer` - map import graph and existing compatibility tests.
- `python-pro` - review lazy import implementation and packaging side effects.

## Risks and rollback
- Risk: Package-level re-export changes can break consumers.
- Rollback: Restore eager exports and instead add explicit dependency declarations; keep import-boundary limitation documented.

## Completion notes
Closed 2026-05-21T22:35:20+03:00.

- Package root exports now resolve lazily, so `import src.http` no longer traverses server/security/TLS imports.
- `src.security` keeps TLS re-exports compatible through lazy attribute resolution, and ACME/josepy imports in `src.security.tls` are limited to ACME code paths.
- `josepy` is declared as a direct runtime dependency while the existing CI constraint pin remains in place.
- Added `tests/test_import_boundaries.py` coverage for HTTP-only import boundaries and public import compatibility with ACME/josepy blocked.
- Verification passed: import probes, targeted HTTP parser tests, HTTP parser collect-only, ruff, py_compile, targeted dependency declaration/pin audit, and subagent review.
- Environment-limited checks: the full installed dependency constraint guard reports unrelated globally installed packages in this shared interpreter; `mypy` is not importable from the local launcher; property parser collection needs `hypothesis`, which is not installed here.
