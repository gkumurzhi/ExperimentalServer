# docker-expert Report
_Generated: 2026-04-28 12:44:06 MSK_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/analysis-plan.md_

## Summary

Operational boundary analyzed: Docker image build/runtime path for `exphttp` from repository root through `examples/docker/docker-compose.yml`. Scope was limited to `Dockerfile`, `.dockerignore`, `examples/docker/docker-compose.yml`, `constraints/ci.txt`, and `pyproject.toml`.

No files were modified. I did not read `uploads/`, `notes/`, `.env*`, keys, certs, credentials, or runtime data contents.

The image has several good foundations: digest-pinned `python:3.12-slim`, multi-stage wheel build, exec-form `ENTRYPOINT`, non-root runtime user, writable `/data`, and a dependency-constrained install. Main risks are build-context leakage, stale base refresh, fixed healthcheck behavior under TLS/auth overrides, bind-mount permissions, and avoidable cache churn.

## Documentation Checks

Context7: attempted `resolve_library_id("Docker", "Dockerfile reference HEALTHCHECK USER EXPOSE COPY dockerignore build context official documentation")`; Context7 reported monthly quota reached, so no Context7 docs were used.

Official docs checked:

- Docker `.dockerignore` build context behavior: https://docs.docker.com/build/concepts/context/
- Docker build cache layer ordering: https://docs.docker.com/build/cache/optimize/
- Dockerfile `FROM`, exec form, `EXPOSE`, `STOPSIGNAL`, `HEALTHCHECK`: https://docs.docker.com/reference/dockerfile/
- Compose `healthcheck`, `cap_drop`, `read_only`, `secrets`, `security_opt`, `stop_grace_period`, `volumes`: https://docs.docker.com/reference/compose-file/services/
- Docker bind mounts: https://docs.docker.com/engine/storage/bind-mounts/
- Compose top-level `version` obsolete behavior: https://docs.docker.com/reference/compose-file/version-and-name/
- pip secure installs / hashes / binary-only installs: https://pip.pypa.io/en/stable/topics/secure-installs/
- pip constraints and wheel install behavior: https://pip.pypa.io/en/stable/user_guide/

## Issues Found

| Severity | Issue | Evidence | Confidence |
|---|---|---|---|
| HIGH | Build context can still include runtime/secret-like files. The Dockerfile only copies targeted paths, so this is primarily a context-transfer risk, especially with remote builders. | `.dockerignore` excludes `uploads/` but not `notes/`, `.env*`, `*.key`, `*.pem`, credentials, or cert patterns: [.dockerignore](/home/user/PycharmProjects/ExperimentalHTTPServer/.dockerignore:1). `git status --short` showed an untracked `notes/` directory; contents were not read. | High for missing ignores; medium for actual sensitive contents. |
| MEDIUM | Base image is pinned, but the pin appears stale and refresh cadence is manual. | `PYTHON_BASE_IMAGE` pins `python:3.12-slim@sha256:804dd...`: [Dockerfile](/home/user/PycharmProjects/ExperimentalHTTPServer/Dockerfile:5). On 2026-04-28, `docker buildx imagetools inspect python:3.12-slim` returned current digest `sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3`. | High. |
| MEDIUM | Image healthcheck only matches default plain-HTTP/no-auth runtime. TLS/auth command overrides will likely mark the container unhealthy unless Compose overrides or disables the image healthcheck. | Healthcheck probes `http://127.0.0.1:8080/` with `PING`: [Dockerfile](/home/user/PycharmProjects/ExperimentalHTTPServer/Dockerfile:58). Compose comment warns overrides need matching healthcheck but provides no actual override: [docker-compose.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/examples/docker/docker-compose.yml:15). | High for TLS mismatch; medium for auth until live behavior is checked. |
| MEDIUM | Compose bind mount may hide the image-owned `/data` and break writes for non-root UID `10001`. | Image creates/chowns `/data`: [Dockerfile](/home/user/PycharmProjects/ExperimentalHTTPServer/Dockerfile:49). Compose mounts `./data:/data`: [docker-compose.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/examples/docker/docker-compose.yml:13). Docker docs confirm bind mounts obscure existing container data and use host filesystem permissions. | High. |
| MEDIUM | Python package install is version-pinned but not artifact-hash reproducible. | Runtime installs from network using constraints: [Dockerfile](/home/user/PycharmProjects/ExperimentalHTTPServer/Dockerfile:45), constraints pin versions but no hashes: [constraints/ci.txt](/home/user/PycharmProjects/ExperimentalHTTPServer/constraints/ci.txt:4). pip docs recommend `--require-hashes` and `--only-binary :all:` for secure repeatable installs. | High. |
| LOW | Build cache is less effective than it could be. Source changes invalidate the build-tool install layer. | `COPY src ./src` happens before `pip install --upgrade pip build setuptools wheel`: [Dockerfile](/home/user/PycharmProjects/ExperimentalHTTPServer/Dockerfile:16). | High. |
| LOW | Compose example lacks runtime hardening controls beyond the Dockerfile’s non-root user. | Compose service has ports, restart, and volume only: [docker-compose.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/examples/docker/docker-compose.yml:3). No `cap_drop`, `security_opt`, `read_only`, `tmpfs`, `init`, or `stop_grace_period`. | High. |
| LOW | Compose `version: "3.9"` is obsolete with current Compose. | [docker-compose.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/examples/docker/docker-compose.yml:1). `docker compose -f examples/docker/docker-compose.yml config --quiet` succeeded but warned that `version` is obsolete and ignored. | High. |

## Recommendations

1. Expand `.dockerignore` first. Add `notes/`, `.env`, `.env.*`, `*.pem`, `*.key`, `*.p12`, `*.pfx`, `id_rsa*`, `id_ed25519*`, `*credentials*.json`, `*secrets*.json`, and cert/key output paths. This is the smallest change that reduces the highest-risk blast radius.

2. Treat the base digest as an update gate, not a one-time pin. Keep digest pinning, but add a scheduled digest refresh and rebuild/test path. The rollback remains simple: revert the digest line.

3. Make TLS/auth healthcheck behavior explicit in Compose. For the commented TLS/auth example, add an actual `healthcheck: { disable: true }` snippet or a matching HTTPS/auth probe. With `--auth random`, disabling the image healthcheck is safer unless credentials are available to the probe through a secret-safe mechanism.

4. Prefer a named volume for `/data` in the example, or document that bind-mounted `./data` must be writable by UID/GID `10001`. Named volume is safer for the non-root default; bind mount is better only when host-side file inspection is required.

5. Split build dependency setup from source copy. Install pinned build tooling after copying only `pyproject.toml`, `README.md`, and constraints; copy `src/` afterward before `python -m build`. Optionally use a BuildKit pip cache mount in the build stage only.

6. For stricter reproducibility, generate a runtime-specific locked requirements or wheelhouse with hashes for third-party runtime deps, then install with `--require-hashes --only-binary=:all:` where practical.

7. Add Compose hardening after validating runtime writes: `cap_drop: ["ALL"]`, `security_opt: ["no-new-privileges:true"]`, `read_only: true`, `tmpfs: ["/tmp"]`, and explicit `stop_grace_period`.

## Quick Wins

- Add missing `.dockerignore` secret/runtime patterns.
- Remove top-level Compose `version`.
- Add an explicit healthcheck disable/override block next to the TLS/auth command example.
- Add a comment or named volume for `/data` ownership with UID `10001`.
- Move `COPY src ./src` below the build-tool install layer.

## Open Questions

- Is the Docker example meant for local dev only, or should it be production-hardened?
- Does Basic Auth apply to `PING /`? I did not inspect source outside the requested scope.
- Where does TLS mode write generated cert/key material, if any?
- Are remote builders used in CI? If yes, the `.dockerignore` gap is more urgent.
- Which target architectures are supported? This affects `cryptography` wheel availability and binary-only install policy.
