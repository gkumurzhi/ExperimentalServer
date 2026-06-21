# STAGE-006 - SMUGGLE temp-control config clarity

## Status
CLOSED

## Priority
MEDIUM

## Source findings
- `codex-analysis/20260621-150449/agent-reports/qa-expert.md` - `smuggle_temp_*` knobs are not covered through settings precedence tests
- `codex-analysis/20260621-150449/agent-reports/cli-developer.md` - `--print-config` can make effective TLS look disabled in `sslip` or ACME flows
- `codex-analysis/20260621-150449/project-analysis-report.md` - retention/config clarity is part of the safe future work

## Goal
Make the operator-facing temp-artifact configuration path easier to trust by covering precedence for `smuggle_temp_*` knobs and clarifying how validated public-direct/TLS-related settings should be interpreted.

## Non-goals
- Changing the default profile or making `lab` eligible for `public_direct`
- Reworking the entire config schema
- Expanding `SMUGGLE` retention controls beyond the existing settings surface

## Scope
### Likely files to inspect
- `src/settings.py` - source maps, redacted output, and runtime kwargs
- `tests/test_settings.py` - existing precedence coverage
- `tests/test_cli.py` - help and config-output expectations
- `deploy/docker/exphttp.ini.example` and `deploy/systemd/exphttp.ini.example` - sample public-direct/operator comments

### Likely files to change
- `tests/test_settings.py` - add INI/env/CLI precedence coverage for `smuggle_temp_*`
- `src/settings.py` - only if a minimal additive clarification is needed for config output
- `tests/test_cli.py` - update output expectations if the operator-facing output changes
- `deploy/docker/exphttp.ini.example` and `deploy/systemd/exphttp.ini.example` - clarify safe profile/public-direct expectations in comments

### Files that must not be changed
- `src/features.py` - capability policy is not part of this stage
- `src/data/` - no frontend work here
- `README.md` - framing work belongs to STAGE-003 unless a small cross-reference is strictly required

## Dependencies
- Depends on: `STAGE-003`
- Blocks: `None`

## Implementation steps
1. Extend settings precedence coverage so `smuggle_temp_age`, `smuggle_temp_file_limit`, and `smuggle_temp_storage_limit_mb` are pinned through config/env/CLI resolution.
2. Decide whether the `--print-config` confusion is best solved by documentation/sample comments or by a small additive output clarification.
3. Update the minimum code, tests, and sample comments needed so operators can understand the validated public-direct/TLS path without widening behavior.

## Acceptance criteria
- [x] Settings precedence tests cover the `smuggle_temp_*` knobs through INI, environment, and CLI resolution
- [x] Operators have a clear explanation for why validated `sslip` or ACME configs may still show `"tls": false` in normalized output, or an additive output field makes the runtime TLS state explicit
- [x] Deployment samples continue to validate and keep `lab` out of the public-direct path

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Targeted tests | `./.venv/bin/pytest -q tests/test_settings.py tests/test_cli.py tests/test_deployment_artifacts.py` | PASS with updated settings and sample-config expectations |
| Type/lint/build | `python -m exphttp --check-config`; `python -m exphttp --config deploy/docker/exphttp.ini.example --check-config`; `python -m exphttp --config deploy/systemd/exphttp.ini.example --check-config` | PASS with no config-validation regressions |
| Manual/static review | Review `--print-config` or sample comments against the public-direct docs | Output/comments explain runtime TLS/public-direct behavior accurately |

## Suggested subagents
- `explorer` - map the current settings precedence and output path for the temp-artifact knobs
- `worker` - implement the narrow test and config-output/sample changes

## Risks and rollback
- Risk: adding output fields or comments can unintentionally become a compatibility promise
- Rollback: revert the output change and keep the safe precedence tests plus sample-comment clarifications

## Completion notes
- Closed on `2026-06-21 18:34:00 +0300`; report: `stage-reports/STAGE-006-20260621-183400.md`.
- Added settings/CLI regression coverage for `smuggle_temp_*` precedence and for `effective_tls` in `--print-config`.
- `ServerSettings.to_redacted_dict()` now reports `effective_tls`, while sample/deploy configs explain that public-direct stays on `workspace`/`serve` and TLS can become active through `sslip`/ACME without the raw `tls` flag.
