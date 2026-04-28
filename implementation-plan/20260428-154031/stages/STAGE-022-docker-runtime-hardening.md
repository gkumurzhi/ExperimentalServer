# STAGE-022 — Improve Docker Runtime Examples

## Status
OPEN

## Priority
MEDIUM

## Source findings
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/docker-expert.md` — MEDIUM: stale base digest, healthcheck mismatch under TLS/auth, bind-mount permissions, missing hardening

## Goal
Docker examples clearly handle TLS/auth healthchecks, non-root data ownership, digest refresh, and basic runtime hardening.

## Non-goals
- Do not change application auth/TLS semantics.
- Do not inspect real mounted data contents.

## Scope
### Likely files to inspect
- `Dockerfile` — base image digest, healthcheck, build layers
- `examples/docker/docker-compose.yml` — command examples, volume, hardening
- `.github/dependabot.yml` — Docker updates if STAGE-021 selected automation

### Likely files to change
- `Dockerfile` — optional cache-friendly layer ordering and healthcheck notes
- `examples/docker/docker-compose.yml` — healthcheck override/disable example, named volume or UID guidance, Compose hardening
- Docs if Docker usage is documented outside example

### Files that must not be changed
- `uploads/**` — runtime user data; do not inspect contents unless an explicit disposable test fixture is created
- `notes/**` — encrypted runtime note data; do not inspect contents
- `.env*`, `*.key`, `*.pem`, `*.p12`, `*.pfx`, credential JSON — secret-heavy files
- `codex-analysis/**` — source analysis artifacts; read-only evidence only
- `implementation-plan/**` — planning artifacts; close-plan-stage may update status/report files only

## Dependencies
- Depends on: STAGE-007, STAGE-021
- Blocks: None

## Implementation steps
1. Add an explicit Compose healthcheck override or disable block for TLS/auth command overrides.
2. Prefer a named volume for default `/data` or document bind-mount UID/GID `10001` requirements.
3. Remove obsolete Compose `version` key.
4. Add low-risk hardening controls such as `cap_drop`, `no-new-privileges`, `read_only`/`tmpfs` only if compatible with writes.
5. Reorder Dockerfile build layers if it does not change build behavior.

## Acceptance criteria
- [ ] TLS/auth Docker examples no longer imply the default HTTP healthcheck will work unchanged.
- [ ] `/data` write permissions are clear for non-root runtime.
- [ ] Compose config validates without obsolete version warning.
- [ ] Hardening controls do not prevent required writes.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `docker compose -f examples/docker/docker-compose.yml config --quiet` if Docker Compose is available | Compose config validates without obsolete version warning |
| Type/lint/build | `docker build .` if Docker is available | Image builds successfully |
| Manual/static review | Review healthcheck and volume examples | TLS/auth and UID behavior is explicit |

## Suggested subagents
- `docker-expert` — Docker/Compose implementation.
- `devops-engineer` — automation implications.

## Risks and rollback
- Risk: Read-only hardening can break runtime writes if not paired with writable `/data` and `/tmp`.
- Rollback: Revert Dockerfile/Compose/doc changes for this stage.

## Completion notes
Filled by `close-plan-stage`.
