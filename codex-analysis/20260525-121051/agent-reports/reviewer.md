# reviewer Report
_Generated: 2026-05-25 13:26:00 MSK_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260525-121051/analysis-plan.md_

**Reviewer Cross-Check**

Scope: read-only review of the saved `analysis-plan.md`, completed agent reports, and `*-error.md` reports under `codex-analysis/20260525-121051`. No files were modified.

**Duplicated Findings To Merge**

- Aggregate resource exhaustion: merge storage-quota findings across security, architecture, Python, performance, QA, Docker, and the plan. Evidence cited includes `src/server.py:84`, `src/handlers/files.py:418-420`, `src/handlers/advanced_upload.py:385-387`, `src/notepad_service.py:390-401`, and `docs/threat-model.md:62`.
- Argv-only auth secrets: merge security/devops/docker/QA findings. Evidence: `src/cli.py:171-177`, `src/cli.py:264`, `src/server.py:225-245`, README examples, and `examples/docker/docker-compose.yml:29-40`.
- Always-on risky features: merge architecture/security/QA findings around `advanced_upload_enabled = True`, deprecated no-op `--advanced-upload`, always-registered `DELETE`, `NOTE`, `SMUGGLE`, and unknown-method advanced upload.
- Wildcard CORS/write/WebSocket trust: merge security/QA/plan findings. Evidence: `src/http/cors.py:83-99`, `src/server.py:777-841`, and tests that assert wildcard mutation/WS allow.
- Docker health/TLS/ACME mode mismatch: merge devops/docker/QA/security findings. Evidence: `Dockerfile:61-64`, `examples/docker/docker-compose.yml:96-99`, `.github/workflows/ci.yml:235-243`, `src/security/tls_manager.py:71-153`.
- Release/SBOM/provenance gap: merge devops/docker/plan findings.
- Generic public `src` package: merge architecture/python/QA/plan findings.

**Severity Corrections**

- Raise argv-only service/container auth secrets to **HIGH** consistently. Devops/QA list this as MEDIUM, but reports show it is the only non-interactive credential path and grants global destructive access.
- Raise always-on destructive/demo capability exposure to **HIGH** consistently. Security/QA list MEDIUM, but architecture and the plan are right: without profiles, least-privilege operation is impossible.
- Raise Docker/TLS/ACME healthcheck lifecycle from security's LOW to **MEDIUM**. It is not a direct exploit, but it can break real auth/TLS/ACME deployments.
- Treat the `src` import/package layout as **MEDIUM** for further development, not LOW, because docs already expose it as public API and migration cost increases with every release.

**Missing Blockers Evident From Reports**

- Add performance/resource blockers not strongly represented in the initial plan: fully buffered standard uploads and slow/incomplete bodies can exhaust memory or all workers. Evidence: `src/http/io.py:102-201`, `src/http/request.py:39-40`, `src/handlers/files.py:418-419`, `src/cli.py:97-119`, `src/server.py:530-540`.
- Docker operation has an additional blocker: default Compose publishes unauthenticated plain HTTP broadly via `examples/docker/docker-compose.yml:18-19`, despite `SECURITY.md:12-18`.

**Final Priority Order**

1. Add resource controls: aggregate disk quotas/retention, in-flight upload memory budget or streaming uploads, slow-body deadlines/rate limits, and container resource/volume limits.
2. Add safe credential injection: `--auth-file`/secret mount or equivalent, then remove inline secret examples from docs/Compose.
3. Add feature profiles/capability gates for `SMUGGLE`, advanced upload, `NOTE`, destructive `DELETE`, and clear operations.
4. Change wildcard CORS policy so `*` is read-only only; require exact origins for browser mutations and WebSocket upgrades.
5. Fix Docker/ops readiness: loopback-only default Compose exposure or explicit auth/TLS, mode-aware healthchecks, and clear ACME renewal/restart policy.
6. Before public distribution, add release artifact smoke from installed wheel/container plus SBOM/provenance/attestation/scanning.
7. Before broader API/library development, migrate public imports from generic `src` to `exphttp` with a compatibility plan.
8. Fix documented programmatic auth so setting custom auth also preserves rate-limiter invariants.
9. Follow up on reduced-coverage areas from error reports: WebSocket lifecycle, API contract docs, dependency/SBOM review, frontend/browser UX, and documentation accuracy.
