# Source Map

## Preflight context

| Item | Value |
|---|---|
| Repo root | `/home/user/PycharmProjects/ExperimentalHTTPServer` |
| Branch | `main` |
| Git status at plan creation | `?? codex-analysis/20260525-121051/` |
| Existing active plan before update | `implementation-plan/20260521-212008` |
| New plan | `implementation-plan/20260525-133607` |

## Source artifacts used

| Source | Last modified | Usage |
|---|---|---|
| `codex-analysis/20260525-121051/project-analysis-report.md` | 2026-05-25 13:28:22 +0300 | Primary findings, severity ordering, recommended action plan |
| `codex-analysis/20260525-121051/agent-reports/security-auditor.md` | 2026-05-25 12:48:24 +0300 | Auth, CORS, feature surface, storage, proxy, TLS risks |
| `codex-analysis/20260525-121051/agent-reports/architect-reviewer.md` | 2026-05-25 12:41:04 +0300 | Feature profiles, handler boundaries, package identity, auth invariant |
| `codex-analysis/20260525-121051/agent-reports/performance-engineer.md` | 2026-05-25 12:43:54 +0300 | Storage exhaustion, body buffering, slow-body/download, listing, WebSocket knobs |
| `codex-analysis/20260525-121051/agent-reports/qa-expert.md` | 2026-05-25 12:47:16 +0300 | Test gaps and verification strategy |
| `codex-analysis/20260525-121051/agent-reports/docker-expert.md` | 2026-05-25 13:05:45 +0300 | Docker secrets, healthchecks, exposure, resource envelope, SBOM/provenance |
| `codex-analysis/20260525-121051/agent-reports/devops-engineer.md` | 2026-05-25 12:42:00 +0300 | CI/release workflow, installed-wheel smoke, artifact provenance |
| `codex-analysis/20260525-121051/agent-reports/python-pro.md` | 2026-05-25 12:43:01 +0300 | Package layout, atomic file writes, WebSocket error semantics |
| `codex-analysis/20260525-121051/agent-reports/reviewer.md` | 2026-05-25 13:26:11 +0300 | Deduplication, severity corrections, final priority order |

## Repository files inspected for command and scope accuracy

| Source | Usage |
|---|---|
| `pyproject.toml` | Package/test/lint/build commands and package identity scope |
| `.github/workflows/ci.yml` | Existing CI, smoke, Docker, coverage, and release gaps |
| `Dockerfile` | Healthcheck and image runtime command scope |
| `examples/docker/docker-compose.yml` | Compose exposure, secrets, ACME, and healthcheck scope |

