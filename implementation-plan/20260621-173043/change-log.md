# Change Log

## 2026-06-21 18:23:44 +0300 — STAGE-004
- Status: CLOSED
- Files changed: `src/data/static/ui/core.js`, `src/data/static/ui/files.js`, `src/data/static/ui/components.css`, `tools/browser_smoke.playwright.js`, `implementation-plan/20260621-173043/stage-reports/STAGE-004-20260621-180914.md`, `implementation-plan/20260621-173043/stage-status.md`, `implementation-plan/20260621-173043/stages/STAGE-004-explicit-artifact-ui-and-keyboard-safety.md`
- Verification: `python tools/browser_smoke.py --profile lab --mode full`, `python tools/browser_smoke.py --profile workspace --mode disabled-state`, `python tools/browser_smoke.py --profile serve --mode disabled-state`, and `git diff --check -- ...` all passed.
- Report: `stage-reports/STAGE-004-20260621-180914.md`

## 2026-06-21 18:26:43 +0300 — STAGE-005
- Status: CLOSED
- Files changed: `README.md`, `docs/architecture.md`, `implementation-plan/20260621-173043/stage-reports/STAGE-005-20260621-182643.md`, `implementation-plan/20260621-173043/stage-status.md`, `implementation-plan/20260621-173043/stages/STAGE-005-plugin-core-method-reservation.md`
- Verification: `./.venv/bin/pytest -q tests/test_extensions.py tests/test_server_methods.py`, `./.venv/bin/pytest -q tests/test_handler_registry.py`, and `git diff --check -- ...` passed.
- Report: `stage-reports/STAGE-005-20260621-182643.md`
