# Implementation Plan
_Generated: 2026-04-28 15:40:31 MSK_

## Source analysis
- `codex-analysis/20260428-113859/project-analysis-report.md`
- `codex-analysis/20260428-113859/analysis-plan.md`
- `codex-analysis/20260428-113859/agent-reports/security-auditor.md`
- `codex-analysis/20260428-113859/agent-reports/python-pro.md`
- `codex-analysis/20260428-113859/agent-reports/architect-reviewer.md`
- `codex-analysis/20260428-113859/agent-reports/websocket-engineer.md`
- `codex-analysis/20260428-113859/agent-reports/performance-engineer.md`
- `codex-analysis/20260428-113859/agent-reports/qa-expert.md`
- `codex-analysis/20260428-113859/agent-reports/devops-engineer.md`
- `codex-analysis/20260428-113859/agent-reports/docker-expert.md`
- `codex-analysis/20260428-113859/agent-reports/frontend-developer.md`
- `codex-analysis/20260428-113859/agent-reports/documentation-engineer.md`
- `codex-analysis/20260428-113859/agent-reports/dependency-manager.md`
- `codex-analysis/20260428-113859/agent-reports/api-documenter.md`

## Strategy
This plan closes high-impact safety issues first, then moves into protocol correctness, resource limits, dependency/CI policy, UI behavior, and documentation drift. Stages are intentionally small enough for one focused `close-plan-stage` run. Source/runtime data contents are out of scope for every stage unless a disposable test fixture is created.

The plan assumes a constraints-first dependency policy for early CI stages because that is the current CI/Docker behavior. A later stage explicitly decides whether to keep constraints or adopt `uv.lock` as the authority.

## Stage overview
| Stage | Priority | Status | Title | Depends on | Main verification | Expected files |
|---|---|---|---|---|---|---|
| STAGE-001 | HIGH | OPEN | Constrain Static Resource Paths | None | `pytest tests/test_handlers/test_path_traversal.py tests/test_http/test_path_traversal_prefix.py tests/test_server_routing.py -q` | src/handlers/base.py, src/handlers/files.py, tests/**/test_*path*traversal*.py |
| STAGE-002 | HIGH | OPEN | Preserve Streaming for Gzip Responses | None | `pytest tests/test_server_methods.py tests/test_server_live.py -q` | src/server.py, tests/test_server_methods.py, CHANGELOG.md |
| STAGE-003 | HIGH | OPEN | Bound SMUGGLE Memory Use | None | `pytest tests/test_server_methods.py -q -k smuggle` | src/handlers/smuggle.py, src/utils/smuggling.py, tests/test_server_methods.py |
| STAGE-004 | HIGH | OPEN | Enforce WebSocket Client Masking | None | `pytest tests/test_websocket.py tests/test_websocket_handlers.py tests/test_security/test_websocket_frame_limit.py -q` | src/websocket.py, src/server.py, tests/test_websocket*.py |
| STAGE-005 | HIGH | OPEN | Make Inspector Asset Intentional | None | `pytest tests/test_server_routing.py tests/test_server_methods.py -q` plus relevant browser smoke if available | src/data/static/ui/inspector.js, src/data/index.html, tests/ |
| STAGE-006 | HIGH | OPEN | Redact Inspector Raw and Copy Output | STAGE-005 | `pytest tests -q -k "browser_smoke or ui or inspector"` or run the browser smoke target if available | src/data/static/ui/inspector.js, src/data/static/ui/requests.js, src/data/static/ui/opsec.js |
| STAGE-007 | HIGH | OPEN | Harden Docker Build Context Ignores | None | `docker build --no-cache --target runtime .` if Docker is available, otherwise static Dockerfile/COPY review | .dockerignore, .gitignore |
| STAGE-008 | HIGH | OPEN | Repair pip-audit Security Workflow | None | `python -m pip_audit --help` and the updated audit command if `pip-audit` is installed | .github/workflows/security.yml, constraints/ci.txt |
| STAGE-009 | HIGH | OPEN | Correct SMUGGLE API Contract Docs | STAGE-003 | `python3 tools/sync_docs.py --check` | API.md, docs/api.md, README.md |
| STAGE-010 | HIGH | OPEN | Correct API Error Contract Docs | None | `python3 tools/sync_docs.py --check` | API.md, docs/api.md, Optional tests only if implementation normalization is chosen instead of docs-first |
| STAGE-011 | HIGH | OPEN | Remove Stale CLAUDE Guidance | None | `pytest tests/test_cli.py -q` | CLAUDE.md |
| STAGE-012 | MEDIUM | OPEN | Reject Malformed Request Lines | None | `pytest tests/test_http tests/test_handlers/test_handler_integration.py tests/test_request_pipeline.py -q` | src/http/request.py, src/request_pipeline.py, tests/ |
| STAGE-013 | MEDIUM | OPEN | Fail Closed for Advanced Upload Crypto Errors | STAGE-012 | `pytest tests/test_handlers/test_handler_integration.py tests/test_security/test_crypto.py -q` | src/handlers/advanced_upload.py, src/security/crypto.py, tests/ |
| STAGE-014 | MEDIUM | OPEN | Enforce Hidden Upload Policy Consistently | STAGE-001 | `pytest tests/test_server_methods.py tests/test_handlers -q -k "hidden or smuggle or fetch or delete"` | src/handlers/files.py, src/handlers/smuggle.py, tests/ |
| STAGE-015 | MEDIUM | OPEN | Make CORS Origin and Header Contract Valid | None | `pytest tests/test_server_methods.py tests/test_http/test_response.py -q -k "cors or options"` | src/http/response.py, src/server.py, src/handlers/files.py |
| STAGE-016 | MEDIUM | OPEN | Validate WebSocket Frame Semantics | STAGE-004 | `pytest tests/test_websocket.py tests/test_websocket_handlers.py tests/test_security/test_websocket_upgrade.py tests/test_security/test_websocket_frame_limit.py -q` | src/websocket.py, src/server.py, tests/ |
| STAGE-017 | MEDIUM | OPEN | Bound WebSocket Resource Use | STAGE-016 | `pytest tests/test_websocket.py tests/test_server_live.py tests/test_security/test_websocket_frame_limit.py -q` | src/server.py, src/websocket.py, src/metrics.py |
| STAGE-018 | MEDIUM | OPEN | Clarify Metrics and Error Counting | STAGE-002 | `pytest tests/test_request_pipeline.py tests/test_server_methods.py -q -k "metrics or error"` | src/metrics.py, src/request_pipeline.py, tests/test_request_pipeline.py |
| STAGE-019 | MEDIUM | OPEN | Reduce Upload Memory Spikes | STAGE-012, STAGE-013 | `pytest tests/test_http/test_content_length_smuggling.py tests/test_handlers/test_handler_integration.py -q` | src/http/io.py, src/handlers/advanced_upload.py, tests/test_http/test_content_length_smuggling.py |
| STAGE-020 | MEDIUM | OPEN | Align CI and Local Toolchain Pins | STAGE-008 | `pre-commit run --all-files` if installed, otherwise `ruff check . && mypy src tests` using constrained env | .pre-commit-config.yaml, constraints/ci.txt, pyproject.toml |
| STAGE-021 | MEDIUM | OPEN | Set Dependency Authority and Update Coverage | STAGE-020 | `python -m pip install -c constraints/ci.txt -e .[crypto,lint,test]` or selected locked workflow command in a disposable env | README.md, .gitignore, .github/dependabot.yml |
| STAGE-022 | MEDIUM | OPEN | Improve Docker Runtime Examples | STAGE-007, STAGE-021 | `docker compose -f examples/docker/docker-compose.yml config --quiet` if Docker Compose is available | Dockerfile, examples/docker/docker-compose.yml, Docs if Docker usage is documented outside example |
| STAGE-023 | MEDIUM | OPEN | Align UI Capabilities, A11y, and Smoke Checks | STAGE-005, STAGE-006 | `node tools/browser_smoke.playwright.js` or project browser smoke wrapper if available | src/data/index.html, src/data/index.html, tools/browser_smoke.playwright.js |
| STAGE-024 | MEDIUM | OPEN | Clean Remaining Documentation Drift | STAGE-009, STAGE-010, STAGE-011, STAGE-013, STAGE-015, STAGE-016 | `python3 tools/sync_docs.py --check` | Canonical root docs — update advanced-upload default, Transfer-Encoding status, HMAC coverage, generated filename workflow, INFO/CORS/WS details, docs/**/*.md, CONTRIBUTING.md |
| STAGE-025 | MEDIUM | OPEN | Protect Runtime Note Data from Accidental Commit | None | `git check-ignore -v notes/example.enc notes/example.meta.json` using dummy paths only | .gitignore, Optional docs note in STAGE-024 if runtime data policy is documented |

## How to close a stage
Use:

```text
$close-plan-stage STAGE-001
$close-plan-stage next
$close-plan-stage STAGE-003 --no-subagents
```

## Definition of closed
A stage is CLOSED only when all acceptance criteria are met, verification is completed, and `stage-status.md` plus a stage report are updated.
