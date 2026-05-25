# STAGE-010 - Public package identity migration

## Status
CLOSED

## Priority
MEDIUM

## Source findings
- `codex-analysis/20260525-121051/agent-reports/architect-reviewer.md` - MEDIUM public API is generic `src` package.
- `codex-analysis/20260525-121051/agent-reports/python-pro.md` - MEDIUM distribution publishes generic `src`; quick win is `namespaces = false`.
- `codex-analysis/20260525-121051/agent-reports/qa-expert.md` - package/import migration is only partially represented.
- `codex-analysis/20260525-121051/project-analysis-report.md` - package migration should happen before broader public API expansion.

## Goal
Move the public import identity toward `exphttp`, protect package discovery, and keep a compatibility path for existing `src` users unless a breaking release is explicitly chosen.

## Non-goals
- Changing distribution name; it is already `exphttp`.
- Publishing a release; covered by STAGE-009.
- Refactoring unrelated module internals.

## Scope
### Likely files to inspect
- `pyproject.toml` - console script, dynamic version, package discovery, package data.
- `src/__init__.py`, `src/__main__.py`, `src/py.typed` - current public package surface.
- `tests/test_import_boundaries.py` - import contract tests.
- `tools/`, `examples/`, docs - references to `python -m src`, `from src`, and `import src`.
- `.github/workflows/ci.yml` - CLI/import smoke commands.

### Likely files to change
- `pyproject.toml` - add `namespaces = false`; update console script/import package when migration is implemented.
- `src/` and possibly new `exphttp/` or `src/exphttp/` layout - public package migration and compatibility shim.
- `tests/` - import contract tests for `exphttp` and optional `src` shim.
- `tools/`, `examples/`, `README.md`, `API.md`, docs - public import command updates.
- `.github/workflows/ci.yml` - installed import/CLI smoke updates.

### Files that must not be changed
- Release artifacts in `dist/`.
- Analysis reports.

## Dependencies
- Depends on: STAGE-009
- Blocks: None

## Implementation steps
1. Add `namespaces = false` and a package discovery test if not already added earlier.
2. Decide compatibility: keep `src` shim by default unless owner explicitly accepts a breaking rename.
3. Introduce `exphttp` as the documented import package and console-script target.
4. Preserve typed exports and `py.typed` behavior.
5. Update tests, tools, examples, docs, and CI smoke from `python -m src`/`from src` to `exphttp` where appropriate.
6. Add stale-doc checks for old public `src` references while allowing compatibility shim internals.

## Acceptance criteria
- [ ] `import exphttp` is the documented public import path and is tested.
- [ ] `exphttp --help` and `python -m exphttp --help` work from an installed wheel.
- [ ] Package discovery does not treat static asset directories as import packages.
- [ ] Existing `src` compatibility is either preserved with warnings/tests or deliberately removed with an explicit breaking-change note.
- [ ] Docs and examples no longer promote `from src` or `python -m src` as the primary API.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `python -m pytest tests/test_import_boundaries.py tests/test_cli.py tests/test_pytest_collection_policy.py` | Import, CLI, and collection policy tests pass |
| Isolated package smoke | `python -m build --wheel --outdir /tmp/exphttp-pkg-dist` then install in temp venv and run `exphttp --help` | Installed package exposes the expected public import/CLI |
| Docs guard | `python tools/check_stale_docs.py` | Public docs do not promote stale `src` API |
| Type/lint/build | `ruff check src tests tools && ruff format --check src tests tools && mypy src` | No lint, format, or type regressions |

## Suggested subagents
- `explorer` - inventory all `src` public references.
- `worker` - implement package migration and shim.
- `qa` - add installed-wheel import tests and stale-doc guard.

## Risks and rollback
- Risk: Import migration touches many docs/tests/tools and can create noisy diffs.
- Rollback: First close a narrower discovery-guard slice, then migrate docs/imports in a separate follow-up if the full rename is too large.

## Completion notes
Closed on 2026-05-25 20:51:55 MSK.

- Added the public `exphttp` package and `python -m exphttp` entry point while keeping `src` as a compatibility import path.
- Updated package discovery to include `exphttp*` and `src*` with `namespaces = false`, preserving `py.typed` and packaged static UI assets explicitly.
- Updated CI/release/security smoke commands, tools, tests, and public docs to use `exphttp`.
- Added regression coverage for `import exphttp`, installed CLI/module usage, `src` compatibility warnings, static asset namespace exclusion, and stale public `src` guidance.
- Verified with docs guard, lint/format/type checks, targeted pytest, isolated wheel build/install smoke, wheel static asset check, installed-package browser smoke, and `git diff --check`.
