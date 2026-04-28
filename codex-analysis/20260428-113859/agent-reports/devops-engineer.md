# devops-engineer Report
_Generated: 2026-04-28 12:48:10 MSK_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/analysis-plan.md_

## Summary

**Operational boundary analyzed:** GitHub Actions CI/security control plane, Dependabot dependency-update path, pip/constraints/uv dependency resolution path, pre-commit local gate, and docs mirror check path for `/home/user/PycharmProjects/ExperimentalHTTPServer`. I did not inspect `notes/`, `uploads/`, `.env*`, keys, certs, or credential-like files.

**Confirmed facts:** current worktree is dirty; `.github/workflows/ci.yml` and `pyproject.toml` have uncommitted changes, and `uv.lock` is untracked. `tools/sync_docs.py --check` passed in read-only mode with `PYTHONDONTWRITEBYTECODE=1`.

**Main risks:** CI has competing dependency-policy signals (`constraints/ci.txt` vs untracked `uv.lock`), local pre-commit tool versions drift from CI, `pip-audit --disable-pip` is likely invalid for the current invocation, and the browser smoke path resolves Playwright dynamically through unpinned `npx`.

## Documentation Checks

Context7 was checked for `uv` documentation, but it was quota-limited: “Monthly quota reached.” I used only official docs as fallback.

Checked official documentation:

- GitHub Dependabot supported ecosystems, including `pip`, `pre-commit`, and `uv`: https://docs.github.com/en/code-security/dependabot/ecosystems-supported-by-dependabot/supported-ecosystems-and-repositories
- GitHub Actions hardening guidance for least-privilege `GITHUB_TOKEN` and pinning actions to full-length SHAs: https://docs.github.com/en/actions/how-tos/security-for-github-actions/security-guides/security-hardening-for-github-actions
- uv lock/sync behavior including lockfile checks and frozen/locked installs: https://docs.astral.sh/uv/concepts/projects/sync/
- pip constraints behavior: constraints constrain resolution but do not themselves trigger package installation: https://pip.pypa.io/en/stable/user_guide/
- pip-audit README for `--disable-pip` restrictions: https://github.com/pypa/pip-audit
- pre-commit docs for hook `rev` management/autoupdate: https://pre-commit.com/

## Issues Found

| Severity | Issue | Evidence | Confidence |
|---|---|---|---|
| HIGH | `pip-audit` security job likely fails before auditing, or is configured against the wrong mode. `--disable-pip` is documented for hashed/no-deps resolution paths, but this workflow audits the installed environment. | [security.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/.github/workflows/security.yml:35) runs `pip-audit --strict --disable-pip`; install step is environment-based at [security.yml:29](/home/user/PycharmProjects/ExperimentalHTTPServer/.github/workflows/security.yml:29). | High |
| MEDIUM | Dependency source of truth is split. CI uses `PIP_CONSTRAINT=constraints/ci.txt`, while an untracked `uv.lock` exists with different versions and is not part of CI cache/install inputs. | [ci.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/.github/workflows/ci.yml:9), [constraints/ci.txt](/home/user/PycharmProjects/ExperimentalHTTPServer/constraints/ci.txt:1), untracked `uv.lock`; examples: constraints `cryptography==46.0.5` at [constraints/ci.txt:16](/home/user/PycharmProjects/ExperimentalHTTPServer/constraints/ci.txt:16), lock has `cryptography 47.0.0` at `uv.lock:377`. | High |
| MEDIUM | `pre-commit` is now a dev dependency but is not pinned in `constraints/ci.txt`, so “pinned CI/local resolution” is incomplete. | `pre-commit>=4.0` at [pyproject.toml](/home/user/PycharmProjects/ExperimentalHTTPServer/pyproject.toml:53); no `pre-commit==...` in [constraints/ci.txt](/home/user/PycharmProjects/ExperimentalHTTPServer/constraints/ci.txt:1). pip docs confirm constraints do not install missing packages by themselves. | High |
| MEDIUM | Local pre-commit hooks drift from CI tool versions. This can make local fixes/checks disagree with GitHub Actions. | CI constraints pin `mypy==1.20.1` and `ruff==0.15.5` at [constraints/ci.txt:37](/home/user/PycharmProjects/ExperimentalHTTPServer/constraints/ci.txt:37), [constraints/ci.txt:64](/home/user/PycharmProjects/ExperimentalHTTPServer/constraints/ci.txt:64); pre-commit uses `ruff-pre-commit v0.9.0` and `mypy v1.14.0` at [.pre-commit-config.yaml](/home/user/PycharmProjects/ExperimentalHTTPServer/.pre-commit-config.yaml:15), [.pre-commit-config.yaml:22](/home/user/PycharmProjects/ExperimentalHTTPServer/.pre-commit-config.yaml:22). | High |
| MEDIUM | Browser smoke has an unpinned external package edge. `npx --yes playwright install` can pull a different Playwright CLI over time; no `package.json` or JS lockfile is tracked. | [ci.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/.github/workflows/ci.yml:143) and [ci.yml:153](/home/user/PycharmProjects/ExperimentalHTTPServer/.github/workflows/ci.yml:153); `git ls-files package.json package-lock.json pnpm-lock.yaml yarn.lock` returned none. | High |
| LOW | Workflows do not set explicit least-privilege permissions and actions are pinned only to major tags. This is not a current functional failure, but weakens supply-chain reproducibility and token-boundary clarity. | No `permissions:` in `.github/workflows/*.yml`; actions use `@v4`/`@v5` tags such as [ci.yml:26](/home/user/PycharmProjects/ExperimentalHTTPServer/.github/workflows/ci.yml:26) and [security.yml:19](/home/user/PycharmProjects/ExperimentalHTTPServer/.github/workflows/security.yml:19). | Medium |
| LOW | Coverage artifact upload does not fail explicitly if `coverage.xml` is missing. | [ci.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/.github/workflows/ci.yml:54) uploads `coverage.xml` without `if-no-files-found: error`. | Medium |

## Recommendations

1. Fix `pip-audit` first. Smallest safe change: remove `--disable-pip` from [security.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/.github/workflows/security.yml:36). Rollback is a one-line revert; failure mode becomes observable as a normal audit failure instead of configuration failure.

2. Pick one Python lock policy. Smallest current-policy option: keep `constraints/ci.txt` as CI truth, pin `pre-commit` and its required transitive packages there, and do not commit `uv.lock` yet. If adopting uv, commit `uv.lock`, switch CI to `uv sync --locked`, add `uv lock --check`, and add Dependabot `package-ecosystem: uv`.

3. Align pre-commit with CI. Bump hook revs to the same ruff/mypy generation as CI, or document pre-commit as a convenience fixer rather than a CI mirror.

4. Pin the browser smoke dependency edge. Either add a tiny JS lockfile for Playwright or use an explicit version such as `npx --yes playwright@<pinned> install --with-deps chromium`.

5. Add top-level workflow permissions:

```yaml
permissions:
  contents: read
```

6. Add artifact guardrails:

```yaml
if-no-files-found: error
retention-days: 7
```

## Quick Wins

- Remove `--disable-pip` from the `pip-audit` command.
- Add `permissions: contents: read` to both workflows.
- Add `if-no-files-found: error` to the coverage upload.
- Add Dependabot entry for `pre-commit` if hook revs should stay maintained automatically.
- Decide whether `uv.lock` is intentionally local-only or intended to become the CI lockfile.

## Open Questions

- Is `uv.lock` intended to replace `constraints/ci.txt`, or is it local experimentation?
- Should security auditing cover docs tooling too? Current `pip-audit` install excludes `[docs]`, while the docs job installs docs dependencies.
- Are GitHub Actions default token permissions already restricted at the repository/org level, or should the workflows declare that boundary explicitly?
- Should browser smoke be considered a release gate? If yes, the Playwright install path should be pinned before relying on it for promotion.
