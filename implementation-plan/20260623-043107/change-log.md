# Change Log

## 2026-06-23 04:42:52 MSK — STAGE-001
- Status: CLOSED
- Files changed: `README.md`, `SECURITY.md`, `CONTRIBUTING.md`, `docs/index.md`, `docs/ADR/ADR-006-profile-default-and-exposure.md`, `docs/ADR/ADR-007-published-artifact-surfaces.md`, `docs/ADR/README.md`, `docs/security.md`, `docs/contributing.md`, `tools/check_stale_docs.py`, `implementation-plan/20260623-043107/stages/STAGE-001-supported-surface-publishing-boundary.md`, `implementation-plan/20260623-043107/stage-status.md`, `implementation-plan/20260623-043107/stage-reports/STAGE-001-20260623-043202.md`
- Verification: `python tools/check_stale_docs.py` PASS; `python tools/sync_docs.py --check` PASS; manual diff review confirmed the docs now describe tagged PyPI/GHCR publication without changing the operator-owned deployment boundary.
- Report: `implementation-plan/20260623-043107/stage-reports/STAGE-001-20260623-043202.md`

## 2026-06-23 05:12:44 MSK — STAGE-002
- Status: CLOSED
- Files changed: `docs/ADR/ADR-008-trusted-proxy-client-identity-boundary.md`, `docs/ADR/ADR-006-profile-default-and-exposure.md`, `docs/ADR/README.md`, `README.md`, `SECURITY.md`, `docs/threat-model.md`, `API.md`, `docs/api.md`, `docs/security.md`, `implementation-plan/20260623-043107/stages/STAGE-002-trusted-proxy-client-identity-boundary.md`, `implementation-plan/20260623-043107/stage-status.md`, `implementation-plan/20260623-043107/change-log.md`, `implementation-plan/20260623-043107/stage-reports/STAGE-002-20260623-050758.md`
- Verification: `python tools/check_stale_docs.py` PASS; `python tools/sync_docs.py --check` PASS; manual review confirmed one maintained direct-peer client-identity boundary and deferred trusted-proxy prerequisites across ADR, README, SECURITY, threat model, and API docs.
- Report: `implementation-plan/20260623-043107/stage-reports/STAGE-002-20260623-050758.md`

## 2026-06-23 05:17:59 MSK — STAGE-003
- Status: CLOSED
- Files changed: `docs/ADR/ADR-009-durable-notepad-recovery-boundary.md`, `docs/ADR/README.md`, `README.md`, `SECURITY.md`, `docs/threat-model.md`, `API.md`, `docs/api.md`, `docs/security.md`, `tools/check_stale_docs.py`, `implementation-plan/20260623-043107/stages/STAGE-003-durable-notepad-recovery-adr.md`, `implementation-plan/20260623-043107/stage-status.md`, `implementation-plan/20260623-043107/change-log.md`, `implementation-plan/20260623-043107/stage-reports/STAGE-003-20260623-051419.md`
- Verification: `python tools/check_stale_docs.py` PASS; `python tools/sync_docs.py --check` PASS; manual review confirmed one explicit Notepad durability ADR and consistent session-bound/non-recoverable wording across README, SECURITY, threat model, API, and the doc guard.
- Report: `implementation-plan/20260623-043107/stage-reports/STAGE-003-20260623-051419.md`

## 2026-06-23 05:22:18 MSK — STAGE-004
- Status: CLOSED
- Files changed: `docs/ADR/ADR-010-api-client-strategy-boundary.md`, `docs/ADR/README.md`, `API.md`, `README.md`, `SECURITY.md`, `docs/api.md`, `docs/security.md`, `tools/check_stale_docs.py`, `implementation-plan/20260623-043107/stages/STAGE-004-api-v1-client-strategy-boundary.md`, `implementation-plan/20260623-043107/stage-status.md`, `implementation-plan/20260623-043107/change-log.md`, `implementation-plan/20260623-043107/stage-reports/STAGE-004-20260623-051922.md`
- Verification: `python tools/sync_docs.py --check` PASS; `python tools/check_stale_docs.py` PASS; manual review confirmed one explicit API/client strategy ADR and consistent legacy-v0/no-`/api/v1` wording across API, README, SECURITY, and the doc guard.
- Report: `implementation-plan/20260623-043107/stage-reports/STAGE-004-20260623-051922.md`
