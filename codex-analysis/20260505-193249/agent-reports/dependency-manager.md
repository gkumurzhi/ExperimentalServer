# dependency-manager Report
_Generated: 2026-05-05 20:05:00 Europe/Moscow_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260505-193249/analysis-plan.md_

## Summary

Read-only dependency-manager pass completed for `/home/user/PycharmProjects/ExperimentalHTTPServer`. No files were written.

Boundary analyzed: Python package metadata, `constraints/ci.txt`, pre-commit isolated hook deps, CI/security/Docker install paths, Dependabot coverage, and docs/error messaging around the new default `acme`/`cryptography` runtime policy.

Primary friction source: the committed dependency policy is mostly coherent, but local developer workflows can diverge because pre-commit mypy owns a separate dependency environment and the current local interpreter is stale.

## Documentation Checks

Context7 was queried for Dependabot behavior but did not conclusively answer the manifest-discovery edge. I checked GitHub's current Dependabot docs instead: pip updates support `.txt` files and PEP 621 `pyproject.toml`; pre-commit updates can include `additional_dependencies`; `directory: "/"` scans files/directories under that directory unless excluded. Sources:
- https://docs.github.com/en/code-security/dependabot/ecosystems-supported-by-dependabot/supported-ecosystems-and-repositories
- https://docs.github.com/en/code-security/dependabot/working-with-dependabot/dependabot-options-reference

## Detailed Findings

`constraints/ci.txt` is consistent with declared direct bounds. `acme>=5.5,<6` and `cryptography>=48.0` in [pyproject.toml](/home/user/PycharmProjects/ExperimentalHTTPServer/pyproject.toml:37) are pinned as `acme==5.5.0` and `cryptography==48.0.0` in [constraints/ci.txt](/home/user/PycharmProjects/ExperimentalHTTPServer/constraints/ci.txt:4). A read-only metadata check found all declared runtime/dev/lint/test/docs deps present in constraints, all direct pins inside declared specifiers, and no duplicate constraint entries.

CI and Docker mostly use the constraints correctly. CI exports `PIP_CONSTRAINT=constraints/ci.txt` globally and installs under that constraint in test/docs/cross-platform/smoke jobs in [.github/workflows/ci.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/.github/workflows/ci.yml:9). Docker builds and installs the wheel with the same constraint file in [Dockerfile](/home/user/PycharmProjects/ExperimentalHTTPServer/Dockerfile:20) and [Dockerfile](/home/user/PycharmProjects/ExperimentalHTTPServer/Dockerfile:47).

Security scanning covers the pinned Python graph. The security workflow installs `pip-audit` under the shared constraint and audits `constraints/ci.txt` with `--strict` in [.github/workflows/security.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/.github/workflows/security.yml:29). It also runs Bandit over `src` in [.github/workflows/security.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/.github/workflows/security.yml:51). I did not run `pip-audit` locally because the current env lacks the tool and this pass was read-only.

Dependabot coverage is adequate in shape. It has weekly `pip`, `github-actions`, `docker`, and `pre-commit` entries in [.github/dependabot.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/.github/dependabot.yml:3). Given GitHub's docs, the root pip updater should see both `pyproject.toml` and `constraints/ci.txt`; the pre-commit updater can update hook `additional_dependencies`.

## Issues Found

- [MEDIUM] Pre-commit mypy dependency environment is inconsistent with runtime policy.
  - File/area: `.pre-commit-config.yaml`, `pyproject.toml`, `constraints/ci.txt`
  - Evidence: `pyproject.toml` requires `cryptography>=48.0`, but the mypy hook pins `cryptography==46.0.5` and lacks explicit `acme`, `josepy`, and `PyOpenSSL` pins in [.pre-commit-config.yaml](/home/user/PycharmProjects/ExperimentalHTTPServer/.pre-commit-config.yaml:21).
  - Detail: Pre-commit does not automatically reuse the project venv or `PIP_CONSTRAINT`, so the hook dependency graph diverges from runtime.
  - Impact: Local developer checks can fail differently from CI or miss dependency-related import/type failures.
  - Confidence: high

- [MEDIUM] Local normal CLI path currently fails in this workspace.
  - File/area: local environment, `src/security/tls.py`
  - Evidence: Read-only import checks show `acme` and `josepy` missing, `cryptography==41.0.7`, and `python -m src --help` fails at `from acme import ...` in [src/security/tls.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/security/tls.py:25).
  - Detail: This is environment drift, but it blocks normal local verification until the package is reinstalled.
  - Impact: Developers cannot run basic CLI smoke locally without refreshing the environment.
  - Confidence: high

- [LOW/MEDIUM] Empty `[crypto]` extra is technically compatible but user-facing text is stale.
  - File/area: `pyproject.toml`, `docs/ADR/ADR-003-cryptography-optional.md`, runtime/UI strings
  - Evidence: `[crypto]` is intentionally empty in [pyproject.toml](/home/user/PycharmProjects/ExperimentalHTTPServer/pyproject.toml:49), matching ADR-003 in [docs/ADR/ADR-003-cryptography-optional.md](/home/user/PycharmProjects/ExperimentalHTTPServer/docs/ADR/ADR-003-cryptography-optional.md:23). Runtime/UI errors still say to install `exphttp[crypto]` in [src/request_pipeline.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/request_pipeline.py:208), [src/handlers/notepad.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/notepad.py:38), and [src/data/static/ui/core.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/core.js:552).
  - Detail: The extra remains useful for backward-compatible install commands but no longer remediates broken installs.
  - Impact: Users get a no-op recovery instruction for missing runtime crypto.
  - Confidence: high

- [LOW] Docs are mostly updated but README still has the old zero-dependency claim.
  - File/area: `README.md`
  - Evidence: [README.md](/home/user/PycharmProjects/ExperimentalHTTPServer/README.md:11) still says pure Python with no external dependencies, while [README.md](/home/user/PycharmProjects/ExperimentalHTTPServer/README.md:56) correctly lists runtime deps.
  - Detail: This is high-visibility dependency policy drift.
  - Impact: Users and maintainers may assume install/runtime properties that are no longer true.
  - Confidence: high

## Concrete Recommendations

Smallest safe change: align the pre-commit mypy hook with the pinned runtime graph by replacing `cryptography==46.0.5` with `cryptography==48.0.0` and adding explicit pins for the imported ACME stack, at least `acme==5.5.0`, `josepy==2.2.0`, and `PyOpenSSL==26.2.0`. Tradeoff: duplicates a small subset of `constraints/ci.txt`, but keeps the isolated pre-commit environment deterministic.

Keep `[crypto]` empty for compatibility, but change user-facing guidance from "install `exphttp[crypto]`" to "reinstall or repair the default `exphttp` environment; cryptography is a runtime dependency." This preserves old install commands without implying the extra fixes anything.

Add a lightweight dependency validation step after constrained installs: `python -m pip check`, `python -m src --help`, and a TLS/ACME import smoke. This catches the local failure path before deeper tests.

## Quick Wins

- Update pre-commit mypy `additional_dependencies`.
- Remove or reword stale `exphttp[crypto]` runtime/UI messages.
- Fix the README line 11 zero-dependency claim.
- Run `PIP_CONSTRAINT=constraints/ci.txt pip install -e ".[crypto,dev,lint,test]"` in a clean local venv before promoting the current dirty dependency changes.

## Deeper Improvements

- Add a lock refresh checklist or script that regenerates `constraints/ci.txt`, runs Python 3.10-3.13 install smoke, `pip check`, mypy, pytest, Docker smoke, and `pip-audit --strict -r constraints/ci.txt`.
- Consider a license/SBOM step for releases. `pip-audit` covers vulnerability exposure, not distribution license review, and ADR-003 explicitly expands the OpenSSL-backed dependency surface.
- If live ACME is release-critical, add a manual gated integration checklist for routable HTTP-01 issuance; current dependency scans and mock tests do not validate CA reachability.

## Open Questions

- Should pre-commit remain isolated with duplicated pins, or should the project switch mypy to a local/system hook that uses the constrained developer venv?
- Is `[crypto]` meant to stay indefinitely as a compatibility extra, or should docs mark it as deprecated for a future major release?
- Do releases need formal license/SBOM artifacts now that `acme`, `cryptography`, `josepy`, and `PyOpenSSL` are default runtime dependencies?
