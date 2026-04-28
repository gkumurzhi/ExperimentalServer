# dependency-manager Report
_Generated: 2026-04-28 12:42:37 MSK_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/analysis-plan.md_

## Summary

Read-only analysis only. I inspected the requested dependency/workflow boundary: `pyproject.toml`, `constraints/ci.txt`, `uv.lock` version signals, `.pre-commit-config.yaml`, `.github/dependabot.yml`, `Dockerfile`, and `.github/workflows/{ci,security}.yml`.

Primary finding: dependency authority is split across broad `pyproject.toml` lower bounds, pip constraints, an untracked `uv.lock`, and independent pre-commit hook pins. That creates local/CI drift and weakens reproducibility.

## Documentation Checks

- Checked GitHub Dependabot supported ecosystems docs: `pip`, `pre-commit`, `uv`, `docker`, and `github-actions` are supported ecosystems; pip supports `.txt` and PEP 621 `pyproject.toml`; pre-commit hook revisions can be updated by Dependabot. Source: https://docs.github.com/en/code-security/reference/supply-chain-security/supported-ecosystems-and-repositories
- Checked Python.org Python 3.14 release page: Python 3.14.0 was a stable release on October 7, 2025. Source: https://www.python.org/downloads/release/python-3140/
- Context7 was not used; this was platform/package-manager documentation, checked directly against official docs.

## Issues Found

### MEDIUM: Multiple Dependency Authorities Are Drifting

Evidence:
- CI and Docker use `PIP_CONSTRAINT=constraints/ci.txt`: `.github/workflows/ci.yml:9`, `.github/workflows/security.yml:11`, `Dockerfile:22`, `Dockerfile:45`.
- `uv.lock` exists but is untracked: `git status` showed `?? uv.lock`.
- `uv.lock` has its own resolver state: `uv.lock:1-7`.
- Static comparison found mismatches including `cryptography` `46.0.5` in `constraints/ci.txt:16` vs `47.0.0` in `uv.lock:378`, `ruff` `0.15.5` in `constraints/ci.txt:64` vs `0.15.12` in `uv.lock:1183`, and `pytest` `9.0.2` in `constraints/ci.txt:56` vs `9.0.3` in `uv.lock:1022`.

Confidence: High.

Impact: A developer using `uv sync` can test a materially different toolchain from CI/Docker.

### MEDIUM: CI Installs `dev`, Which Pulls Unpinned Pre-commit Tooling

Evidence:
- `dev` includes `pre-commit>=4.0`: `pyproject.toml:49-53`.
- CI installs `.[crypto,dev,lint,test]`: `.github/workflows/ci.yml:37-40`, `.github/workflows/ci.yml:148-151`.
- `constraints/ci.txt` does not pin `pre-commit`; `uv.lock` shows `pre-commit==4.6.0` and transitives like `cfgv`, `identify`, `nodeenv`, `virtualenv`: `uv.lock:124`, `uv.lock:548`, `uv.lock:911`, `uv.lock:965`, `uv.lock:1297`.

Confidence: High.

Impact: The “pinned CI toolchain” comment in `constraints/ci.txt:1-2` is not fully true for CI installs using `dev`.

### MEDIUM: Pre-commit Hook Pins Lag CI Tool Pins

Evidence:
- Pre-commit uses `ruff-pre-commit` `v0.9.0`: `.pre-commit-config.yaml:14-19`.
- CI constraints pin `ruff==0.15.5`: `constraints/ci.txt:64`.
- Pre-commit uses `mypy` `v1.14.0`: `.pre-commit-config.yaml:21-28`.
- CI constraints pin `mypy==1.20.1`: `constraints/ci.txt:37`.

Confidence: High.

Impact: Local pre-commit can pass while CI fails, or auto-fix code differently than CI’s formatter/linter.

### MEDIUM: Dependabot Coverage Misses Active Dependency Surfaces

Evidence:
- Config only includes `pip` and `github-actions`: `.github/dependabot.yml:3-23`.
- Repo also has `.pre-commit-config.yaml`, `Dockerfile`, and `uv.lock` signals.
- Official GitHub docs list supported ecosystems for `pre-commit`, `docker`, and `uv`.

Confidence: High.

Impact: Hook revisions, Docker base image digest/tag policy, and a future promoted `uv.lock` will not be updated by current Dependabot config.

### MEDIUM: Python Support Policy Allows More Than CI Tests

Evidence:
- Package metadata allows all Python versions `>=3.10`: `pyproject.toml:11`.
- Classifiers stop at Python 3.13: `pyproject.toml:29-32`.
- CI matrix tests `3.10` through `3.13`: `.github/workflows/ci.yml:22-23`.
- Python 3.14 is stable per Python.org, but not in the matrix.
- `uv.lock` already contains resolution markers split around Python 3.15: `uv.lock:4-7`.

Confidence: High.

Impact: Users on Python 3.14 are allowed by metadata but not covered by CI.

### LOW: Security Audit Omits Docs Extra

Evidence:
- Docs job installs `.[docs,lint]`: `.github/workflows/ci.yml:77-80`.
- Security audit installs `.[crypto,dev,lint,test]`: `.github/workflows/security.yml:29-36`.
- Docs dependencies are pinned in constraints, e.g. `mkdocs` and `mkdocs-material`: `constraints/ci.txt:32-34`.

Confidence: High.

Impact: Vulnerabilities in docs build dependencies may not be caught by the scheduled `pip-audit` job.

### LOW: `all` Extra Uses a Self-reference

Evidence:
- `all = ["exphttp[crypto,dev,lint,test,docs]"]`: `pyproject.toml:67-69`.
- Lock metadata records the self-reference: `uv.lock:497-511`.

Confidence: Medium.

Impact: Usually resolvable, but it adds an avoidable recursive edge for dependency tools.

## Recommendations

1. Pick one reproducibility authority.
   - Smallest safe path: keep `constraints/ci.txt` authoritative and do not commit/promote `uv.lock` until CI uses `uv sync --frozen`.
   - If adopting uv: commit `uv.lock`, switch CI/Docker install paths to uv, add Dependabot `package-ecosystem: uv`, and retire or clearly demote `constraints/ci.txt`.

2. Split CI extras from local developer extras.
   - Move `pytest`, `pytest-cov`, and benchmark/test dependencies into `test`.
   - Keep `pre-commit` in a separate `precommit` or `dev` extra.
   - Then CI can install `.[crypto,lint,test]` without bringing pre-commit’s virtualenv toolchain.

3. Align pre-commit with CI.
   - Update pre-commit `ruff` and `mypy` hook revs to match the constrained versions, or add Dependabot `pre-commit` updates and accept automated drift management.

4. Expand Dependabot coverage.
   - Add `pre-commit`.
   - Add `docker` for the Dockerfile base image workflow.
   - Add `uv` only if `uv.lock` becomes part of the committed workflow.

5. Clarify Python support.
   - Add Python 3.14 to CI and classifiers if supported.
   - If not supported, document that explicitly; avoid claiming broad `>=3.10` support without test coverage.

6. Audit the full pinned graph.
   - Prefer `pip-audit -r constraints/ci.txt` or install all extras including docs in the audit job.

## Quick Wins

- Add Dependabot `pre-commit` entry.
- Update `.pre-commit-config.yaml` ruff/mypy revs to match CI constraints.
- Add Python `3.14` to the CI matrix as an allowed-failure first, then promote after passing.
- Decide whether `uv.lock` is experimental local state or a committed install authority.

## Open Questions

- Is `uv.lock` intended to be committed and used, or is `constraints/ci.txt` the intended source of truth?
- Should Python 3.14 be officially supported now that 3.14 is stable?
- Is pre-commit meant to be installed in CI, or only used locally?
- Do you want Docker base digest updates handled by Dependabot, or intentionally manual because of release-risk control?
