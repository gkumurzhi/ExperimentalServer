# dependency-manager Report
_Generated: 2026-06-15 00:08:08 Europe/Moscow_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/analysis-plan.md_

## Summary

Read-only dependency workflow reviewed: package metadata, constraints authority, ignored local `uv.lock`, CI/security/release dependency installs, Dependabot cadence, and Docker dependency path.

Primary friction: Python support policy is stale. The package caps support at `>=3.10,<3.14` in [pyproject.toml](/home/user/PycharmProjects/ExperimentalHTTPServer/pyproject.toml:11), CI tests only 3.10-3.13 in [ci.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/.github/workflows/ci.yml:26), while parent preflight records Python 3.14 as already released/current enough to require a decision in [preflight.md](/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/preflight.md:20).

Smallest safe plan: add Python 3.14 to the constrained CI matrix first. If install, tests, `pip check`, import smoke, security audit, and Docker smoke pass, update metadata/docs to `>=3.10,<3.15` and add the 3.14 classifier. Do not drop 3.10 in the same change.

## Documentation Checks

Read: source plan, product-manager and QA reports, `pyproject.toml`, `constraints/ci.txt`, local `uv.lock`, `.github/dependabot.yml`, `.github/workflows/security.yml`, `.github/workflows/ci.yml`, `.github/workflows/release.yml`, `Dockerfile`, README/CONTRIBUTING dependency guidance, and ADR-003.

I did not re-run Context7. The parent plan already records current checks for cryptography, Docker, and Python release status in [analysis-plan.md](/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/analysis-plan.md:67).

I did check the official Python Developer's Guide status page for deprecation timing: Python 3.14 is in bugfix support through 2030-10, Python 3.10 reaches EOL in 2026-10, and Python 3.11 reaches EOL in 2027-10. Source: https://devguide.python.org/versions/

## Detailed Findings

Runtime dependencies are intentionally small and direct: `acme>=5.5,<6`, `cryptography>=48.0`, and `josepy>=2.2,<3` in [pyproject.toml](/home/user/PycharmProjects/ExperimentalHTTPServer/pyproject.toml:37). Constraints pin these to `acme==5.5.0`, `cryptography==48.0.0`, `josepy==2.2.0`, and `PyOpenSSL==26.2.0` in [constraints/ci.txt](/home/user/PycharmProjects/ExperimentalHTTPServer/constraints/ci.txt:4).

The empty `crypto` extra is not a bug. ADR-003 says crypto/ACME moved into the default runtime and `[crypto]` remains as a compatibility extra in [ADR-003](/home/user/PycharmProjects/ExperimentalHTTPServer/docs/ADR/ADR-003-cryptography-optional.md:17).

Constraints are the real reproducibility boundary. README and CONTRIBUTING both say `constraints/ci.txt` is the only committed dependency authority and local `uv.lock` should not be committed in [README.md](/home/user/PycharmProjects/ExperimentalHTTPServer/README.md:913) and [CONTRIBUTING.md](/home/user/PycharmProjects/ExperimentalHTTPServer/CONTRIBUTING.md:28). `.gitignore` ignores `uv.lock` in [.gitignore](/home/user/PycharmProjects/ExperimentalHTTPServer/.gitignore:35), and `git ls-files --stage uv.lock` returned no tracked entry.

The local ignored `uv.lock` is nevertheless drifted: it has `acme==5.6.0` while constraints pin `5.5.0` in [uv.lock](/home/user/PycharmProjects/ExperimentalHTTPServer/uv.lock:6); it also has newer local pins for `mypy`, `ruff`, `requests`, `certifi`, `pytest-cov`, and `hypothesis`. This does not affect CI, but it is analyst/developer friction.

Security cadence is basically sound: Dependabot runs weekly for pip, actions, Docker, and pre-commit in [.github/dependabot.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/.github/dependabot.yml:3), and security workflow runs `pip-audit --strict --no-deps -r constraints/ci.txt` in [security.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/.github/workflows/security.yml:45). Release also audits constraints and generates CycloneDX SBOM in [release.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/.github/workflows/release.yml:112).

Docker is aligned with the current constrained dependency path: it builds and installs with `PIP_CONSTRAINT=/.../constraints/ci.txt` in [Dockerfile](/home/user/PycharmProjects/ExperimentalHTTPServer/Dockerfile:20) and uses pinned `python:3.12-slim` digest in [Dockerfile](/home/user/PycharmProjects/ExperimentalHTTPServer/Dockerfile:7). It is not yet aligned to a future 3.14 support story.

Validation performed: parsed `pyproject.toml`, constraints, and local `uv.lock`; confirmed Python runtime is 3.12.3 locally; confirmed `pip_audit` is not installed locally; ran the constraints completeness guard and it failed in the ambient environment because unrelated user/system packages are installed. That failure confirms the guard belongs in a clean constrained environment, as CI does.

## Issues Found

P1: Python 3.14 is blocked by metadata and CI policy, not by an evidenced dependency failure. The cap is in [pyproject.toml](/home/user/PycharmProjects/ExperimentalHTTPServer/pyproject.toml:11), and docs explicitly say `<3.14` remains until CI tests it in [README.md](/home/user/PycharmProjects/ExperimentalHTTPServer/README.md:919).

P2: Local ignored `uv.lock` drift can mislead dependency analysis. It is ignored by policy, but present and newer than constraints for several packages.

P2: CI is strongly pinned, but there is no floating runtime smoke for unconstrained user installs. That matters because `cryptography>=48.0` has no upper bound in [pyproject.toml](/home/user/PycharmProjects/ExperimentalHTTPServer/pyproject.toml:39), while CI/release run against constraints.

P3: Docker image scanning/SBOM/provenance is intentionally absent from release artifacts. README documents that container image digest scan/SBOM/provenance are not configured until registry intent is chosen in [README.md](/home/user/PycharmProjects/ExperimentalHTTPServer/README.md:991).

## Concrete Recommendations

Immediate: add Python 3.14 to CI as a blocking matrix entry, still using `constraints/ci.txt`. After it passes, update `requires-python` to `>=3.10,<3.15`, add the 3.14 classifier, and update README/CONTRIBUTING badges and support text.

Deprecation horizon: announce Python 3.10 deprecation now and drop it after 2026-10 EOL, ideally in the first minor/major release after October 2026. Keep Python 3.11 through its 2027-10 EOL unless a hard dependency blocker appears.

Keep constraints as the committed authority. Do not promote `uv.lock` unless the project deliberately switches to uv as the source of truth and generates constraints from it.

Run ACME/crypto upgrades as small staged PRs, not mass upgrades: refresh constraints, run the full Python matrix, `pip check`, import smoke, TLS/ACME tests, `pip-audit`, release smoke, and Docker smoke. Prioritize security advisories over weekly routine bumps.

## Quick Wins

Remove the local ignored `uv.lock` from working copies used for analysis, or regenerate it only from current constraints when a developer explicitly needs uv locally.

Add a short Python support table to README/CONTRIBUTING: 3.10 supported until 2026-10, 3.11 until 2027-10, 3.14 pending CI promotion.

Make the 3.14 CI PR separate from any dependency refresh. That keeps rollback simple: revert metadata/matrix only if interpreter support fails.

## Deeper Improvements

Add a scheduled floating install smoke without `PIP_CONSTRAINT` for the latest stable Python. This catches future unconstrained `cryptography`/ACME breakage before users do.

If Docker becomes a distribution artifact, add image vulnerability scanning, image SBOM/provenance, registry digest rollback, and release-lane Docker smoke.

Consider hash-locked release constraints if supply-chain reproducibility becomes a stronger goal than current version-pin reproducibility.

Add Python 3.15 prerelease canary later in 2026, non-blocking until final release and dependency wheel support are stable.

## Open Questions

Should 3.14 support be promoted immediately after CI passes, or kept as a short canary period?

Is Docker a supported release artifact or only a CI/runtime convenience?

Should the project continue with constraints-only authority, or adopt uv as the actual lock source?

Does the project promise compatibility with unconstrained PyPI installs, or only with the pinned CI/release dependency set?
