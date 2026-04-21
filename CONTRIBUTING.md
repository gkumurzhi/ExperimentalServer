# Contributing

Thanks for your interest! This project welcomes focused contributions.
Before you open a PR, please read the policies below — they keep the review
cycle short.

## Setup

```bash
git clone <repo-url>
cd ExperimentalHTTPServer
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[crypto,dev,lint]"
pre-commit install           # recommended: runs ruff/mypy/yaml checks on commit
```

To reproduce the pinned CI/docs/security toolchain locally, use the shared
constraints file:

```bash
PIP_CONSTRAINT=constraints/ci.txt pip install -e ".[crypto,dev,lint,test]"
```

## Branching

- Work from `main` on a feature branch: `feature/<short-slug>`, `fix/<issue>`,
  `security/<id>`, `docs/<area>`.
- **`main` is protected.** All changes land via PR with a passing CI.
- Rebase, do not merge, when updating your branch from `main`
  (`git pull --rebase origin main`).

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short imperative summary>

<body, wrapped at 72 cols, explaining WHY>

Refs: #123
```

Types we use:

| Type       | When to use                                        |
|------------|----------------------------------------------------|
| `feat`     | New user-facing capability                         |
| `fix`      | Bug fix — include reproducer in the body           |
| `security` | Security-impacting change — link advisory ID       |
| `perf`     | Measurable performance improvement                 |
| `refactor` | Internal change, no behavior shift                 |
| `test`     | Tests only, no production change                   |
| `docs`     | Documentation only                                 |
| `ci`       | CI/workflow/tooling change                         |
| `deps`     | Dependency bump (often by Dependabot)              |
| `chore`    | Anything else that doesn't change behavior         |

Breaking changes get a `!` after the type (`feat!:`) and a `BREAKING CHANGE:`
footer.

## Running checks locally

The CI (`.github/workflows/ci.yml`) runs all of these — run them locally
first to avoid round-trips.

When you need to reproduce CI package resolution exactly, prefix the install
step with `PIP_CONSTRAINT=constraints/ci.txt`.

```bash
ruff check src tests
ruff format --check src tests
mypy src
pytest --cov=src --cov-report=term-missing
python tools/sync_docs.py --check
# optional when docs extras are installed
mkdocs build --strict
```

Coverage gate in CI is 65 %; aim higher.

## Documentation ownership

- `README.md` is the repository landing page and stays root-only.
- `docs/index.md`, `docs/architecture.md`, `docs/threat-model.md`, and
  `docs/ADR/*` are docs-site pages and stay `docs/`-canonical.
- `API.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, and `SECURITY.md` are
  root-canonical and are generated into `docs/` by `tools/sync_docs.py`.
- After editing a root-canonical document, run
  `python tools/sync_docs.py --write` and commit both the root file and its
  generated `docs/` mirror.

## Pull request checklist

Reviewers look for (the template in `.github/PULL_REQUEST_TEMPLATE.md`
restates this):

- [ ] Tests added or updated; `pytest` green locally.
- [ ] `ruff check` and `ruff format --check` pass.
- [ ] `mypy src` has no **new** errors.
- [ ] `CHANGELOG.md` updated under `[Unreleased]` with the appropriate
      section (`Added`, `Changed`, `Fixed`, `Security`, `Performance`,
      `Deprecated`, `Removed`).
- [ ] Root-canonical docs regenerated with `python tools/sync_docs.py --check`.
- [ ] Documentation updated when behavior changes:
      `README.md`, `API.md`, or a new `docs/ADR/` entry.
- [ ] Security impact statement in the PR body (say "none" explicitly if
      the change is unrelated to auth/TLS/crypto/path handling).

## Code conventions

- **Python 3.10+** syntax — use `X | None`, not `Optional[X]`.
- **Type hints on everything** that is not a test fixture. `mypy --strict`
  is enforced on `src/`.
- **Paths:** always `pathlib.Path`; compare with `Path.resolve().relative_to()`
  for any user-supplied component (see ADR-004).
- **Randomness:** use `secrets` for anything security-adjacent, `random`
  for nothing in `src/`.
- **Logger:** `logging.getLogger("httpserver")`. Log what a reader needs to
  investigate a failure — include the request ID when available.
- **Error responses:** JSON body `{"error": "...", "status": NNN}`.
- **English** in user-facing strings (logs, CLI `--help`, response bodies).
  Source-code comments may be in any language the team can read.

## Adding a new HTTP method

1. Create a mixin in `src/handlers/` that inherits `BaseHandler`, or extend
   an existing mixin whose scope already covers the new method.
2. Define `def handle_<name>(self, request: HTTPRequest) -> HTTPResponse`.
3. Register the method with the registry in `ExperimentalHTTPServer.__init__`:
   `self.method_handlers.register("<NAME>", self.handle_<name>)`.
4. If the mixin is new, add it to the composition in
   `src/handlers/__init__.py`.
5. Document the method in `API.md` and, if it has non-trivial semantics,
   add a short ADR in `docs/ADR/`.
6. Tests:
   - Unit tests in `tests/test_handlers/test_<mixin>.py`
   - Integration scenarios in `tests/test_handlers/test_handler_integration.py`
     if the method interacts with sockets, auth, or OPSEC mode.

## Reporting security issues

**Do not open a public issue.** See `SECURITY.md` for the private
disclosure process.

## Questions

Open a draft PR or issue — happy to discuss design before code.
