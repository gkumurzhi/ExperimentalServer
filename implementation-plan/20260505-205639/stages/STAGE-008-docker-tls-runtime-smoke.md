# STAGE-008 - Add Docker TLS and runtime import smoke

## Status
OPEN

## Priority
MEDIUM

## Source findings
- `codex-analysis/20260505-193249/project-analysis-report.md` - DevOps: Docker smoke checks only `--version` and plain HTTP PING.
- `codex-analysis/20260505-193249/agent-reports/devops-engineer.md` - MEDIUM: Docker smoke does not validate runtime imports, TLS mode, or healthcheck override behavior.
- `codex-analysis/20260505-193249/agent-reports/docker-expert.md` - LOW: Docker smoke misses `acme`/`cryptography`, hardened Compose, TLS mode, healthcheck override.
- `codex-analysis/20260505-193249/agent-reports/reviewer.md` - Quick win: add Docker TLS smoke.

## Goal
Extend CI Docker smoke so the image proves required runtime crypto/ACME imports and basic TLS serving behavior, without requiring live ACME issuance.

## Non-goals
- Do not run live ACME/sslip issuance in default CI.
- Do not make Docker smoke depend on external DNS or public ports.
- Do not redesign the image healthcheck beyond what is needed for smoke coverage.

## Scope
### Likely files to inspect
- `.github/workflows/ci.yml` - current Docker smoke commands.
- `Dockerfile` - entrypoint, healthcheck, exposed port, runtime user.
- `tools/` - existing smoke helpers, if any.
- `tests/test_server_live.py` - existing TLS/live server patterns for reference.

### Likely files to change
- `.github/workflows/ci.yml` - add Docker runtime import check and TLS PING smoke.
- `Dockerfile` - only if the existing entrypoint/healthcheck blocks the smoke path.
- `tools/docker_smoke.sh` or similar - optional helper if workflow shell becomes hard to read.

### Files that must not be changed
- `examples/docker/docker-compose.yml` - operator profile/docs are STAGE-005 unless a config invariant check is added.
- `src/security/tls.py` - no ACME protocol change in this stage.
- `.env*`, credentials, keys, certificates - never read or edit secrets.

## Dependencies
- Depends on: STAGE-003, STAGE-005
- Blocks: `None`

## Implementation steps
1. Keep existing Docker build, `--version`, and plain HTTP PING smoke.
2. Add a container import check for `acme`, `cryptography`, and `josepy` through the built image.
3. Start a container in self-signed TLS mode on a non-conflicting host port.
4. Probe it with `curl -k -X PING https://127.0.0.1:<port>/` and assert the pong response.
5. Account for Docker healthcheck behavior in TLS mode, either by overriding/disabling it during smoke or waiting/probing independently.

## Acceptance criteria
- [ ] Docker CI fails if the image cannot import required ACME/crypto runtime packages.
- [ ] Docker CI proves self-signed TLS mode responds to HTTPS PING.
- [ ] Existing plain HTTP Docker smoke remains present.
- [ ] The smoke does not require live ACME, public network ingress, or secrets.
- [ ] Healthcheck behavior does not create false negatives for the TLS smoke container.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Docker build | `docker build -t exphttp:ci .` | Builds successfully |
| Import smoke | `docker run --rm exphttp:ci python -c "import acme, cryptography, josepy"` or equivalent entrypoint override | Exits 0 |
| Plain HTTP smoke | Existing `curl -fsS -X PING http://127.0.0.1:18082/` flow | Returns pong |
| TLS smoke | Start image with `--tls`, then `curl -k -fsS -X PING https://127.0.0.1:<port>/` | Returns pong |

## Suggested subagents
- `explorer` - determine the cleanest way to override entrypoint and healthcheck for current Dockerfile.
- `worker` - update CI Docker smoke commands or helper script.
- `docker-expert` - review smoke reliability and container health behavior.

## Risks and rollback
- Risk: CI runner port collisions or slow container startup can make smoke flaky.
- Rollback: Revert TLS smoke to an import-only check and document Docker TLS smoke as a manual command until timing is stabilized.

## Completion notes
Filled by `close-plan-stage`.
