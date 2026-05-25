# STAGE-009 - Release artifacts and provenance lane

## Status
OPEN

## Priority
MEDIUM

## Source findings
- `codex-analysis/20260525-121051/agent-reports/devops-engineer.md` - MEDIUM no controlled release, publish, SBOM, provenance, or attestation path.
- `codex-analysis/20260525-121051/agent-reports/docker-expert.md` - MEDIUM no image release/SBOM/provenance lane.
- `codex-analysis/20260525-121051/agent-reports/qa-expert.md` - release smoke does not exercise exact installed wheel or container UI runtime.

## Goal
Create a tag-gated release lane that builds artifact-of-record wheel/sdist and, if image distribution is intended, a container image digest with SBOM/provenance/scanning hooks.

## Non-goals
- Actually publishing to PyPI or a container registry unless repository secrets/OIDC are already configured and the owner has explicitly requested publishing.
- Package import rename; covered by STAGE-010.
- Broad coverage gate ratcheting.

## Scope
### Likely files to inspect
- `.github/workflows/ci.yml` - existing build, smoke, Docker checks.
- `.github/workflows/security.yml` - existing audit workflow.
- `pyproject.toml` - build metadata and optional dependencies.
- `tools/check_static_ui_assets.py` - wheel static asset validation.
- `tools/browser_smoke.py` - source-tree browser smoke entry.
- `README.md`, `CONTRIBUTING.md` - release/contributor docs.

### Likely files to change
- `.github/workflows/release.yml` or equivalent - tag-gated release artifact workflow.
- `.github/workflows/ci.yml` - reuse installed-wheel smoke if appropriate.
- `tools/` - add installed-wheel browser smoke support if needed.
- `README.md`, `CONTRIBUTING.md`, `docs/` - release artifact and rollback documentation.

### Files that must not be changed
- Repository secrets or credentials.
- Generated dist artifacts committed to the repo.

## Dependencies
- Depends on: STAGE-008
- Blocks: STAGE-010

## Implementation steps
1. Add or design a release workflow triggered by tags and manual dispatch for dry runs.
2. Build wheel and sdist from a clean checkout with explicit permissions.
3. Install the built wheel in a fresh venv and run `exphttp --help`, `exphttp --version`, import probes, static UI asset check, and browser smoke against the installed artifact when feasible.
4. Upload dists as workflow artifacts.
5. Add SBOM/provenance/attestation steps for Python artifacts and optional container image digest if publication is intended.
6. Add scan/check step for produced container digest when container release is enabled.
7. Document release promotion and rollback by artifact version or image digest.

## Acceptance criteria
- [ ] Release workflow builds wheel and sdist as artifacts of record.
- [ ] Installed-wheel smoke runs without importing from the source tree.
- [ ] Static UI assets are checked from the built wheel.
- [ ] Workflow permissions are minimal and explicit.
- [ ] SBOM/provenance/attestation/scanning path is present or explicitly documented as blocked by publish intent.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Local build | `python -m build --sdist --wheel --outdir /tmp/exphttp-dist` | Wheel and sdist are produced |
| Isolated wheel smoke | `python -m venv /tmp/exphttp-wheel-smoke` then `/tmp/exphttp-wheel-smoke/bin/pip install /tmp/exphttp-dist/exphttp-*.whl` then `/tmp/exphttp-wheel-smoke/bin/exphttp --version` | Built wheel installs and CLI runs |
| Static UI artifact check | `python tools/check_static_ui_assets.py --wheel /tmp/exphttp-dist/exphttp-*.whl` | Wheel contains required UI assets |
| Workflow static review | `python tools/check_stale_docs.py` | Release docs and semantic guards pass |

## Suggested subagents
- `explorer` - inventory workflow permissions and smoke scripts.
- `worker` - add release workflow and installed-wheel smoke support.
- `qa` - validate local artifact commands and workflow syntax where possible.

## Risks and rollback
- Risk: Publishing configuration may not exist or may be intentionally private.
- Rollback: Keep release workflow artifact-only until owner enables trusted publishing or registry credentials.

## Completion notes
Filled by `close-plan-stage`.

