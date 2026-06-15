# docker-expert Report
_Generated: 2026-06-15 00:11:11 Europe/Moscow_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/analysis-plan.md_

## Summary

Subagent execution note: this session does not expose a `spawn_agent` tool, so I performed the requested Docker-expert read-only pass directly. No files were modified.

Operational boundary analyzed: Docker build/runtime path for `exphttp`, including [Dockerfile](/home/user/PycharmProjects/ExperimentalHTTPServer/Dockerfile:1), [examples/docker/docker-compose.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/examples/docker/docker-compose.yml:1), `.dockerignore`, CI Docker smoke, release artifacts, dependency/security workflows, README, and SECURITY guidance.

Recommendation: keep the image as a local/operator example for now. It is directionally well hardened for examples, but not ready to be treated as a published artifact without a GHCR/release lane, image SBOM/provenance, vulnerability scanning, explicit default-profile decision, and rollback-by-digest process.

## Documentation Checks

- No additional Context7 lookup was needed. I relied on the parent Docker documentation check recorded in [analysis-plan.md](/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/analysis-plan.md:71).
- Reviewed completed reports: product recommends postponing public PyPI/GHCR publishing until SLA/rollback/support decisions are made [product-manager.md](/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/agent-reports/product-manager.md:71); security flags Docker default `lab` exposure risk [security-auditor.md](/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/agent-reports/security-auditor.md:22); QA says Docker smoke should move to release only if Docker becomes a release surface [qa-expert.md](/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/agent-reports/qa-expert.md:68).
- Prompt and plan mention root `docker-compose.yml`, but the actual Compose example is [examples/docker/docker-compose.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/examples/docker/docker-compose.yml:1). No root Compose file exists.

## Detailed Findings

- Build posture is solid for a local image: multi-stage build, pinned `python:3.12-slim` digest, constraints-backed pip installs, non-root runtime user, owned `/data` and ACME state paths, and no package-manager installs in the image [Dockerfile](/home/user/PycharmProjects/ExperimentalHTTPServer/Dockerfile:7).
- Runtime hardening is good in Compose: `init: true`, `read_only: true`, tmpfs `/tmp`, `cap_drop: ALL`, `no-new-privileges`, and localhost-only default port publication [examples/docker/docker-compose.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/examples/docker/docker-compose.yml:9).
- Secret handling is mostly complete: auth profile uses Compose secrets mounted at `/run/secrets/exphttp_auth` [examples/docker/docker-compose.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/examples/docker/docker-compose.yml:65), README warns against argv secrets [README.md](/home/user/PycharmProjects/ExperimentalHTTPServer/README.md:451), and `examples/docker/secrets/.gitignore` ignores real local secret files [examples/docker/secrets/.gitignore](/home/user/PycharmProjects/ExperimentalHTTPServer/examples/docker/secrets/.gitignore:1).
- Healthchecks are coherent for documented examples: image probes plain HTTP `PING` [Dockerfile](/home/user/PycharmProjects/ExperimentalHTTPServer/Dockerfile:61), auth/TLS Compose overrides it with HTTPS plus Basic Auth [examples/docker/docker-compose.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/examples/docker/docker-compose.yml:77), and ACME disables it because public-name/cert validation requires an external probe [README.md](/home/user/PycharmProjects/ExperimentalHTTPServer/README.md:496).
- CI validates normal container startup: build, runtime imports, `--version`, HTTP health/PING, and TLS/auth PING are covered in Docker smoke [ci.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/.github/workflows/ci.yml:199).
- Release lane is Python-only: wheel/sdist, dependency SBOM, and attestations exist [release.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/.github/workflows/release.yml:51), but README explicitly says image digest, image SBOM, provenance, and digest scan are not configured [README.md](/home/user/PycharmProjects/ExperimentalHTTPServer/README.md:991).
- Signal handling is better than basic Docker readiness: exec-form entrypoint/CMD [Dockerfile](/home/user/PycharmProjects/ExperimentalHTTPServer/Dockerfile:66), SIGTERM handler calls `server.stop()` [src/cli.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/cli.py:420), and the server shuts down the executor with cleanup [src/server.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/server.py:704).

## Issues Found

- Medium: published-image safety is unresolved. The image command binds `0.0.0.0` without auth/TLS/profile [Dockerfile](/home/user/PycharmProjects/ExperimentalHTTPServer/Dockerfile:67), while CLI default profile remains `lab` [src/cli.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/cli.py:140). Compose mitigates this with localhost publication, but `docker run -p 8080:8080` would expose the lab surface.
- Medium: graceful shutdown is not fully aligned with container timeouts. Compose uses `stop_grace_period: 20s` [examples/docker/docker-compose.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/examples/docker/docker-compose.yml:18), but body and streamed response deadlines default to 300s [src/http/io.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/http/io.py:20). Docker may SIGKILL long uploads/downloads during stop.
- Medium if publishing, low if local-only: base-image refresh is partially operational. Weekly Docker Dependabot exists [dependabot.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/.github/dependabot.yml:25), but no image scanner, image SBOM, image provenance, or registry rollback lane exists.
- Low: image healthcheck is only valid for the default plain HTTP mode. TLS/auth/ACME require overrides; examples handle this, but a published image needs stronger operator docs or labels around healthcheck expectations.
- Low: analysis plan path drift. The plan lists `docker-compose.yml` [analysis-plan.md](/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/analysis-plan.md:418), but the repository uses `examples/docker/docker-compose.yml`.

## Concrete Recommendations

- Immediate decision: declare Docker as an example/operator convenience, not a published artifact, until the profile-default and registry-support decisions are made.
- Smallest safe change when implementation resumes: make the Compose default service pass an explicit `--profile workspace` or `--profile serve`, while leaving image `CMD` unchanged until a compatibility decision is approved.
- If publishing to GHCR: add release image build, HTTP and TLS/auth smoke, vulnerability scan, image SBOM, provenance attestation, immutable digest output, and rollback docs pointing to the previous known-good digest.
- Align stop behavior: either raise `stop_grace_period` to cover expected transfer deadlines or lower container example `--body-timeout` and `--stream-send-timeout` to fit the grace window.
- Keep `python:3.12-slim` for now. It is a defensible base-image choice for Python runtime plus stdlib healthcheck. Do not move to distroless unless publishing needs justify the operability tradeoff.

## Quick Wins

- Update plan/docs references from `docker-compose.yml` to `examples/docker/docker-compose.yml`.
- Add a README `docker run` example that binds `127.0.0.1` and passes an explicit safe profile.
- Add comments or command args in Compose showing timeout values that match `stop_grace_period`.
- Add a short "Docker image status" note: local/operator example today; not a supported registry artifact.

## Deeper Improvements

- Add a GHCR lane only after ownership is clear: tags, digest pinning, SBOM/provenance, scan gate, smoke gate, and rollback procedure.
- Add scheduled image vulnerability scanning separate from Python `pip-audit`.
- Add an external ACME healthcheck recipe for public-name HTTPS validation.
- Add profile-specific Docker smoke if Docker examples switch away from implicit `lab`.

## Open Questions

- Is the Docker image a supported release artifact or only a local/operator example?
- Should Docker defaults diverge from CLI defaults and use `workspace` or `serve`?
- What shutdown contract is acceptable for in-flight uploads/downloads?
- Who owns base-image CVE response and digest refresh cadence?
- If GHCR is added, what tag policy and rollback digest policy should be guaranteed?
