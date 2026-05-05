# STAGE-004 - Normalize CLI TLS source and numeric validation

## Status
CLOSED

## Priority
HIGH

## Source findings
- `codex-analysis/20260505-193249/project-analysis-report.md` - Security & Compliance and Code Quality: TLS source validation and numeric lower bounds incomplete.
- `codex-analysis/20260505-193249/agent-reports/cli-developer.md` - MEDIUM: invalid numeric flags and unclear TLS source precedence.
- `codex-analysis/20260505-193249/agent-reports/python-pro.md` - MEDIUM: invalid primary limits defer failures to lower layers.
- `codex-analysis/20260505-193249/agent-reports/reviewer.md` - MEDIUM blocker: `--key` alone can start plaintext; cert/key plus ACME silently selects ACME.

## Goal
Make invalid CLI configuration fail early with argparse-style exit code `2`, and make library/server lower-bound guards reject invalid runtime values before side effects.

## Non-goals
- Do not redesign the full config object model.
- Do not add new ACME features or cache directory options.
- Do not change valid default CLI behavior.

## Scope
### Likely files to inspect
- `src/cli.py` - argument definitions and post-parse validation.
- `src/server.py` - constructor/runtime invariants for programmatic callers.
- `src/security/tls_manager.py` - cert/key pairing and ACME precedence behavior.
- `tests/test_cli.py` - current CLI validation tests.
- `tests/test_security/test_tls_manager.py` - TLSManager precedence tests.

### Likely files to change
- `src/cli.py` - bounded integer validators and TLS source/mode validation.
- `src/server.py` - lower-layer guards for `port`, `max_upload_size`, and `max_workers`.
- `tests/test_cli.py` - invalid `--port`, `--max-size`, `--workers`, `--key`, cert/key plus ACME cases.
- `docs/ADR/ADR-005-threadpool-over-asyncio.md` or `README.md` - only if flag behavior/doc wording changes.

### Files that must not be changed
- `src/security/tls.py` - no ACME protocol work is needed.
- `Dockerfile` and Compose docs - container behavior is STAGE-005/STAGE-008.
- `.env*`, credentials, keys, certificates - never read or edit secrets.

## Dependencies
- Depends on: STAGE-001
- Blocks: STAGE-005, STAGE-008

## Implementation steps
1. Decide and document whether `--port 0` is supported; default recommendation is reject `0` unless actual bound-port reporting is implemented.
2. Add bounded validators for `--port`, `--acme-http-port`, `--max-size`, and `--workers`.
3. Add post-parse TLS validation for exactly-one cert/key, `--key` alone, cert/key combined with `--letsencrypt` or `--sslip`, and ACME-only flags without ACME mode if chosen.
4. Add server constructor guards for programmatic callers.
5. Add parametrized CLI tests asserting exit code `2` and useful messages.

## Acceptance criteria
- [x] `--key` alone no longer starts plaintext HTTP.
- [x] `--cert` alone and `--key` alone both fail early.
- [x] user-supplied cert/key combined with ACME mode is rejected or follows an explicitly documented behavior.
- [x] `--port`, `--max-size`, and `--workers` invalid lower/out-of-range values fail at CLI parse/validation time.
- [x] Programmatic server construction rejects invalid primary limits before sockets/thread pools are created.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted CLI tests | `pytest -q tests/test_cli.py` | Passes with invalid-argument coverage |
| TLS manager tests | `pytest -q tests/test_security/test_tls_manager.py` | Existing TLS setup behavior remains consistent |
| CLI help | `python -m src --help > /dev/null` | Exits 0 |
| Manual subprocess checks | `python -m src --key key.pem`; `python -m src --workers 0` using safe dummy paths | Exit code 2 with actionable message |

## Suggested subagents
- `explorer` - map current CLI tests and expected argparse helper patterns.
- `worker` - implement validators and tests.
- `cli-developer` - review CLI UX and compatibility.

## Risks and rollback
- Risk: Rejecting `--port 0` can break tests or users relying on ephemeral bind.
- Rollback: Revert validation changes or explicitly support `0` with actual bound-port display and tests.

## Completion notes
Closed 2026-05-05 22:22:27 MSK. Added bounded argparse validators for CLI numeric flags, explicit TLS source validation for cert/key and ACME/sslip combinations, and server constructor guards for invalid primary runtime limits before filesystem/socket side effects. Targeted CLI, TLS manager, static, subprocess, and verification subagent checks passed.
