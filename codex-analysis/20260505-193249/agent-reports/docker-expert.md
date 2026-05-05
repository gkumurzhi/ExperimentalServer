# docker-expert Report
_Generated: 2026-05-05 20:03:30 Europe/Moscow_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260505-193249/analysis-plan.md_

## Summary

Read-only docker-expert review completed. Boundary analyzed: `exphttp` container image, example Compose runtime, CI Docker smoke path, and runtime edges for `/data/uploads`, `/data/notes`, `~/.exphttp/acme`, `/tmp`, healthchecks, TLS/auth, and ACME HTTP-01.

Main finding: the default HTTP container path is coherent, but the hardened Compose example is not sufficient for ACME/sslip operation. It publishes only `8080`, keeps the root filesystem read-only, and does not mount writable ACME home state, while ACME defaults to a temporary HTTP-01 server on port `80`.

Validation performed: `docker compose -f examples/docker/docker-compose.yml config` resolved successfully and confirmed only `8080:8080`; `docker build --check -f Dockerfile .` passed with no warnings. No image build/run or live ACME issuance was performed.

## Documentation Checks

- README documents ACME needing external port 80 reachability and cache storage under `~/.exphttp/acme/`: [README.md](/home/user/PycharmProjects/ExperimentalHTTPServer/README.md:360), [README.md](/home/user/PycharmProjects/ExperimentalHTTPServer/README.md:376).
- Compose documents TLS/auth healthcheck override risk, but not ACME port mappings or ACME cache volume needs: [docker-compose.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/examples/docker/docker-compose.yml:26).
- README links Dockerfile but does not provide a container ACME/sslip recipe with ports, mounts, healthcheck, and capability posture: [README.md](/home/user/PycharmProjects/ExperimentalHTTPServer/README.md:13).

## Detailed Findings

- Runtime dependencies are installed through the wheel, not optional extras. `acme>=5.5,<6` and `cryptography>=48.0` are normal deps, constrained to `acme==5.5.0` and `cryptography==48.0.0`: [pyproject.toml](/home/user/PycharmProjects/ExperimentalHTTPServer/pyproject.toml:37), [constraints/ci.txt](/home/user/PycharmProjects/ExperimentalHTTPServer/constraints/ci.txt:4), [Dockerfile](/home/user/PycharmProjects/ExperimentalHTTPServer/Dockerfile:47).
- Base image is pinned by digest in both stages, and Dependabot has Docker coverage. This is good for rollback and update review: [Dockerfile](/home/user/PycharmProjects/ExperimentalHTTPServer/Dockerfile:7), [.github/dependabot.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/.github/dependabot.yml:25).
- Non-root `/data` path is compatible with default uploads/notes. Image creates UID/GID `10001`, owns `/data`, and app creates `/data/uploads` plus `/data/notes`: [Dockerfile](/home/user/PycharmProjects/ExperimentalHTTPServer/Dockerfile:39), [Dockerfile](/home/user/PycharmProjects/ExperimentalHTTPServer/Dockerfile:52), [server.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/server.py:179).
- Compose `read_only: true` plus writable `/tmp` is compatible with self-signed cert temp files, but not with ACME cache under `/home/exphttp/.exphttp` unless an additional writable volume is mounted: [docker-compose.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/examples/docker/docker-compose.yml:10), [tls_manager.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/security/tls_manager.py:99).
- ACME HTTP-01 binds the configured challenge port, default `80`, before the HTTPS server starts: [tls.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/security/tls.py:344). Default Compose publishes only target `8080`, so public port `80` cannot reach the challenge server in that config.
- Image healthcheck is plain HTTP PING on `127.0.0.1:8080`: [Dockerfile](/home/user/PycharmProjects/ExperimentalHTTPServer/Dockerfile:60). It will fail under TLS, and Basic Auth is enforced before PING dispatch: [request_pipeline.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/request_pipeline.py:120), [test_server_live.py](/home/user/PycharmProjects/ExperimentalHTTPServer/tests/test_server_live.py:176).

## Issues Found

- High: hardened Compose ACME/sslip path is incomplete. It lacks writable `~/.exphttp/acme` storage and does not publish host port `80` to the ACME challenge listener or host `443` to HTTPS.
- Medium: Dockerfile healthcheck is correct only for default unauthenticated HTTP mode. TLS/auth/ACME deployments can be marked unhealthy even when the service is intentionally configured differently.
- Medium: ACME startup can exceed the 5s healthcheck start period because public IP lookup and ACME order/challenge happen before the main socket listens.
- Low: Docker smoke verifies `--version` and default PING, but does not assert runtime import of `acme`/`cryptography`, hardened Compose behavior, TLS mode, or healthcheck override behavior.

## Concrete Recommendations

- Keep the default Compose path as plain HTTP `8080`; add a separate ACME/sslip recipe/profile rather than changing the default blast radius.
- For ACME Compose, mount a dedicated secret/state volume at `/home/exphttp/.exphttp`, not inside the image and not from the source tree.
- Prefer high container ports to preserve `cap_drop: [ALL]`: map host `80` to a high `--acme-http-port`, and host `443` to a high HTTPS `--port`, for example host `80:8080` for challenge and `443:8443` for HTTPS.
- Override or disable healthcheck whenever enabling `--tls`, `--auth`, `--letsencrypt`, or `--sslip`. For TLS checks, use HTTPS with certificate verification disabled for localhost probing, or probe through the real public hostname externally.

## Quick Wins

- Add README/Compose comments for ACME: required `80` reachability, `443` mapping, writable ACME volume, and healthcheck override.
- Extend CI Docker smoke with `docker run --rm exphttp:ci python -c "import acme, cryptography"` or an equivalent entrypoint override.
- Add a Compose config check in CI to catch accidental loss of `read_only`, `tmpfs /tmp`, dropped caps, and `/data` volume.

## Deeper Improvements

- Add `--acme-dir` or `EXPHTTP_ACME_DIR` so containers can mount ACME state at an explicit path like `/var/lib/exphttp/acme`.
- Provide a documented ACME Compose profile with cached-cert startup and a separate first-issuance path.
- Consider making the image healthcheck configurable by env or moving healthcheck examples to Compose instead of baking a single HTTP-only probe into the image.

## Open Questions

- Should official container ACME guidance avoid privileged container ports entirely by standardizing on high internal ports?
- Should ACME cert/key cache validation be fixed before recommending persistent ACME volumes broadly?
- Is live ACME staging validation expected in release CI, or should it remain an operator-run checklist because it needs real DNS/public port 80?
