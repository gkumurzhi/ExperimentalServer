# Source Map

## Repository State
- Repo root: `/home/user/PycharmProjects/ExperimentalHTTPServer`
- Branch: `main`
- Planning run: `implementation-plan/20260505-205639`
- Generated: 2026-05-05 20:56:39 MSK
- Dirty status captured with `git status --short` before planning:

```text
 M API.md
 M CHANGELOG.md
 M Dockerfile
 M README.md
 M SECURITY.md
 M constraints/ci.txt
 M docs/ADR/ADR-002-advanced-upload-xor-hmac.md
 M docs/ADR/ADR-003-cryptography-optional.md
 M docs/ADR/README.md
 M docs/api.md
 M docs/architecture.md
 M docs/changelog.md
 M docs/index.md
 M docs/security.md
 M examples/notepad_client.py
 M pyproject.toml
 M src/cli.py
 M src/security/tls.py
 M src/security/tls_manager.py
 M src/server.py
 M tests/test_cli.py
 M tests/test_security/test_tls.py
 M tests/test_security/test_tls_manager.py
?? codex-analysis/20260505-193249/
```

## Analysis Artifacts
| Artifact | Last modified | Use |
|---|---|---|
| `codex-analysis/20260505-193249/project-analysis-report.md` | 2026-05-05 20:51:25 | Primary source for findings, priorities, roadmap, blockers, and source appendix |
| `codex-analysis/20260505-193249/agent-reports/websocket-engineer.md` | 2026-05-05 20:11:19 | Secure Notepad HKDF, recoverability, WS reconnect/idempotency evidence |
| `codex-analysis/20260505-193249/agent-reports/security-auditor.md` | 2026-05-05 20:13:48 | ACME cache validation, title metadata privacy, CSP/runtime string findings |
| `codex-analysis/20260505-193249/agent-reports/devops-engineer.md` | 2026-05-05 20:23:37 | CI smoke, pre-commit, dependency audit, Docker smoke, ignored local files |
| `codex-analysis/20260505-193249/agent-reports/docker-expert.md` | 2026-05-05 20:22:12 | Docker/Compose ACME/sslip path, healthcheck, container state requirements |
| `codex-analysis/20260505-193249/agent-reports/cli-developer.md` | 2026-05-05 20:08:01 | CLI validation and TLS source precedence findings |
| `codex-analysis/20260505-193249/agent-reports/dependency-manager.md` | 2026-05-05 20:24:24 | Constraints, pre-commit dependency, empty `[crypto]`, local env drift |
| `codex-analysis/20260505-193249/agent-reports/frontend-developer.md` | 2026-05-05 20:25:27 | Notepad UI copy, dirty edits, WS retry, smoke coverage |
| `codex-analysis/20260505-193249/agent-reports/documentation-engineer.md` | 2026-05-05 20:26:11 | Docs/API/README/ADR dependency and ACME docs drift |
| `codex-analysis/20260505-193249/agent-reports/api-documenter.md` | 2026-05-05 20:39:49 | Public API contract gaps and exact Notepad/ACME documentation needs |
| `codex-analysis/20260505-193249/agent-reports/qa-expert.md` | 2026-05-05 20:22:56 | Test gaps, collect-only evidence, targeted regression recommendations |
| `codex-analysis/20260505-193249/agent-reports/reviewer.md` | 2026-05-05 20:49:16 | PR-style blocker ranking for dirty TLS/ACME/dependency diff |
| `codex-analysis/20260505-193249/agent-reports/python-pro.md` | 2026-05-05 20:11:19 | Python runtime import, CLI, ACME cache, persistence atomicity evidence |
| `codex-analysis/20260505-193249/agent-reports/performance-engineer.md` | 2026-05-05 20:11:19 | Advanced upload body guardrail, backpressure, metrics, limits evidence |
| `codex-analysis/20260505-193249/agent-reports/architect-reviewer.md` | 2026-05-05 20:11:19 | Architecture boundary, persistence docs, ACME cache-pair recommendations |
| `codex-analysis/20260505-193249/preflight.md` | 2026-05-05 19:35:26 | Source appendix context only |
| `codex-analysis/20260505-193249/agents-inventory.md` | 2026-05-05 19:44:29 | Source appendix context only |
| `codex-analysis/20260505-193249/analysis-plan.md` | 2026-05-05 19:46:27 | Source appendix context only |

## Template Artifact
| Artifact | Use |
|---|---|
| `/home/user/.agents/skills/implementation-plan/references/plan-templates.md` | Required output structures for active plan, stage files, status, matrix, backlog, risks, decisions, and README |
