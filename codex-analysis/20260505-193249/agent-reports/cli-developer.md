# cli-developer Report
_Generated: 2026-05-05 19:58:00 Europe/Moscow_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260505-193249/analysis-plan.md_

## Summary

Read-only CLI developer pass completed for `exphttp`.

Workflow/tool boundary analyzed: `exphttp` / `python -m src` argument parsing in `src/cli.py`, handoff into `ExperimentalHTTPServer` in `src/server.py`, TLS/ACME lifecycle in `src/security/tls_manager.py`, and matching README/tests/docs coverage.

Primary friction source: CLI validation is inconsistent. ACME-specific checks use `parser.error()` and exit cleanly with code `2`, but core runtime-affecting flags and several TLS source combinations are accepted until lower layers fail, get ignored, or start with surprising behavior.

Validation performed:
- Normal path: `python -m src --help` via `.venv` succeeds and shows current CLI help.
- Failure path: `--acme-http-port 0` and `--letsencrypt` fail early with argparse exit code `2`.
- Edge path: parser accepts `--port 0`, `--port -1`, `--max-size 0`, `--max-size -5`, `--workers 0`, `--workers -2`; `ThreadPoolExecutor(max_workers=0)` raises `ValueError`; `socket.bind()` rejects ports outside `0-65535`.

## Documentation Checks

- **Python / CPython** `v3.13.9` - Context7 topic checked: `argparse` custom `type` callables and invalid argument handling; impact on recommendation: range validation can be implemented at parse time with `ArgumentTypeError` / `parser.error()`, preserving the existing automation-friendly argparse failure contract.
- **Python / CPython** `v3.13.9` - Context7 topic checked: `ThreadPoolExecutor` usage patterns; impact on recommendation: `max_workers` must be treated as a positive runtime invariant before `server.start()` reaches executor creation.

## Detailed Findings

The CLI already has a useful validation pattern at `src/cli.py:175-182`: invalid ACME combinations and out-of-range `--acme-http-port` fail before server construction.

That pattern is not applied to the rest of the flags. `--port`, `--max-size`, and `--workers` are plain `type=int` arguments at `src/cli.py:45`, `src/cli.py:72-85`, then are copied directly into runtime config at `src/cli.py:187-190`.

TLS source selection is also not normalized at the CLI boundary. `--cert` enables TLS because `config["tls"]` includes `bool(args.cert)`, but `--key` alone does not because `bool(args.key)` is omitted at `src/cli.py:193`. `TLSManager.setup()` only checks cert/key pairing after `enabled` is true at `src/security/tls_manager.py:71-74`, so key-only input can be ignored.

Docs mostly reflect available flags, but there is drift: CLI help omits several supported methods, and ADR-005 names a non-existent `--max-workers` flag.

## Issues Found

- [MEDIUM] Core numeric flags accept invalid or nonsensical values
  - File/area: `src/cli.py`, `src/server.py`, `src/http/io.py`, `tests/test_cli.py`
  - Evidence: `--port`, `--max-size`, and `--workers` use only `type=int` at `src/cli.py:45`, `src/cli.py:72-85`; only `--acme-http-port` has range validation at `src/cli.py:181-182`; config passes values through at `src/cli.py:187-190`.
  - Detail: `--workers 0` reaches `ThreadPoolExecutor(max_workers=self.max_workers)` at `src/server.py:390`, which raises `ValueError`. Invalid ports reach `sock.bind((self.host, self.port))` at `src/server.py:356`. Negative `--max-size` becomes a negative byte cap at `src/cli.py:189`, then `receive_request()` drops requests because `content_length > max_upload_size` at `src/http/io.py:116-122`.
  - Impact: Users get late exit code `1` and raw lower-layer errors instead of argparse exit code `2`; `--max-size <= 0` can make uploads or even ordinary requests fail unpredictably; `--port 0` binds an ephemeral port but `server.start()` still prints `:0` from `self.port`.
  - Confidence: high

- [MEDIUM] `--key` without `--cert` can be silently ignored and start plaintext HTTP
  - File/area: `src/cli.py`, `src/security/tls_manager.py`
  - Evidence: TLS activation is `args.tls or bool(args.cert) or args.letsencrypt or args.sslip` at `src/cli.py:193`, excluding `args.key`; `key_file` is still passed at `src/cli.py:195`; `TLSManager.setup()` returns immediately when disabled at `src/security/tls_manager.py:71-72`.
  - Detail: `--cert` alone eventually fails in `TLSManager.setup()` with `--cert and --key must be provided together`, but `--key` alone does not enable TLS and bypasses that pairing check.
  - Impact: A typo or omitted cert can run a plaintext server even though the operator supplied TLS material.
  - Confidence: high

- [MEDIUM] User-supplied cert/key can be combined with ACME modes, with unclear precedence
  - File/area: `src/cli.py`, `src/security/tls_manager.py`, `tests/test_security/test_tls_manager.py`
  - Evidence: `main()` does not reject `--cert/--key` with `--letsencrypt` or `--sslip`; `TLSManager.setup()` runs `_try_letsencrypt()` when ACME is requested at `src/security/tls_manager.py:79-82`; `_try_letsencrypt()` overwrites `self.cert_file` and `self.key_file` at `src/security/tls_manager.py:134-135`.
  - Detail: If both certificate sources are supplied, ACME wins silently. If ACME fails, the provided cert/key are not used as fallback. The existing test at `tests/test_security/test_tls_manager.py:97-108` checks `describe()` before setup, not actual setup precedence.
  - Impact: Operators can unintentionally trigger ACME network calls, port-80 challenge binding, or rate limits while thinking their local cert/key will be used.
  - Confidence: high

- [LOW] ACME-scoped flags are accepted without an ACME mode and then ignored
  - File/area: `src/cli.py`, `src/security/tls_manager.py`
  - Evidence: `--public-ip` requires `--sslip` at `src/cli.py:179-180`, but `--domain`, `--email`, `--acme-staging`, `--acme-server`, and `--acme-http-address` have no equivalent mode check. TLS is not enabled by these flags at `src/cli.py:193`.
  - Detail: `--email ops@example.com` or `--domain example.com` alone starts non-TLS HTTP. ACME settings are only consumed if `_try_letsencrypt()` runs.
  - Impact: Missed `--letsencrypt` / `--sslip` typos can produce a successful but wrong server mode.
  - Confidence: high

- [LOW] CLI help and docs drift from actual command surface
  - File/area: `src/cli.py`, `src/handlers/__init__.py`, `README.md`, `docs/ADR/ADR-005-threadpool-over-asyncio.md`
  - Evidence: CLI epilog lists only `FETCH, INFO, PING, NONE, SMUGGLE` plus some standard methods at `src/cli.py:32-33`; actual registry includes `GET`, `HEAD`, `POST`, `PUT`, `PATCH`, `DELETE`, `OPTIONS`, `FETCH`, `INFO`, `PING`, `NONE`, `NOTE`, `SMUGGLE` at `src/handlers/__init__.py:38-50`; README lists the full set at `README.md:38`; ADR-005 says pool size is tunable via `--max-workers` at `docs/ADR/ADR-005-threadpool-over-asyncio.md:24`, but the CLI flag is `--workers`.
  - Impact: Discoverability is worse for operators using `--help`, and contributor docs name a flag that does not exist.
  - Confidence: high

## Concrete Recommendations

Add CLI-level validators for bounded positive integers:
- `--port`: `1..65535`, unless the project intentionally supports ephemeral `0`.
- `--acme-http-port`: reuse the same validator.
- `--max-size`: `>= 1` MB.
- `--workers`: `>= 1`.

Use `argparse.ArgumentTypeError` or `parser.error()` so invalid operator input keeps the existing usage output and exit code `2`.

Add explicit post-parse TLS source validation:
- Reject exactly one of `--cert` / `--key`.
- Reject `--cert/--key` combined with `--letsencrypt` or `--sslip`, unless a documented precedence is intentionally kept.
- Reject or clearly warn on ACME-only flags without `--letsencrypt` or `--sslip`.

Add lower-layer constructor guards for library users too:
- `ExperimentalHTTPServer.__init__()` should reject invalid `port`, `max_upload_size`, and `max_workers` before sockets, directories, TLS, or cleanup-sensitive setup.

## Quick Wins

- Add `tests/test_cli.py` parametrized cases for invalid `--port`, `--max-size`, `--workers`, and cert/key pairing.
- Add tests that `--key` alone exits with code `2`.
- Add tests that `--cert --key --letsencrypt --domain ...` is rejected or follows a documented precedence.
- Fix ADR-005 from `--max-workers` to `--workers`.
- Update CLI epilog to include `HEAD`, `PATCH`, `DELETE`, and `NOTE`, or avoid hardcoding the method list there.

## Deeper Improvements

- Introduce one small CLI validation helper section in `src/cli.py` so flag rules are centralized and easy to test.
- Consider a typed config object shared by CLI and library initialization, but only if more config sources are added later.
- Decide whether `--port 0` is supported. If yes, `server.start()` should print the actual bound port from `sock.getsockname()`; if no, reject it like `--acme-http-port 0`.

## Open Questions

- Should ACME mode with default `--host 127.0.0.1` warn? README examples imply public binding for `--sslip`, but the CLI allows `exphttp --sslip` to advertise a public sslip hostname while the HTTPS server binds localhost.
- Should `--acme-server` plus `--acme-staging` remain allowed with "server overrides staging," or should it be rejected for clarity?
- Should `--domain` alone be rejected, or reserved for a future non-ACME TLS hostname feature?
