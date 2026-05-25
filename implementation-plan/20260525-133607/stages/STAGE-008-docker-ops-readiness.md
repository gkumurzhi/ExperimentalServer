# STAGE-008 - Docker and operational readiness

## Status
CLOSED

## Priority
MEDIUM

## Source findings
- `codex-analysis/20260525-121051/agent-reports/docker-expert.md` - MEDIUM Docker health, exposure, resource envelope, and release image gaps.
- `codex-analysis/20260525-121051/agent-reports/devops-engineer.md` - MEDIUM Docker health/smoke does not represent auth/TLS/ACME modes.
- `codex-analysis/20260525-121051/agent-reports/qa-expert.md` - MEDIUM Docker health/smoke coverage gap.
- `codex-analysis/20260525-121051/agent-reports/reviewer.md` - final priority includes Docker/ops readiness after CORS.

## Goal
Make Docker examples and CI smoke safer and mode-aware for default HTTP, auth, TLS, and ACME operations.

## Non-goals
- Public image publishing; covered by STAGE-009.
- Implementing app-level quotas; covered by STAGE-001 and STAGE-002.
- Replacing Dockerfile base image or digest pin unless required by CI.

## Scope
### Likely files to inspect
- `Dockerfile` - default healthcheck and entrypoint.
- `examples/docker/docker-compose.yml` - default ports, auth/TLS/ACME profiles, resources.
- `.github/workflows/ci.yml` - Docker smoke behavior.
- `README.md`, `SECURITY.md` - container deployment guidance.
- `src/cli.py` - flags introduced by prior stages.

### Likely files to change
- `examples/docker/docker-compose.yml` - loopback default port, secrets, resource examples, stop grace, healthcheck overrides.
- `Dockerfile` - keep or adjust default HTTP healthcheck only if default mode changes.
- `.github/workflows/ci.yml` - inspect default container health and add one auth/TLS health path or explicit disabled-health validation.
- `README.md`, `SECURITY.md` - document health, ACME renewal/restart, resource envelope, and external exposure guidance.

### Files that must not be changed
- Real Docker secret files.
- Release/publish credentials.

## Dependencies
- Depends on: STAGE-005, STAGE-006, STAGE-007
- Blocks: STAGE-009

## Implementation steps
1. Change default Compose port publishing to host loopback, while leaving image CMD bound to `0.0.0.0` inside the container.
2. Replace inline auth examples with `--auth-file` and Compose secret mount examples.
3. Add commented or profile-gated resource controls: memory, CPU, PID, ulimit, stop grace, and volume quota guidance.
4. Keep default plain HTTP Dockerfile healthcheck if compatible; add Compose overrides for auth/TLS or documented disabled-health behavior for ACME.
5. Extend CI Docker smoke to inspect default container health and cover one auth/TLS override path if feasible.
6. Document ACME restart-before-expiry or renewal policy explicitly.

## Acceptance criteria
- [ ] Default Compose example does not publish plain HTTP on all host interfaces.
- [ ] Compose auth examples use mounted secret files, not inline passwords.
- [ ] Docker health behavior is explicit for default HTTP, auth/TLS, and ACME profiles.
- [ ] CI Docker smoke validates default health status or records a clear mode-aware alternative.
- [ ] Docs describe resource sizing from workers, body budget, and storage quotas.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Compose syntax | `docker compose -f examples/docker/docker-compose.yml config` | Compose file renders successfully |
| Docker default smoke | `docker build -t exphttp:ops-smoke .` | Image builds successfully |
| Docker health smoke | `docker run -d --name exphttp-health-smoke -p 127.0.0.1::8080 exphttp:ops-smoke` then `docker inspect exphttp-health-smoke` | Default container reaches healthy status when Docker is available |
| CI/static checks | `python tools/check_stale_docs.py` | Docs stay aligned with auth/profile/Docker behavior |

## Suggested subagents
- `explorer` - map Docker/Compose health and CI smoke behavior.
- `worker` - update Compose, docs, and CI smoke.
- `qa` - validate Docker commands where Docker is available.

## Risks and rollback
- Risk: Docker is unavailable in local development or CI forks.
- Rollback: Keep Docker commands in CI where available and document skipped local verification in closure report.

## Completion notes
- Closed on 2026-05-25 19:58:26 MSK.
- Default Compose HTTP publishing is now loopback-only while the container still binds `0.0.0.0` internally.
- Added a concrete `auth-tls` Compose profile using a mounted `--auth-file` secret and HTTPS/Auth healthcheck; ACME keeps disabled healthcheck with documented external probe expectations.
- CI Docker smoke now waits for default Docker health and validates TLS/auth mode with a mounted auth-file fixture and disabled image healthcheck.
- README and SECURITY now document Docker health behavior, ACME restart-before-expiry policy, and resource sizing from workers, body memory budget, and storage quotas.
- Verification passed: Compose default/auth-tls/acme config, Docker build, default health smoke, TLS/auth smoke, Compose auth-tls runtime smoke, docs stale guard, CI Docker smoke shell syntax, and `git diff --check`.
