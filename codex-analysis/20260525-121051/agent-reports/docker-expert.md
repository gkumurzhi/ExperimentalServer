# docker-expert Report
_Generated: 2026-05-25 12:57:18 MSK_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260525-121051/analysis-plan.md_

## Summary

Read-only Docker/container analysis completed. I reviewed `Dockerfile`, `.dockerignore`, `examples/docker/docker-compose.yml`, `.github/workflows/ci.yml`, `SECURITY.md`, `README.md`, `src/cli.py`, the source analysis plan, all prior reports, and targeted runtime paths needed for health/auth/TLS evidence.

Operational boundary analyzed: image build path, default container runtime path, Compose example/ACME profile, CI Docker smoke path, and release-image supply chain path. No files were modified and no live Docker build/run was executed.

The Dockerfile is already in a decent baseline state: pinned Python slim digest, multi-stage wheel build, non-root UID, exec-form entrypoint, writable `/data` and ACME state paths, and a minimal `.dockerignore`. Main risks are operational: argv-only auth secrets, mode-mismatched healthchecks, plain HTTP exposure in examples, missing resource/volume quotas, and no image release lane with SBOM/provenance.

## Documentation Checks

- Context7 `/docker/docs` succeeded for Docker hardening, Compose secrets, `no-new-privileges`, and SBOM/provenance guidance. It confirmed Docker’s guidance for non-root users, Compose secret mounts, and `docker/build-push-action` `sbom`/`provenance`.
- Context7 resolved `/compose-spec/compose-spec`, but the query failed with `TypeError: fetch failed`; I used official Docker docs as fallback for Compose keys: [Compose services reference](https://docs.docker.com/reference/compose-file/services/).
- Docker official docs confirm Compose supports overriding/disabling healthchecks, `read_only`, `tmpfs`, `cap_drop`, `security_opt`, `secrets`, `mem_limit`, `pids_limit`, `ulimits`, and `stop_grace_period`; Docker’s attestation docs confirm SBOM/provenance release behavior: [Docker attestations with GitHub Actions](https://docs.docker.com/build/ci/github-actions/attestations/).

## Detailed Findings

Confirmed normal path: default image runs `exphttp --host 0.0.0.0 --port 8080 --dir /data` (`Dockerfile:66-67`), matching the built-in HTTP healthcheck (`Dockerfile:61-64`). Binding `0.0.0.0` inside the container is appropriate for `docker run -p` reachability.

Confirmed hardening: runtime uses a dedicated non-root user (`Dockerfile:31-42`), Compose uses `read_only: true`, `/tmp` tmpfs, `cap_drop: [ALL]`, `security_opt: no-new-privileges:true`, and `init: true` (`examples/docker/docker-compose.yml:8-17`, `53-60`).

Failure path validated statically: `PING` is dispatched only after auth (`src/request_pipeline.py:124-127`), so any `--auth` deployment breaks the Dockerfile’s unauthenticated HTTP healthcheck. TLS/ACME also mismatch because the image healthcheck always probes plain HTTP `127.0.0.1:8080`.

Recovery/rollback path: ACME state is isolated in `exphttp-acme-state:/home/exphttp/.exphttp` and documented as certificate secret material (`examples/docker/docker-compose.yml:67-71`, `README.md:413-423`). Rollback remains image-tag/digest based, but there is no published image artifact-of-record yet.

## Issues Found

- `[HIGH]` Basic Auth secrets are argv-only for containers. CLI accepts only `--auth CREDS` (`src/cli.py:173-177`) and passes it directly into config (`src/cli.py:264`); server rejects non-interactive random auth by telling operators to pass explicit `user:password` (`src/server.py:225-245`). Compose still shows inline `admin:replace-with-a-strong-secret` (`examples/docker/docker-compose.yml:29-40`).

- `[MEDIUM]` Healthchecks are not mode-aware. Dockerfile probes plain unauthenticated HTTP (`Dockerfile:61-64`); README acknowledges TLS/Auth/ACME mismatch (`README.md:437-441`); ACME disables healthcheck entirely (`examples/docker/docker-compose.yml:96-99`); CI TLS smoke uses `--no-healthcheck` (`.github/workflows/ci.yml:235-243`).

- `[MEDIUM]` Default Compose exposure publishes plain HTTP on all host interfaces. The image command using `0.0.0.0` is correct inside a container, but `ports: "8080:8080"` exposes unauthenticated HTTP broadly (`examples/docker/docker-compose.yml:18-19`) despite `SECURITY.md` saying `0.0.0.0` is only for controlled networks with TLS/auth/firewalling (`SECURITY.md:12-18`).

- `[MEDIUM]` No container-level resource envelope or aggregate storage quota. App defaults allow 10 workers and 100 MB per upload (`src/cli.py:97-119`, `src/server.py:79-86`), while Compose has no `mem_limit`, `cpus`, `pids_limit`, `ulimits`, or volume quota. Named volumes for `/data` and ACME state are unbounded.

- `[MEDIUM]` No image release/SBOM/provenance lane. Existing workflows are CI/security only (`.github/workflows/ci.yml`, `.github/workflows/security.yml`); search found no `docker/build-push-action`, `sbom`, `provenance`, image scan, signing, or attestation workflow.

- `[LOW]` Shutdown is signal-aware but not operationally bounded. CLI installs SIGTERM handling (`src/cli.py:215-227`), server stops accept loop, then waits on executor shutdown (`src/server.py:561-566`). Compose uses `init: true`, but no explicit `stop_grace_period`; long uploads/downloads may be SIGKILLed by runtime defaults.

## Concrete Recommendations

Keep the image `CMD` binding to `0.0.0.0`; changing it to `127.0.0.1` would break normal Docker port publishing. Instead, make the default Compose example safer by binding host loopback: `127.0.0.1:8080:8080`, and reserve all-interface publishing for an explicit lab/external profile.

Add a non-argv secret path before promoting container examples: smallest coherent change is `--auth-file /run/secrets/exphttp_auth`, then Compose `secrets:`. This matches Docker’s per-service secret mount model and avoids process-argument leakage.

Make health behavior explicit per mode: keep Dockerfile HTTP health for the default plain mode; add Compose examples for auth/TLS healthcheck overrides or disable health with an external HTTPS probe. Add CI that inspects Docker health for the default mode and one auth/TLS override path.

Add an example runtime envelope: memory, CPU, PID, nofile, and stop grace settings sized from `max_workers * max_upload_size`, plus documented host/orchestrator volume quotas for `/data` and ACME state.

Add a tag-gated image release lane only when image distribution is intended: Buildx build/push by digest, `sbom: true`, `provenance: mode=max`, scan the pushed digest, and keep rollback to the previous digest/tag.

## Quick Wins

- Change Compose default port to loopback-only.
- Replace the commented inline auth password with a TODO pointing at a future secret file path.
- Add `stop_grace_period` to Compose examples.
- Add commented resource-limit examples for `mem_limit`, `cpus`, `pids_limit`, and `ulimits`.
- Extend CI Docker smoke to `docker inspect` default container health status.

## Deeper Improvements

- Implement `--auth-file` and update Docker docs/examples to use Compose secrets.
- Add app-level aggregate storage quotas for uploads, notes, and SMUGGLE artifacts.
- Add mode/profile support so Docker examples can run a safer file-server surface without NOTE/SMUGGLE/advanced upload.
- Add image release workflow with SBOM, provenance, scanning, and digest promotion notes.
- Add protocol-aware health endpoint or healthcheck command support for auth/TLS deployments.

## Open Questions

- Are Compose files examples only, or intended supported deployment templates?
- Is public image publishing planned, and if so which registry owns promotion/rollback?
- Should the default container example optimize for localhost experiments or trusted-lab access?
- Which secret source should be canonical: file secret, env var, stdin, or orchestrator-native secret?
- Should storage enforcement live in the app, filesystem/orchestrator quotas, or both?
