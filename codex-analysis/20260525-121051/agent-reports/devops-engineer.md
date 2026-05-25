# devops-engineer Report
_Generated: 2026-05-25 12:41:13 MSK_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260525-121051/analysis-plan.md_

## Summary

Operational boundary analyzed: GitHub Actions CI/security workflows, dependency constraints, release artifact path, Docker image/runtime smoke path, browser smoke path, and example deployment secret/healthcheck boundaries.

The merge-time CI surface is solid for Python tests, lint, typing, docs, cross-platform smoke, package-data checks, browser smoke, Docker HTTP/TLS PING smoke, pip-audit, Bandit, and Dependabot. The main production-safety gap is after merge: there is no controlled release/publish workflow, no artifact-of-record, and no SBOM/provenance/attestation/signing path for Python or container artifacts.

## Documentation Checks

- **GitHub Actions** `unknown/current` - Context7 topic checked: artifact attestations, required workflow permissions, container/image attestations; impact on recommendation: release workflows should use explicit `contents: read`, `id-token: write`, `attestations: write`, plus `packages: write` only for image publication.
- **Python Packaging User Guide** `unknown/current` - Context7 topic checked: GitHub Actions publishing, trusted publishing, dist build/upload flow; impact on recommendation: prefer tag-gated build job plus PyPI trusted publishing over manual token uploads.
- **Docker** `current` - Context7 topic checked: SBOM/provenance attestations and Docker Scout verification; impact on recommendation: container release should build with SBOM/provenance and verify/scan the produced image digest.

## Detailed Findings

Confirmed facts:
- Only two workflows exist: `.github/workflows/ci.yml` and `.github/workflows/security.yml`.
- No release, publish, PyPI, TestPyPI, GHCR, SBOM, provenance, cosign, Sigstore, SLSA, Trivy, Grype, Docker Scout, or attestation workflow was found.
- CI coverage gate is exactly `--cov-fail-under=65` in `.github/workflows/ci.yml:62`.
- Docker healthcheck is plain unauthenticated HTTP `PING` in `Dockerfile:61-64`.
- Auth happens before dispatch, so authenticated deployments require credentials even for `PING`: `src/request_pipeline.py:124-127`.
- Browser smoke starts an in-process source-tree server via `sys.path.insert(0, str(REPO_ROOT))` and `from src.server import ExperimentalHTTPServer` in `tools/browser_smoke.py:18-21`.

Assumptions:
- Branch protection / required checks are not visible from repository files.
- Public release intent is inferred from `pyproject.toml`, README badges, SECURITY supported versions, Dockerfile, and release-smoke naming.

## Issues Found

- [MEDIUM] No controlled release, publish, SBOM, provenance, or attestation path
  - File/area: `.github/workflows/`, `.github/workflows/ci.yml`, `pyproject.toml`
  - Evidence: only `ci.yml` and `security.yml` exist; CI builds a temporary wheel at `.github/workflows/ci.yml:173-175`; only coverage is uploaded as an artifact at `.github/workflows/ci.yml:64-69`.
  - Detail: Merge gates are present, but there is no tag-gated build/publish workflow that produces Python dists or container images as release artifacts with provenance.
  - Impact: manual releases can bypass CI; consumers cannot verify that a wheel/image came from the reviewed commit.
  - Confidence: high

- [MEDIUM] Docker healthcheck and Docker smoke are not representative for auth/TLS/ACME modes
  - File/area: `Dockerfile`, `examples/docker/docker-compose.yml`, `.github/workflows/ci.yml`
  - Evidence: healthcheck probes `http://127.0.0.1:8080/` with `PING` at `Dockerfile:61-64`; Compose warns TLS/auth need override at `examples/docker/docker-compose.yml:27-28`; ACME disables healthcheck at `examples/docker/docker-compose.yml:96-99`; CI disables healthcheck for TLS smoke at `.github/workflows/ci.yml:235-243`.
  - Detail: Default HTTP mode is covered, but the operational modes recommended for exposure either fail the built-in healthcheck or disable it.
  - Impact: orchestrators can get false unhealthy signals, or no health signal at all, in the modes most likely to be deployed externally.
  - Confidence: high

- [MEDIUM] Release smoke does not exercise the exact built wheel or container UI runtime
  - File/area: `.github/workflows/ci.yml`, `tools/browser_smoke.py`, `tools/check_static_ui_assets.py`
  - Evidence: CI checks wheel UI files at `.github/workflows/ci.yml:173-175`; browser smoke then runs `python tools/browser_smoke.py` at `.github/workflows/ci.yml:191-194`; that script imports from the repo source tree at `tools/browser_smoke.py:18-21`; Docker smoke only checks version/import/PING at `.github/workflows/ci.yml:224-243`.
  - Detail: Package-data checks are useful, but the browser flow is not run from an installed wheel or container.
  - Impact: wheel entry point/resource regressions or container UI regressions can escape the release smoke.
  - Confidence: high

- [MEDIUM] Service credentials are still modeled as command-line arguments
  - File/area: `src/cli.py`, `README.md`, `examples/docker/docker-compose.yml`, `SECURITY.md`
  - Evidence: CLI accepts only `--auth CREDS` at `src/cli.py:171-177`; config passes `auth: args.auth` at `src/cli.py:264`; examples show `--auth admin:secretpassword` and `--auth admin:pass` at `README.md:192-199`; Compose example shows `admin:replace-with-a-strong-secret` at `examples/docker/docker-compose.yml:31-40`; SECURITY says use a secret manager at `SECURITY.md:90-93`.
  - Detail: The documented desired boundary is secret-manager sourced credentials, but the CLI/deployment interface still encourages argv/Compose-file secrets.
  - Impact: credentials can leak through shell history, process listings, Compose files, logs, or copied deployment snippets.
  - Confidence: high

- [LOW] Coverage gate is low and not reproduced by local contributor commands
  - File/area: `.github/workflows/ci.yml`, `CONTRIBUTING.md`
  - Evidence: CI uses `--cov-fail-under=65` at `.github/workflows/ci.yml:62`; local instructions run `pytest --cov=src --cov-report=term-missing` without fail-under at `CONTRIBUTING.md:102`; line `CONTRIBUTING.md:109` says “Coverage gate in CI is 65 %; aim higher.”
  - Detail: The gate is explicit but permissive for a security-adjacent server.
  - Impact: meaningful test loss can merge until the project falls to 65%.
  - Confidence: high

- [LOW] Constraint refresh and duplicated tool pins are only partly enforceable
  - File/area: `constraints/ci.txt`, `.pre-commit-config.yaml`, `.github/workflows/ci.yml`, `tools/browser_smoke.py`
  - Evidence: constraints policy is documented at `constraints/ci.txt:1-2`, `README.md:799-803`, and `CONTRIBUTING.md:28-31`; pre-commit separately pins ruff/mypy at `.pre-commit-config.yaml:15` and `.pre-commit-config.yaml:22`; Playwright CLI is duplicated at `.github/workflows/ci.yml:180` and `tools/browser_smoke.py:23`.
  - Detail: The constraints authority is good, but refresh/parity checks do not verify duplicated non-pip pins.
  - Impact: Dependabot or manual updates can make local hooks/browser smoke differ from CI behavior.
  - Confidence: medium

## Concrete Recommendations

1. Add a tag-gated release workflow before any public publish path:
   - build wheel and sdist from a clean checkout;
   - run existing static UI wheel check;
   - install the built wheel in a fresh venv and run CLI smoke plus browser smoke against that install;
   - upload dists as artifacts;
   - use PyPI trusted publishing with `id-token: write` only in the publish job;
   - generate SBOM/provenance attestations for release artifacts.

2. Add a container release lane only when images are intended for distribution:
   - build by digest;
   - scan the produced image digest;
   - build/push with SBOM and provenance;
   - attest the image digest;
   - keep promotion explicit, tag-based, and reversible.

3. Make Docker healthchecks mode-aware:
   - keep default plain HTTP healthcheck for default mode;
   - add documented Compose overrides for TLS/auth;
   - add one CI smoke that validates an auth-enabled healthcheck or explicitly validates the disabled-healthcheck recovery path.

4. Add a safer secret input mechanism:
   - smallest option: `--auth-file` reading `user:password` from a mounted secret file;
   - update Compose examples to use `secrets:` or a bind-mounted secret file, not argv.

## Quick Wins

- Add `permissions: contents: read` to CI/security workflows; grant broader permissions only in release jobs that need them.
- Add a script check that the Playwright pin in `tools/browser_smoke.py` matches `.github/workflows/ci.yml`.
- Move coverage fail-under into `pyproject.toml` so local and CI coverage behavior match.
- Add `python -m build --sdist --wheel` to release smoke, even before publishing exists.

## Deeper Improvements

- Ratchet coverage gradually by module or by changed files instead of one global jump.
- Add artifact attestation and SBOM verification as required release checks.
- Add image digest promotion notes and rollback steps for GHCR/Docker publishing.
- Consider SHA pinning third-party Actions in release workflows first, then CI if maintenance overhead is acceptable.

## Open Questions

- Are `ci.yml` and `security.yml` both required branch-protection checks on `main`?
- Is PyPI/GHCR publishing planned, or are release artifacts only local/internal?
- Should Docker Compose examples become supported deployment templates or remain examples only?
- What is the intended credential source for non-interactive services: env var, file secret, stdin, or platform secret manager?
