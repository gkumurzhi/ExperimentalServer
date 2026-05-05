# STAGE-005 - Complete container ACME/sslip operator path

## Status
OPEN

## Priority
HIGH

## Source findings
- `codex-analysis/20260505-193249/project-analysis-report.md` - Critical & High Issues #3: documented/container ACME path is incomplete.
- `codex-analysis/20260505-193249/agent-reports/docker-expert.md` - High: hardened Compose ACME/sslip path lacks writable cache and port 80/443 mapping.
- `codex-analysis/20260505-193249/agent-reports/devops-engineer.md` - MEDIUM: Compose ACME mode lacks writable cert cache and port-80 exposure guidance.
- `codex-analysis/20260505-193249/agent-reports/api-documenter.md` - MEDIUM: ACME/sslip docs under-specify prerequisites and recovery behavior.
- `codex-analysis/20260505-193249/agent-reports/reviewer.md` - MEDIUM blocker if sslip is released as supported container guidance.

## Goal
Give operators a container ACME/sslip path that is either demonstrably working or clearly documented as constrained, including public port 80 reachability, HTTPS serving port, writable ACME state, NAT/global IPv4 requirements, `api.ipify.org`, and healthcheck override behavior.

## Non-goals
- Do not require live ACME issuance in default CI.
- Do not change the default plain HTTP Compose service unless necessary.
- Do not add configurable ACME cache directory; that remains backlog unless required.

## Scope
### Likely files to inspect
- `examples/docker/docker-compose.yml` - current hardened Compose example.
- `Dockerfile` - current healthcheck and runtime user/home.
- `README.md` - Docker, TLS, ACME, sslip guidance.
- `docs/architecture.md`, `docs/security.md`, `docs/index.md` - operator/security references if needed.
- `src/security/tls.py` and `src/security/tls_manager.py` - actual ACME paths, ports, public IP behavior.

### Likely files to change
- `examples/docker/docker-compose.yml` - comments or optional profile for ACME/sslip ports, volumes, and healthcheck override.
- `README.md` - concrete Docker/NAT/sslip ACME recipe and failure/recovery caveats.
- `docs/security.md` or `docs/architecture.md` - persistence/secrets boundary if this stage owns it.
- `Dockerfile` - only if healthcheck behavior needs a minimal documented default adjustment.

### Files that must not be changed
- `src/security/tls_manager.py` - cache validation belongs to STAGE-003.
- Real ACME cache directories such as `~/.exphttp/**` - do not read or edit secrets.
- `.env*`, credentials, keys, certificates - never read or edit secrets.

## Dependencies
- Depends on: STAGE-003
- Blocks: STAGE-008

## Implementation steps
1. Decide whether to provide a Compose profile, documentation-only recipe, or both.
2. Document required public port 80 forwarding to the challenge listener and HTTPS serving port mapping.
3. Document writable ACME cache/state volume under the container user's home and clarify backup/restore sensitivity.
4. Document sslip public IPv4 auto-detection through `api.ipify.org`, global IPv4 requirement, NAT/firewall constraints, and unsupported wildcard/DNS-01 behavior.
5. Document or implement healthcheck override/disable behavior for TLS/auth/ACME modes.
6. Run Compose config and docs build checks.

## Acceptance criteria
- [ ] Operators can identify the exact ports and volume needed for ACME/sslip in containers.
- [ ] The default plain HTTP container path remains intact.
- [ ] TLS/auth/ACME healthcheck limitations are called out or handled.
- [ ] ACME cache repair guidance aligns with STAGE-003 behavior.
- [ ] Docs do not imply live ACME works behind NAT/private IPv4 without public port 80 reachability.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Compose validation | `docker compose -f examples/docker/docker-compose.yml config` | Resolves successfully |
| Docs build | `mkdocs build --strict` | Passes |
| Docs sync | `python tools/sync_docs.py --check` if generated docs are touched | Reports mirrors in sync |
| Static ops review | Compare docs to `src/security/tls.py` and `src/security/tls_manager.py` | Ports, paths, and public-IP behavior match code |

## Suggested subagents
- `explorer` - verify current Docker/ACME paths and docs mentions.
- `worker` - update Compose/docs with a bounded operator recipe.
- `docker-expert` - review container ports, read-only root, volume, and healthcheck posture.

## Risks and rollback
- Risk: A Compose ACME profile can look production-grade while still requiring external DNS/routing not controlled by the repo.
- Rollback: Remove the profile and keep the safer documentation-only guidance with explicit limitations.

## Completion notes
Filled by `close-plan-stage`.
