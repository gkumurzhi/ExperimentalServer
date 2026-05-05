# python-pro Report
_Generated: 2026-05-05 19:59:20 Europe/Moscow_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260505-193249/analysis-plan.md_

## Summary

Read-only analysis completed. I did not write files.

Execution boundary analyzed: `exphttp = src.cli:main`, `python -m src`, package import via `src.__init__`, TLS/ACME setup in `src/security/tls.py` and `src/security/tls_manager.py`, request framing in `src/http/io.py`, request parsing in `src/http/request.py`, worker lifecycle in `src/server.py`, and note persistence in `src/notepad_service.py`.

Main risks are tooling/runtime dependency drift, missing CLI bounds, recoverable ACME cache states that fail late, and non-atomic user-data writes.

## Documentation Checks
- **pre-commit** `4.6.0 constrained / hook rev v1.20.1 mypy mirror` - Context7 topic checked: isolated hook environments and `additional_dependencies`; impact on recommendation: the mypy hook must install the packages imported by `src/`, not rely on the developer environment.
- **mypy** `1.20.1` - Context7 topic checked: missing imports/stubs under strict checking; impact on recommendation: missing third-party imports should be fixed by installing deps/stubs in the type-check environment, not by broad `ignore_missing_imports`.
- **cryptography** `>=48.0 declared` - Context7 topic checked: RSA private-key PEM serialization, X.509 `CertificateBuilder`, timezone-aware cert validity accessors; impact on recommendation: current serialization and `not_valid_after_utc` usage are API-compatible, but local/runtime environments must actually satisfy the declared lower bound.
- **Certbot acme** `5.5.0` - Context7 topic carried from source plan: `ClientV2`, account/order flow, HTTP-01 standalone challenge behavior; impact on recommendation: ACME review should focus on key/cache recovery and live port-80/domain validation beyond mocks.

## Detailed Findings

The current build metadata is mostly safe by accident: `pyproject.toml:73-74` reads `src.config.__version__`, and `src/config.py:6` is a literal. I verified setuptools can read it statically without importing `src.__init__`. However, the public import boundary is heavy: `src/__init__.py:10-22` imports security and server modules, `src/security/__init__.py:29-34` imports `src/security/tls.py`, and `src/security/tls.py:25-31` imports `acme`, `cryptography`, and `josepy` at module import time.

Direct local validation showed the active interpreter cannot import the package:

`import src` fails with `ModuleNotFoundError: No module named 'acme'`. `pip show acme` and `pip show josepy` found nothing, and `pip show cryptography` reports `41.0.7`, below `cryptography>=48.0`.

## Issues Found

- [MEDIUM] Pre-commit mypy environment is incompatible with the runtime import boundary
  - File/area: `.pre-commit-config.yaml`, `pyproject.toml`, `constraints/ci.txt`, `src/security/tls.py`
  - Evidence: `pyproject.toml:37-40` declares `acme>=5.5,<6` and `cryptography>=48.0`; `constraints/ci.txt:4,18,29,42` pins `acme==5.5.0`, `cryptography==48.0.0`, `josepy==2.2.0`, `mypy==1.20.1`; `.pre-commit-config.yaml:21-28` installs only `cryptography==46.0.5` for mypy; `src/security/tls.py:25-31` imports `acme`, `cryptography`, and `josepy` at top level.
  - Detail: pre-commit hooks run in isolated environments. The configured mypy hook lacks `acme` and `josepy`, and pins `cryptography` below the project lower bound. Since `src.__init__` reaches `src.security.tls` during normal package import, type checking `src/` can fail before meaningful type analysis.
  - Impact: local pre-commit can fail differently from CI, or developers may "fix" missing imports by suppressing checks. The active local interpreter already reproduces the import failure for `acme`.
  - Confidence: high

- [MEDIUM] CLI accepts invalid primary limits and defers failures to lower layers
  - File/area: `src/cli.py`, `src/server.py`, `src/http/io.py`, `tests/test_cli.py`
  - Evidence: `src/cli.py:44-46`, `src/cli.py:71-86` use plain `type=int` for `--port`, `--max-size`, and `--workers`; only `--acme-http-port` is range-checked at `src/cli.py:181-182`; config passes raw values at `src/cli.py:187-190`; `ThreadPoolExecutor(max_workers=self.max_workers)` is created at `src/server.py:390`; request receive uses `max_upload_size` at `src/http/io.py:100-122`; tests cover ACME invalid ports at `tests/test_cli.py:298-310` but not invalid primary port/workers/max-size.
  - Detail: `--workers 0` or negative values fail late when the executor is created. Negative `--max-size` becomes a negative byte cap, causing request reads to drop normal traffic or later produce misleading 413 behavior. Invalid `--port` values fail at socket bind instead of parser validation.
  - Impact: users get late, less actionable startup/runtime errors; some configurations can start setup side effects before failing.
  - Confidence: high

- [MEDIUM] TLSManager reuses a fresh ACME certificate without verifying the key file
  - File/area: `src/security/tls_manager.py`
  - Evidence: `_try_letsencrypt()` computes `cert_path` and `key_path` at `src/security/tls_manager.py:99-101`; the reuse branch checks only `cert_path.exists()` and `check_cert_needs_renewal(cert_path)` at `src/security/tls_manager.py:109-132`; it then assigns both paths at `src/security/tls_manager.py:134-135`; tests only cover the happy reuse case with both files present at `tests/test_security/test_tls_manager.py:112-144`.
  - Detail: if `fullchain.pem` exists and is fresh but `privkey.pem` is missing, unreadable, or unrelated, the manager skips renewal and fails later in `context.load_cert_chain()` at `src/security/tls_manager.py:151`.
  - Impact: a recoverable cache-miss state becomes a startup failure instead of triggering renewal or clear diagnostics.
  - Confidence: high

- [MEDIUM] Upload writes are non-exclusive and can overwrite under concurrent requests
  - File/area: `src/handlers/files.py`, `src/handlers/advanced_upload.py`
  - Evidence: regular uploads choose a unique path then open with `"wb"` at `src/handlers/files.py:409-415`; advanced uploads check existence and then open with `"wb"` at `src/handlers/advanced_upload.py:367-386`; server concurrency is a `ThreadPoolExecutor` at `src/server.py:390`.
  - Detail: uniqueness is checked before opening, but the final file is not reserved with exclusive creation. Two workers uploading the same user-supplied name can both observe the path as free and then truncate/write the same destination.
  - Impact: user uploads can be lost or corrupted under concurrent traffic. Crash/interruption can also leave partial files.
  - Confidence: medium

- [MEDIUM] Secure Notepad save is not atomic across ciphertext and metadata sidecar
  - File/area: `src/notepad_service.py`
  - Evidence: `save_note()` writes the encrypted blob, then writes metadata directly at `src/notepad_service.py:204-210`; tests assert files exist after success at `tests/test_handlers/test_notepad.py:142-157` but do not simulate write failure between the two files.
  - Detail: `enc_path.write_bytes()` and `meta_path.write_text()` truncate/replace files in place. If metadata write fails after ciphertext write, the method returns a 500 but leaves a new or updated ciphertext on disk with missing/stale/corrupt metadata.
  - Impact: clients can see failed saves that partially persist; updates can pair new ciphertext with old metadata.
  - Confidence: high

- [LOW] Connection-level exceptions are swallowed without observability
  - File/area: `src/server.py`
  - Evidence: `_handle_client()` catches `Exception` and `pass` at `src/server.py:467-468`; WebSocket send-close paths similarly swallow send failures at `src/server.py:697-701` and `src/handlers/notepad.py:366-369`.
  - Detail: request-level failures are logged in `RequestPipeline.process()` at `src/request_pipeline.py:159-166`, but exceptions outside that boundary disappear. Some socket send failures are expected, but unexpected worker errors should be debug-logged at minimum.
  - Impact: production debugging and metrics lose connection-level failure signals.
  - Confidence: medium

- [LOW] Crypto-required runtime error still recommends an empty extra
  - File/area: `pyproject.toml`, `src/handlers/notepad.py`, `src/request_pipeline.py`, `src/server.py`
  - Evidence: `pyproject.toml:49-50` defines `crypto = []`; runtime errors still say `install exphttp[crypto]` at `src/handlers/notepad.py:38-40` and `src/request_pipeline.py:208-212`; ECDH initialization failures are swallowed at `src/server.py:159-164`.
  - Detail: cryptography is now a required runtime dependency, so the extra is only compatibility metadata. The error text points users to a no-op remediation and hides the underlying initialization failure.
  - Impact: users cannot fix broken installs from the message, and operators get no clear startup signal when Secure Notepad is disabled.
  - Confidence: high

## Concrete Recommendations

Align `.pre-commit-config.yaml` mypy `additional_dependencies` with runtime imports: include `acme==5.5.0`, `josepy==2.2.0`, and `cryptography==48.0.0` or reuse the same constraints strategy as CI.

Add parser-level validation in `src/cli.py`: primary `--port` should match the intended contract, likely `1..65535`; `--workers` should be `>=1`; `--max-size` should be `>=1` MB unless zero has a documented meaning.

In `TLSManager._try_letsencrypt()`, treat missing/unreadable key as cache miss. Ideally validate both files before reuse and add a regression test for fresh cert plus missing key.

For uploads, reserve final paths with exclusive creation or a shared helper that retries with a random suffix until `O_EXCL` succeeds. For notes, use same-directory temp files plus `replace()` and cleanup, with explicit tests for failure between blob and metadata writes.

Replace stale `exphttp[crypto]` runtime guidance with a required-dependency reinstall message, and log ECDH initialization failure at warning/debug level with exception context.

## Quick Wins

- Add CLI validation tests beside `tests/test_cli.py:298-310`.
- Add a TLSManager test for fresh `fullchain.pem` with missing `privkey.pem`.
- Update the two `install exphttp[crypto]` strings.
- Update pre-commit mypy deps to match `constraints/ci.txt`.

## Deeper Improvements

- Make `src.__init__` lighter by avoiding eager TLS/ACME imports for simple metadata imports.
- Introduce one shared atomic/exclusive write helper for uploads, notes, and TLS cache writes.
- Add a no-write import/build smoke in CI that verifies metadata preparation and `python -m src --version` in a clean installed environment.
- Add one failure-injection test for note save after ciphertext write and before metadata write.

## Open Questions

- Should CLI `--port 0` be intentionally supported for ephemeral-port testing, or rejected like `--acme-http-port 0`?
- Is live ACME validation expected in CI/staging, or should the project explicitly document that ACME coverage is mock-only?
- Should `crypto = []` remain indefinitely for compatibility, or be removed in the next breaking release?

