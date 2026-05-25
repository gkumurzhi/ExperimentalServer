# STAGE-005 - Auth secret files and auth invariants

## Status
CLOSED

## Priority
HIGH

## Source findings
- `codex-analysis/20260525-121051/project-analysis-report.md` - Critical & High Issues #4: Basic Auth service/container secrets are argv-only.
- `codex-analysis/20260525-121051/agent-reports/security-auditor.md` - HIGH argv-only auth secrets and proxy-rate-limit caveat.
- `codex-analysis/20260525-121051/agent-reports/docker-expert.md` - HIGH container secret issue; recommends `--auth-file /run/secrets/exphttp_auth`.
- `codex-analysis/20260525-121051/agent-reports/architect-reviewer.md` - MEDIUM auth mutation issue: documented post-init authenticator assignment loses rate-limiter invariant.

## Goal
Add a safe non-argv Basic Auth secret source and repair documented auth configuration so authenticator changes preserve rate-limiter invariants.

## Non-goals
- Multi-user or role-based authorization.
- Trusted reverse-proxy IP parsing.
- Feature profiles; covered by STAGE-006.

## Scope
### Likely files to inspect
- `src/cli.py` - auth CLI parsing and server config creation.
- `src/server.py` - auth parsing, `random` behavior, `_rate_limiter` setup.
- `src/security/auth.py` - authenticator and rate limiter types.
- `tests/test_cli.py` - CLI behavior tests.
- `tests/test_security/test_auth.py` - auth helper tests.
- `README.md`, `SECURITY.md`, `examples/docker/docker-compose.yml` - auth examples.

### Likely files to change
- `src/cli.py` - add `--auth-file` and precedence/failure handling.
- `src/server.py` - parse auth file contents without logging secrets; add constructor injection or `set_authenticator()`.
- `tests/` - add secret file, missing/unreadable/invalid, newline trimming, precedence, and redaction tests.
- `README.md`, `SECURITY.md`, `examples/docker/docker-compose.yml` - replace inline service/container credential examples with secret file guidance.

### Files that must not be changed
- Real `.env`, secret, key, certificate, or token files - do not inspect or create real secrets.
- Existing auth hash algorithms unless needed for test injection.

## Dependencies
- Depends on: `None`
- Blocks: STAGE-006, STAGE-008

## Implementation steps
1. Add `--auth-file PATH` that reads one `user:password` value from a mounted file with newline trimming.
2. Define and test precedence if both `--auth` and `--auth-file` are provided; prefer failing closed unless a clear existing CLI pattern supports precedence.
3. Ensure missing, unreadable, empty, and malformed files produce non-secret error messages.
4. Update non-interactive service guidance away from inline `--auth user:password`.
5. Replace documented post-init authenticator mutation with constructor injection or `set_authenticator()` that refreshes rate limiting.
6. Add tests proving secrets do not appear in stdout/stderr/log output on failure paths.

## Acceptance criteria
- [x] Service/container deployments can configure Basic Auth from a file path without passing the password in argv.
- [x] Auth-file parsing handles newline trimming and rejects malformed or empty files safely.
- [x] Error output and docs do not expose secret contents.
- [x] README custom-auth guidance preserves auth rate-limiter invariants.
- [x] Existing `--auth random` and explicit `--auth user:pass` behavior remains tested.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `python -m pytest tests/test_cli.py tests/test_security/test_auth.py tests/test_request_pipeline.py` | CLI, auth, and pipeline auth tests pass with new secret-file cases |
| Type/lint/build | `ruff check src tests && ruff format --check src tests && mypy src` | No lint, format, or type regressions |
| Manual/static review | Search docs/examples for inline service secrets | Service/container examples prefer `--auth-file`; any inline examples are local-only and warn about argv leakage |

## Suggested subagents
- `explorer` - map current auth config flow and tests.
- `worker` - implement `--auth-file` and invariant-safe auth setter.
- `qa` - add failure/redaction tests.

## Risks and rollback
- Risk: Ambiguous precedence between `--auth` and `--auth-file` could surprise users.
- Rollback: Fail when both are provided and document that behavior; this is safest and easy to reason about.

## Completion notes
Closed 2026-05-25 18:41:08 MSK.

- Added CLI/server `--auth-file` support with fail-closed `--auth` conflict handling.
- Auth-file parsing reads one UTF-8 `user:password` line, trims one trailing newline, and rejects empty, malformed, multiline, invalid UTF-8, missing, and unreadable files without echoing secrets.
- Added `ExperimentalHTTPServer.set_authenticator()` and updated README custom-auth guidance so rate limiting remains synchronized.
- Updated service/container/CI docs and Docker Compose examples to prefer `--auth-file`.
- Verification passed: targeted CLI/auth/request-pipeline tests, stale-doc guard, compose config, ruff check, ruff format check, and mypy via isolated uv lint environment.
- Report: `stage-reports/STAGE-005-20260525-181754.md`.
