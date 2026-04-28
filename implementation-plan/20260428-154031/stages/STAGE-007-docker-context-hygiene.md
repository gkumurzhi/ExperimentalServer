# STAGE-007 — Harden Docker Build Context Ignores

## Status
CLOSED

## Priority
HIGH

## Source findings
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/docker-expert.md` — HIGH: `.dockerignore` misses `notes/`, `.env*`, keys, certs, credentials
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/architect-reviewer.md` — MEDIUM: `notes/` runtime data not ignored

## Goal
Docker build contexts exclude runtime data and secret-like files by default.

## Non-goals
- Do not inspect or modify `notes/` or `uploads/` contents.
- Do not change Docker runtime behavior or healthchecks; STAGE-021 owns that.

## Scope
### Likely files to inspect
- `.dockerignore` — build context exclusions
- `.gitignore` — runtime data policy signal
- `Dockerfile` — copied paths
- `examples/docker/docker-compose.yml` — `/data` runtime mount

### Likely files to change
- `.dockerignore` — add runtime/secret-heavy ignore patterns
- Optional `.gitignore` coordination deferred to STAGE-024 if broader runtime-data policy is needed

### Files that must not be changed
- `uploads/**` — runtime user data; do not inspect contents unless an explicit disposable test fixture is created
- `notes/**` — encrypted runtime note data; do not inspect contents
- `.env*`, `*.key`, `*.pem`, `*.p12`, `*.pfx`, credential JSON — secret-heavy files
- `codex-analysis/**` — source analysis artifacts; read-only evidence only
- `implementation-plan/**` — planning artifacts; close-plan-stage may update status/report files only

## Dependencies
- Depends on: None
- Blocks: STAGE-021

## Implementation steps
1. Add ignore patterns for `notes/`, `.env`, `.env.*`, key/cert formats, SSH keys, credential JSON, secret JSON, and likely generated cert output paths.
2. Keep required build inputs available to Dockerfile targeted COPY commands.
3. Validate build context configuration statically without printing secret file contents.

## Acceptance criteria
- [x] `.dockerignore` excludes `notes/` and common secret-like file patterns.
- [x] Dockerfile required inputs are not accidentally ignored.
- [x] No runtime data contents are read or copied during verification.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `docker build --no-cache --target runtime .` if Docker is available, otherwise static Dockerfile/COPY review | Build succeeds or static review confirms no required input excluded |
| Type/lint/build | `docker buildx build --help >/dev/null` optional environment check | Docker tooling availability known |
| Manual/static review | `git check-ignore -v notes .env example.key` using dummy names only | Patterns match dummy secret/runtime paths |

## Suggested subagents
- `docker-expert` — review Docker context patterns.
- `security-auditor` — review secret-like exclusions.

## Risks and rollback
- Risk: Over-broad ignore patterns may exclude intentional test fixtures.
- Rollback: Revert `.dockerignore` changes for this stage.

## Completion notes
Closed 2026-04-28 22:40:57 MSK. `.dockerignore` now excludes runtime data (`notes/`, `uploads/`, example compose data) and secret-like files including `.env*`, nested env files, key/cert/keystore formats, SSH private keys, credential/secret JSON, and generated certificate/secret directories. Docker runtime build, disposable dummy-context checks, `diff --check`, and Docker/security verifier subagents passed after resolving the security verifier's `.env*` and singular `secret/` findings.
