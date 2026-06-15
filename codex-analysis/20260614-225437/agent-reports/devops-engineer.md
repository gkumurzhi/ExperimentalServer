# devops-engineer Report
_Generated: 2026-06-15 00:16:17 Europe/Moscow_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/analysis-plan.md_

## Summary

Subagent execution note: I attempted to run a read-only `devops-engineer` Codex subprocess, but its internal sandbox failed before repo reads. I completed the DevOps pass in this main session with read-only commands and did not modify files.

Operational boundary analyzed: GitHub Actions CI/security/release control plane, Python package artifact path, docs mirror path, dependency constraints, and Docker/example runtime path.

Confirmed direction: keep PyPI/GHCR publishing strategic for now. The immediate safety gap is not "no publish"; it is that the release lane treats 30-day GitHub Actions artifacts as artifacts of record while docs describe rollback from prior verified artifacts.

## Documentation Checks

No fresh Context7 lookup was needed; the recommendations rely on repo evidence and the parent plan's Docker/Python checks at [analysis-plan.md](/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/analysis-plan.md:67).

Read-only validation performed:

- `python tools/sync_docs.py --check` fails for `API.md -> docs/api.md` and `CONTRIBUTING.md -> docs/contributing.md`.
- `python tools/check_stale_docs.py` passes.
- Non-writing mirror comparison found first drift at generated `docs/api.md` line 57 and `docs/contributing.md` line 123.

## Detailed Findings

Control plane: CI runs Python 3.10-3.13, docs, cross-platform smoke, release smoke, browser smoke, and Docker smoke in [ci.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/.github/workflows/ci.yml:26), [ci.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/.github/workflows/ci.yml:95), and [ci.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/.github/workflows/ci.yml:199). Security runs pip-audit and Bandit on push/PR plus weekly schedule in [security.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/.github/workflows/security.yml:8). Dependabot covers pip, GitHub Actions, Docker, and pre-commit weekly in [dependabot.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/.github/dependabot.yml:3).

Dependency edge: `constraints/ci.txt` is fully pinned and documented as the committed dependency authority in [README.md](/home/user/PycharmProjects/ExperimentalHTTPServer/README.md:913). The constraints checker verifies installed distributions match pins in [check_dependency_constraints.py](/home/user/PycharmProjects/ExperimentalHTTPServer/tools/check_dependency_constraints.py:57).

Release path: release builds wheel/sdist, wheel-smokes outside source tree, browser-smokes installed package, audits pinned constraints, creates SBOM, attests wheel/sdist/SBOM, and uploads artifacts in [release.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/.github/workflows/release.yml:51) and [release.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/.github/workflows/release.yml:112). It intentionally does not publish, per [CONTRIBUTING.md](/home/user/PycharmProjects/ExperimentalHTTPServer/CONTRIBUTING.md:113).

Data plane/runtime: Docker uses pinned `python:3.12-slim` digest, non-root runtime user, and healthcheck in [Dockerfile](/home/user/PycharmProjects/ExperimentalHTTPServer/Dockerfile:7), [Dockerfile](/home/user/PycharmProjects/ExperimentalHTTPServer/Dockerfile:56), and [Dockerfile](/home/user/PycharmProjects/ExperimentalHTTPServer/Dockerfile:61). Root `docker-compose.yml` is absent; the compose file is actually [examples/docker/docker-compose.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/examples/docker/docker-compose.yml:1), with loopback publication by default at line 32.

Python policy: package metadata caps support at `>=3.10,<3.14` in [pyproject.toml](/home/user/PycharmProjects/ExperimentalHTTPServer/pyproject.toml:11), CI matches 3.10-3.13 in [ci.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/.github/workflows/ci.yml:26), and docs say the cap remains until CI tests 3.14 in [CONTRIBUTING.md](/home/user/PycharmProjects/ExperimentalHTTPServer/CONTRIBUTING.md:33).

## Issues Found

1. Medium: release rollback evidence expires too quickly. `upload-artifact` retention is 30 days in [release.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/.github/workflows/release.yml:158), but docs say rollback uses previous verified wheel/sdist from release artifacts in [CONTRIBUTING.md](/home/user/PycharmProjects/ExperimentalHTTPServer/CONTRIBUTING.md:129).

2. Medium: docs drift is already present and only guaranteed at CI time. Mirrors are defined in [sync_docs.py](/home/user/PycharmProjects/ExperimentalHTTPServer/tools/sync_docs.py:23), CI checks them in [ci.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/.github/workflows/ci.yml:95), but pre-commit local hooks only cover static UI/browser syntax after [pre-commit-config.yaml](/home/user/PycharmProjects/ExperimentalHTTPServer/.pre-commit-config.yaml:33).

3. Medium if container distribution expands: raw image default is broad. Code default is `lab` in [features.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/features.py:23), `lab` enables experimental/destructive surfaces in [features.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/features.py:89), and Dockerfile default command does not set profile/auth/TLS in [Dockerfile](/home/user/PycharmProjects/ExperimentalHTTPServer/Dockerfile:66).

4. Low now, higher if publishing: GitHub Actions use major-version action tags rather than immutable SHAs, e.g. [release.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/.github/workflows/release.yml:27). Dependabot mitigates update visibility, but published release automation would need stronger pinning.

## Concrete Recommendations

Keep PyPI and GHCR manual/strategic for now. Do not add registry publishing until maintainer SLA, version policy, credentials/OIDC boundaries, artifact promotion, and rollback are explicit.

For tagged releases, either publish durable GitHub Release assets or increase artifact retention so "previous verified artifact" rollback remains real. GitHub Releases are the smallest publishing step if the project wants durable artifact-of-record storage without PyPI/GHCR.

Keep Python support tied to CI: no metadata widening until the interpreter is in the CI matrix; announce any 3.10/3.11 removal one release ahead with a dated deprecation note.

Catch docs drift earlier by adding local pre-commit hooks for `python tools/sync_docs.py --check` and `python tools/check_stale_docs.py`, scoped to root docs, docs mirrors, and the docs tools.

## Quick Wins

- Regenerate the drifted mirrors in an implementation pass, then rerun `sync_docs --check`.
- Add docs-sync and stale-doc hooks to `.pre-commit-config.yaml`.
- Make Docker examples explicitly pass `--profile workspace` or `--profile serve`.
- Increase release artifact retention or create GitHub Release assets for tag builds.

## Deeper Improvements

- Add a release environment/promotion gate before PyPI or GHCR.
- If GHCR becomes real, add image build, scan, SBOM/provenance, digest output, and digest rollback.
- Pin release-critical GitHub Actions to SHAs when external publishing starts.
- Add Python 3.14 readiness as a separate stage before changing `requires-python`.

## Open Questions

- Should GitHub Releases become the durable artifact-of-record now, or should artifacts remain private/manual?
- Is Docker a supported distribution surface or only a local example?
- What exact date/release should start Python 3.10 deprecation?
- Should the container default diverge from CLI compatibility and use `workspace`/`serve` first?
