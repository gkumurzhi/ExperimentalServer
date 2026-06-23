# Implementation Plan
_Generated: 2026-05-05 20:56:39 MSK_

## Source analysis
- `codex-analysis/20260505-193249/project-analysis-report.md`
- `codex-analysis/20260505-193249/agent-reports/websocket-engineer.md`
- `codex-analysis/20260505-193249/agent-reports/security-auditor.md`
- `codex-analysis/20260505-193249/agent-reports/devops-engineer.md`
- `codex-analysis/20260505-193249/agent-reports/docker-expert.md`
- `codex-analysis/20260505-193249/agent-reports/cli-developer.md`
- `codex-analysis/20260505-193249/agent-reports/dependency-manager.md`
- `codex-analysis/20260505-193249/agent-reports/frontend-developer.md`
- `codex-analysis/20260505-193249/agent-reports/documentation-engineer.md`
- `codex-analysis/20260505-193249/agent-reports/api-documenter.md`
- `codex-analysis/20260505-193249/agent-reports/qa-expert.md`
- `codex-analysis/20260505-193249/agent-reports/reviewer.md`
- `codex-analysis/20260505-193249/agent-reports/python-pro.md`

## Strategy
Start by restoring release-smoke signal, then close the user-facing cryptographic and TLS/ACME correctness blockers before broadening to documentation, dependency tooling, Docker coverage, Notepad reliability, upload/body limits, atomic persistence, and CI/local confidence drift. The order keeps high-risk merge blockers first while avoiding stages that require live ACME issuance or product decisions that were still open in the analysis.

No new external documentation checks were performed during this planning pass. The source analysis reports record prior Context7/current-docs checks for `cryptography`, Certbot `acme`, `pytest`, Python `argparse`/`ThreadPoolExecutor`, browser WebSocket/CSP behavior, and dependency ecosystem guidance, with no Context7 blocker.

## Normalized actionable findings
| Finding ID | Source | Severity | Area | Evidence | Root cause | Proposed outcome | Confidence |
|---|---|---:|---|---|---|---|---:|
| F-001 | `project-analysis-report.md` critical/high table; `reviewer.md` | HIGH | CI | `.github/workflows/ci.yml` stale-doc grep matches valid `docs/changelog.md` text and exits before browser/Docker smoke | Broad grep denylist treats historical/current changelog text as stale contract | Replace or narrow stale-doc guard so release smoke reaches browser and Docker validation | High |
| F-002 | `websocket-engineer.md`; `api-documenter.md`; `qa-expert.md`; `reviewer.md` | HIGH | Secure Notepad | `examples/notepad_client.py` HKDF `salt=None`/`exphttp-notepad` differs from server/browser zero salt and `notepad-e2e-key`; API omits recoverability limits | Public example and API do not pin the cryptographic contract | Fix example, document exact HKDF/session limits/plaintext metadata, add interoperability regression | High |
| F-003 | `security-auditor.md`; `python-pro.md`; `architect-reviewer.md`; `reviewer.md` | HIGH | TLS/ACME | `TLSManager._try_letsencrypt()` reuses fresh `fullchain.pem` without validating `privkey.pem` existence/parse/pairing | Certificate cache is not treated as an atomic cert/key pair | Validate cache pair before reuse and renew or fail early with clear repair guidance | High |
| F-004 | `cli-developer.md`; `python-pro.md`; `performance-engineer.md`; `reviewer.md` | HIGH | CLI/TLS | `--key` alone can start plaintext; cert/key plus ACME silently selects ACME; invalid numeric values reach lower layers | CLI source/mode validation is incomplete | Add argparse validation and lower-layer guards for TLS source combinations and numeric bounds | High |
| F-005 | `docker-expert.md`; `devops-engineer.md`; `api-documenter.md`; `reviewer.md` | HIGH | Docker/Ops | Compose publishes only `8080`, read-only root lacks writable ACME cache, Docker healthcheck is HTTP-only | ACME/sslip container path is documented without required ports, state, and health behavior | Add working Docker/NAT guidance or profile plus healthcheck override expectations | High |
| F-006 | `dependency-manager.md`; `documentation-engineer.md`; `frontend-developer.md`; `security-auditor.md` | MEDIUM | Dependencies/Docs/UI | Runtime/UI/docs still recommend empty `exphttp[crypto]`; root docs retain zero-dependency/pure Python claims | Dependency policy moved crypto/ACME into runtime deps but copy/tests/docs did not fully follow | Reword runtime/UI/docs guidance and add stale-reference checks | High |
| F-007 | `devops-engineer.md`; `dependency-manager.md`; `python-pro.md`; `qa-expert.md` | MEDIUM | Tooling | Pre-commit mypy pins `cryptography==46.0.5` and lacks `acme`/`josepy`; audit lacks installed-env completeness | Isolated hook/security environments diverge from constrained runtime install | Align hook deps and add clean installed-env import/`pip check`/audit completeness smoke | High |
| F-008 | `devops-engineer.md`; `docker-expert.md` | MEDIUM | Docker/CI | Docker smoke checks `--version` and HTTP PING only | Smoke coverage does not exercise TLS/import/healthcheck changes | Add Docker runtime import and TLS PING smoke, plus Compose config invariants | High |
| F-009 | `frontend-developer.md`; `security-auditor.md` | MEDIUM | Notepad UX/Privacy | Note titles are plaintext metadata; dirty edits can be lost when switching/newing before debounce save | UI copy overstates privacy and state transitions do not flush or confirm pending edits | Add title metadata warning and dirty-transition guard | High |
| F-010 | `websocket-engineer.md`; `frontend-developer.md` | MEDIUM | WebSocket Notepad | Saves have no operation id/ack tracking/retry; stale close handlers can reconnect over healthy sockets | Reconnect/save state lacks idempotency and connection generation | Add operation IDs or client-generated IDs, ack tracking, retry/fallback, and generation guards | Medium |
| F-011 | `performance-engineer.md`; `api-documenter.md` | MEDIUM | Advanced Upload | JSON body transport parses full body before advanced-upload encoded-size cap | Handler validates after JSON decode/parse | Reject oversized body transport before JSON parsing and update docs/tests | High |
| F-012 | `python-pro.md`; `project-analysis-report.md` | MEDIUM | Persistence | Uploads use check-then-open `"wb"`; notes write ciphertext and metadata non-atomically | Files are not reserved/replaced atomically under concurrent/failing writes | Use exclusive creation/atomic same-directory temp writes with failure-injection tests | Medium |
| F-013 | `qa-expert.md`; `devops-engineer.md` | MEDIUM | CI Process | Ignored `tests/test_close_plan_stages.py` is collected locally but absent in CI checkout | Local-only files match pytest collection patterns | Track, move, or explicitly ignore local-only tests/tools and add collection guard | High |

## Stage overview
| Stage | Priority | Status | Title | Depends on | Main verification | Expected files |
|---|---|---|---|---|---|---|
| STAGE-001 | HIGH | CLOSED | Restore release-smoke stale-doc guard | None | `python -m src --help`, targeted grep/script check | `.github/workflows/ci.yml`, optional `tools/*` |
| STAGE-002 | HIGH | CLOSED | Fix Secure Notepad key contract and example interoperability | STAGE-001 | Notepad example/contract tests, docs sync | `examples/notepad_client.py`, `src/security/keys.py`, `API.md`, `docs/api.md`, tests |
| STAGE-003 | HIGH | CLOSED | Validate ACME cert/key cache pairs before reuse | STAGE-001 | TLS manager targeted tests | `src/security/tls_manager.py`, `src/security/tls.py`, `tests/test_security/test_tls_manager.py` |
| STAGE-004 | HIGH | CLOSED | Normalize CLI TLS source and numeric validation | STAGE-001 | CLI invalid-argument tests | `src/cli.py`, `src/server.py`, `tests/test_cli.py` |
| STAGE-005 | HIGH | CLOSED | Complete container ACME/sslip operator path | STAGE-003 | Compose config check, docs build | `examples/docker/docker-compose.yml`, `README.md`, `Dockerfile`, docs |
| STAGE-006 | MEDIUM | CLOSED | Remove stale crypto/dependency copy drift | STAGE-001 | stale-reference check, docs sync, browser smoke text update | runtime strings, UI strings, docs, smoke tests |
| STAGE-007 | MEDIUM | CLOSED | Align pre-commit and dependency completeness checks | STAGE-006 | `pre-commit run mypy`, `pip check`, security workflow smoke | `.pre-commit-config.yaml`, `.github/workflows/security.yml`, CI |
| STAGE-008 | MEDIUM | CLOSED | Add Docker TLS and runtime import smoke | STAGE-003 | Docker build/run, HTTPS PING | `.github/workflows/ci.yml`, `Dockerfile`, optional tools |
| STAGE-009 | MEDIUM | CLOSED | Guard Notepad plaintext title and dirty transitions | STAGE-002 | browser smoke/unit tests for title warning and dirty switch | `src/data/static/ui/notepad.js`, `src/data/static/ui/core.js`, tests |
| STAGE-010 | MEDIUM | CLOSED | Make Notepad WebSocket saves idempotent | STAGE-009 | WS retry/reconnect tests | `src/data/static/ui/notepad.js`, `src/handlers/notepad.py`, `src/notepad_service.py`, tests |
| STAGE-011 | MEDIUM | CLOSED | Add advanced-upload JSON body guardrails | STAGE-001 | advanced-upload oversized-body tests | `src/handlers/advanced_upload.py`, `API.md`, tests |
| STAGE-012 | MEDIUM | CLOSED | Make user-data writes exclusive and atomic | STAGE-011 | concurrent/failure-injection persistence tests | `src/handlers/files.py`, `src/handlers/advanced_upload.py`, `src/notepad_service.py`, tests |
| STAGE-013 | MEDIUM | CLOSED | Resolve local-only pytest collection drift | STAGE-001 | collect-only and tracked/ignored guard | `.gitignore`, `pyproject.toml`, `tools/`, `tests/`, CI |

## How to close a stage
Use:

```text
$close-plan-stage STAGE-001
$close-plan-stage next
$close-plan-stage STAGE-003 --no-subagents
```

## Definition of closed
A stage is CLOSED only when all acceptance criteria are met, verification is completed, and `stage-status.md` plus a stage report are updated.
