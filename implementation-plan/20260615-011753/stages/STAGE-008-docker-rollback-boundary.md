# STAGE-008 - Docker and rollback boundary

## Status
OPEN

## Priority
MEDIUM

## Source findings
- `codex-analysis/20260614-225437/agent-reports/devops-engineer.md` - Medium: release rollback evidence expires too quickly because artifacts retain for 30 days.
- `codex-analysis/20260614-225437/agent-reports/docker-expert.md` - Medium: raw image default binds `0.0.0.0` without auth/TLS/profile; Compose mitigates through loopback publication.
- `codex-analysis/20260614-225437/agent-reports/security-auditor.md` - Quick Wins: Docker examples should pass an explicit profile and warn about lab/non-loopback/no-auth.
- `codex-analysis/20260614-225437/project-analysis-report.md` - DevOps & Infrastructure: keep Docker as example/operator convenience unless ownership expands.

## Goal
Make Docker/profile examples and release rollback docs match the support boundary, and ensure "previous verified artifact" rollback remains real.

## Non-goals
- Do not publish to PyPI or GHCR.
- Do not add image SBOM/provenance/scanning unless Docker is explicitly promoted to a supported artifact.
- Do not change CLI default profile; that is STAGE-004.

## Scope
### Likely files to inspect
- `Dockerfile` - image command, healthcheck, user, bind behavior.
- `examples/docker/docker-compose.yml` - loopback publication and profile arguments.
- `.github/workflows/release.yml` - artifact retention and release asset behavior.
- `README.md`, `CONTRIBUTING.md`, `SECURITY.md` - Docker status, rollback, external exposure, artifact policy.
- `.github/workflows/ci.yml` - Docker smoke coverage.

### Likely files to change
- `examples/docker/docker-compose.yml` - pass explicit `--profile workspace` or `--profile serve` if approved by STAGE-002.
- `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, and docs mirrors - document Docker status, explicit profiles, and rollback reality.
- `.github/workflows/release.yml` - increase artifact retention or attach durable GitHub Release assets for tag builds, depending on chosen policy.
- `.github/workflows/ci.yml` - add profile-specific Docker smoke only if examples switch away from implicit `lab`.

### Files that must not be changed
- `src/features.py` and `src/cli.py` - default migration is STAGE-004.
- Dependency constraints and package metadata - out of scope.
- Registry credentials, secrets, or deployment tokens - never read or write.
- `.env*`, credentials, keys, certificates - secrets are out of scope.

## Dependencies
- Depends on: STAGE-002
- Blocks: `None`

## Implementation steps
1. Re-read the STAGE-002 decision for Docker status and safe profile stance.
2. Make Docker examples explicit about `--profile workspace`, `--profile serve`, or documented `lab` usage.
3. Clarify that the image is an example/operator convenience unless the project intentionally supports registry artifacts.
4. Align rollback docs with actual artifact durability: either increase retention enough for the documented rollback process or publish durable GitHub Release assets for tag builds.
5. Review container shutdown timeout wording against body/response deadlines and document current behavior or adjust example grace periods if needed.
6. Add profile-specific Docker smoke only if example behavior changes.

## Acceptance criteria
- [ ] Docker examples pass an explicit safe profile or clearly document intentional `lab` usage and required auth/TLS/firewall controls.
- [ ] Release rollback docs point to artifacts that remain available for the documented rollback window.
- [ ] The project states whether Docker is example/operator convenience or a supported registry artifact.
- [ ] Docker smoke or docs are updated if Compose/example profile behavior changes.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Compose config | `docker compose -f examples/docker/docker-compose.yml config` | Exits 0 if Docker Compose is installed. |
| Release workflow review | Inspect `.github/workflows/release.yml` retention/assets | Rollback artifacts match documented policy. |
| Docs checks | `python tools/sync_docs.py --check && python tools/check_stale_docs.py` | Exits 0. |
| Optional Docker smoke | Existing CI Docker smoke or local Docker build/run if available | Exits 0 when Docker is available. |

## Suggested subagents
- `explorer` - inspect Docker/release/docs current behavior.
- `worker` - implement Docker example and rollback policy changes.
- `devops-reviewer` - review artifact durability and Docker support boundary if available.

## Risks and rollback
- Risk: changing Compose profile defaults can surprise users relying on lab features in examples.
- Rollback: restore previous Compose command and keep explicit warning/docs; leave release artifact retention changes if they are independently beneficial.

## Completion notes
Filled by `close-plan-stage`.
