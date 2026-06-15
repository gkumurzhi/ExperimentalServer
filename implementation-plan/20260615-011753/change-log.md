# Change Log

## 2026-06-15 13:04:45 +0300 - STAGE-002
- Status: CLOSED
- Files changed: `README.md`, `SECURITY.md`, `docs/ADR/ADR-006-profile-default-and-exposure.md`, `docs/ADR/README.md`, `docs/security.md`, `docs/threat-model.md`, `implementation-plan/20260615-011753/stages/STAGE-002-profile-exposure-decision-gate.md`, `implementation-plan/20260615-011753/stage-status.md`, `implementation-plan/20260615-011753/change-log.md`, `implementation-plan/20260615-011753/stage-reports/STAGE-002-20260615-125438.md`
- Verification: `python tools/sync_docs.py --check` passed; `python tools/check_stale_docs.py` passed; manual/static diff review confirmed runtime defaults, Docker files, workflows, and code were unchanged. Optional `mkdocs build --strict` could not run because `mkdocs` is unavailable locally.
- Report: `stage-reports/STAGE-002-20260615-125438.md`

## 2026-06-15 12:50:25 +0300 - STAGE-001
- Status: CLOSED
- Files changed: `.pre-commit-config.yaml`, `CHANGELOG.md`, `docs/api.md`, `docs/changelog.md`, `docs/contributing.md`, `docs/index.md`, `implementation-plan/20260615-011753/stages/STAGE-001-docs-mirror-release-hygiene.md`, `implementation-plan/20260615-011753/stage-status.md`, `implementation-plan/20260615-011753/change-log.md`, `implementation-plan/20260615-011753/stage-reports/STAGE-001-20260615-124223.md`
- Verification: `python tools/sync_docs.py --check` passed; `python tools/check_stale_docs.py` passed; `.pre-commit-config.yaml` parsed; `pre-commit` and `mkdocs` executables were unavailable locally.
- Report: `stage-reports/STAGE-001-20260615-124223.md`
