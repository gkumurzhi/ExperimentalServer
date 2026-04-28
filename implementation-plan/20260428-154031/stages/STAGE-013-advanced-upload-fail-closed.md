# STAGE-013 — Fail Closed for Advanced Upload Crypto Errors

## Status
OPEN

## Priority
MEDIUM

## Source findings
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/security-auditor.md` — MEDIUM: AES-GCM wrong key/tamper writes ciphertext instead of failing
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/qa-expert.md` — MEDIUM: no-crypto AES can store corrupted output
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/agent-reports/documentation-engineer.md` — ADR overstates HMAC metadata coverage

## Goal
Advanced upload rejects authenticated decryption failures, AES without crypto support, and invalid URL base64 consistently.

## Non-goals
- Do not redesign advanced-upload encryption format.
- Do not expand HMAC metadata coverage in this stage unless needed to keep current claims truthful; docs are handled in STAGE-023.

## Scope
### Likely files to inspect
- `src/handlers/advanced_upload.py` — decrypt/base64/HMAC handling
- `src/security/crypto.py` — AES/XOR/no-crypto behavior
- `tests/test_handlers/test_handler_integration.py` and `tests/test_security/test_crypto.py` — crypto tests

### Likely files to change
- `src/handlers/advanced_upload.py` — return 400 on requested decrypt failure
- `src/security/crypto.py` — distinguish AES unavailable from XOR fallback
- `tests/` — wrong-key, tamper, no-crypto, strict URL-base64 regressions

### Files that must not be changed
- `uploads/**` — runtime user data; do not inspect contents unless an explicit disposable test fixture is created
- `notes/**` — encrypted runtime note data; do not inspect contents
- `.env*`, `*.key`, `*.pem`, `*.p12`, `*.pfx`, credential JSON — secret-heavy files
- `codex-analysis/**` — source analysis artifacts; read-only evidence only
- `implementation-plan/**` — planning artifacts; close-plan-stage may update status/report files only

## Dependencies
- Depends on: STAGE-012
- Blocks: STAGE-023

## Implementation steps
1. Make `decrypt_key` + failed AES-GCM authentication a request failure, not a successful ciphertext write.
2. Reject `e=aes` when `cryptography` support is unavailable instead of falling through to XOR output.
3. Use strict URL-safe base64 validation for URL transport.
4. Add tests for wrong key, tampered ciphertext, no-crypto AES, and malformed URL base64.

## Acceptance criteria
- [ ] Wrong-key/tampered AES-GCM uploads return 400 and do not write ciphertext as success.
- [ ] `e=aes` without crypto support fails clearly.
- [ ] URL base64 validation behavior matches header/body strictness.
- [ ] Existing valid XOR/AES/HMAC upload tests still pass.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `pytest tests/test_handlers/test_handler_integration.py tests/test_security/test_crypto.py -q` | Advanced upload crypto tests pass |
| Type/lint/build | `python -m compileall src tests` | Compilation succeeds |
| Manual/static review | Inspect `decrypt()` call sites | No requested-authenticated decrypt failure is treated as success |

## Suggested subagents
- `security-auditor` — fail-closed review.
- `qa-expert` — optional dependency/no-crypto coverage.

## Risks and rollback
- Risk: Clients relying on best-effort ciphertext storage will now receive errors.
- Rollback: Revert advanced-upload crypto handling and tests for this stage.

## Completion notes
Filled by `close-plan-stage`.
