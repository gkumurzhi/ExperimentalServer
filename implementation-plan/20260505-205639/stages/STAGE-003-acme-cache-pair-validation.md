# STAGE-003 - Validate ACME cert/key cache pairs before reuse

## Status
CLOSED

## Priority
HIGH

## Source findings
- `codex-analysis/20260505-193249/project-analysis-report.md` - Security & Compliance: `_try_letsencrypt()` reuses fresh cert without checking `privkey.pem`.
- `codex-analysis/20260505-193249/agent-reports/security-auditor.md` - MEDIUM: fresh ACME certs reused without validating private key cache state.
- `codex-analysis/20260505-193249/agent-reports/python-pro.md` - MEDIUM: recoverable ACME cache state fails late.
- `codex-analysis/20260505-193249/agent-reports/reviewer.md` - MEDIUM blocker unless fail-late behavior is explicitly accepted.
- `codex-analysis/20260505-193249/agent-reports/architect-reviewer.md` - recommendation: treat ACME cert/key as an atomic pair.

## Goal
Ensure cached ACME material is reused only when both `fullchain.pem` and `privkey.pem` exist, parse, and belong together; otherwise renew/recover or fail early with clear diagnostics.

## Non-goals
- Do not add live ACME staging issuance.
- Do not add a configurable ACME directory in this stage.
- Do not rewrite the embedded ACME client flow unless required for cache validation.

## Scope
### Likely files to inspect
- `src/security/tls_manager.py` - `_try_letsencrypt()` reuse and context-load behavior.
- `src/security/tls.py` - certificate parsing, renewal checks, key generation/cache helpers.
- `tests/test_security/test_tls_manager.py` - existing cert/key reuse and renewal tests.
- `tests/test_security/test_tls.py` - certificate/key helper tests.

### Likely files to change
- `src/security/tls_manager.py` - apply pair validation before cached reuse.
- `src/security/tls.py` - optional helper for parsing/matching cert and private key.
- `tests/test_security/test_tls_manager.py` - add missing-key, invalid-key, and mismatched-key/cache tests.
- `README.md` or docs - only if error/recovery behavior becomes user-visible.

### Files that must not be changed
- `~/.exphttp/**`, `*.pem`, local ACME/cert/key material - do not inspect or edit real secrets.
- `examples/docker/docker-compose.yml` - container docs are STAGE-005.
- `.env*`, credentials, keys, certificates - never read or edit secrets.

## Dependencies
- Depends on: STAGE-001
- Blocks: STAGE-005, STAGE-008

## Implementation steps
1. Add or reuse helpers that load the cached certificate and private key without exposing key material.
2. Check both paths exist before cached reuse.
3. Parse both files and compare the certificate public key to the private key public key, or otherwise establish a robust same-pair check.
4. Define behavior for missing/invalid/mismatched key: renew if safe within existing ACME flow, or fail early with a message naming the broken cache state and repair path.
5. Add focused tests for fresh cert with missing key, invalid key, mismatched key, and happy cached reuse.

## Acceptance criteria
- [x] A fresh `fullchain.pem` without usable `privkey.pem` is not silently reused.
- [x] Mismatched or unparsable cert/key cache state fails early or renews according to explicit behavior.
- [x] Happy-path cached cert/key reuse remains covered.
- [x] Error messages do not include secret key contents.
- [x] Tests cover the previously missing cache states.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted TLS manager tests | `pytest -q tests/test_security/test_tls_manager.py` | Passes with new cache-state tests |
| TLS helper tests | `pytest -q tests/test_security/test_tls.py` | Passes |
| Static secret review | Inspect logs/errors and tests | No private-key contents are printed or asserted |
| CLI smoke | `python -m src --help > /dev/null` | Imports still succeed in dependency-complete env |

## Suggested subagents
- `explorer` - confirm existing test factories for cert/key material and monkeypatch patterns.
- `worker` - implement pair validation and focused tests.
- `security-auditor` - review secret-handling and fail/renew behavior.

## Risks and rollback
- Risk: Comparing public keys can be implemented incorrectly across key types.
- Rollback: Revert helper and `_try_letsencrypt()` changes; keep tests as evidence if behavior decision changes.

## Completion notes
Closed 2026-05-05 22:08:12 MSK.

- Added sanitized ACME cache validation helpers for PEM certificate/private-key presence, parsing, and public-key pairing.
- Validates primary, legacy, and newly obtained ACME cert/key material before reuse; recoverable missing/mismatched states renew, while unusable key states fail early with repair guidance.
- Added focused regression coverage for missing key, malformed key, missing cert plus malformed key, mismatched primary/legacy/obtained pairs, and happy cached reuse.
- Verification passed with targeted TLS tests, mypy, ruff, compileall, CLI import smoke, static secret review, and verifier/security subagents.
- Report: `stage-reports/STAGE-003-20260505-214641.md`.
