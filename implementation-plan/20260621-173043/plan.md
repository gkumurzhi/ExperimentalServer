# Implementation Plan
_Generated: 2026-06-21 17:30:43 MSK_

## Source analysis
- `codex-analysis/20260621-150449/project-analysis-report.md`
- `codex-analysis/20260621-150449/agent-reports/security-auditor.md`
- `codex-analysis/20260621-150449/agent-reports/architect-reviewer.md`
- `codex-analysis/20260621-150449/agent-reports/frontend-developer.md`
- `codex-analysis/20260621-150449/agent-reports/qa-expert.md`
- `codex-analysis/20260621-150449/agent-reports/documentation-engineer.md`
- `codex-analysis/20260621-150449/agent-reports/cli-developer.md`
- `codex-analysis/20260621-150449/agent-reports/accessibility-tester.md`

## Strategy
Restore the verified `SMUGGLE` runtime path before any presentation cleanup. After the runtime and renderer contract are stable, align operator framing, then update the artifact UI and plugin/config guardrails without widening the `lab` surface or relaxing the global UI CSP.

## Stage overview
| Stage | Priority | Status | Title | Depends on | Main verification | Expected files |
|---|---|---|---|---|---|---|
| STAGE-001 | HIGH | CLOSED | SMUGGLE artifact runtime contract | `None` | `./.venv/bin/pytest -q tests/test_server_methods.py tests/test_server_live.py` and `python tools/browser_smoke.py --profile lab --mode full` | `src/utils/smuggling.py`, `src/handlers/files.py`, `src/handlers/smuggle.py`, `tools/browser_smoke.playwright.js`, `tests/test_server_methods.py` |
| STAGE-002 | HIGH | CLOSED | Renderer seam and contract tests | `STAGE-001` | `./.venv/bin/pytest -q tests/test_utils/test_smuggling.py tests/test_server_methods.py` | `src/utils/smuggling.py`, `exphttp/__init__.py`, `tests/test_utils/test_smuggling.py`, `tests/test_server_methods.py` |
| STAGE-003 | HIGH | CLOSED | Safe operator framing and docs guardrails | `STAGE-001` | `./.venv/bin/pytest -q tests/test_cli.py tests/test_check_stale_docs.py` and `python tools/check_stale_docs.py` | `README.md`, `SECURITY.md`, `docs/security.md`, `docs/architecture.md`, `src/cli.py`, `tools/check_stale_docs.py` |
| STAGE-004 | HIGH | CLOSED | Explicit artifact UI and keyboard safety | `STAGE-002` | `python tools/browser_smoke.py --profile lab --mode full` and `python tools/browser_smoke.py --profile workspace --mode disabled-state` | `src/data/index.html`, `src/data/static/ui/files.js`, `src/data/static/ui/core.js`, `tools/browser_smoke.playwright.js` |
| STAGE-005 | MEDIUM | CLOSED | Plugin core-method reservation | `None` | `./.venv/bin/pytest -q tests/test_extensions.py tests/test_server_methods.py` | `src/server.py`, `src/extensions.py`, `README.md`, `docs/architecture.md`, `tests/test_extensions.py` |
| STAGE-006 | MEDIUM | CLOSED | SMUGGLE temp-control config clarity | `STAGE-003` | `./.venv/bin/pytest -q tests/test_settings.py tests/test_cli.py tests/test_deployment_artifacts.py` and `python -m exphttp --check-config` | `src/settings.py`, `tests/test_settings.py`, `tests/test_cli.py`, `deploy/docker/exphttp.ini.example`, `deploy/systemd/exphttp.ini.example` |

## How to close a stage
Use:

```text
$close-plan-stage STAGE-001
$close-plan-stage next
$close-plan-stage STAGE-003 --no-subagents
```

## Definition of closed
A stage is CLOSED only when all acceptance criteria are met, verification is completed, and `stage-status.md` plus a stage report are updated.
