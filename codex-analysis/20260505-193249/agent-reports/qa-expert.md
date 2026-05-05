# qa-expert Report
_Generated: 2026-05-05 20:04:00 Europe/Moscow_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260505-193249/analysis-plan.md_

## Summary

Scope analyzed: `tests/`, `pyproject.toml`, `.github/workflows/ci.yml`, `.pre-commit-config.yaml`, `constraints/ci.txt`, `tools/browser_smoke.py`, `tools/browser_smoke.playwright.js`, ignored `tools/close_plan_stages.py` / `tests/test_close_plan_stages.py`, plus affected CLI/TLS/notepad source and `examples/notepad_client.py`.

Validated read-only: `.venv/bin/python -m pytest --collect-only -q -p no:cacheprovider` collected 637 tests and did include ignored `tests/test_close_plan_stages.py`. Full pytest/browser smoke/live ACME were not run.

## Documentation Checks

No additional Context7 lookup was needed. Parent already checked cryptography, Certbot ACME, and pytest. Local environment confirmed pytest `9.0.3` via collect-only output.

## Detailed Findings

1. Local pytest collects ignored tests that CI will not see.
Evidence: `pyproject.toml:96-99` collects `tests/test_*.py`; `.gitignore:63-64` ignores `tools/close_plan_stages.py` and `tests/test_close_plan_stages.py`; `git ls-files` returned no tracked entries for either file. Collect-only included `<Module test_close_plan_stages.py>` and its 20 tests. CI runs from checkout and `pytest --cov=src...` at `.github/workflows/ci.yml:26,51-52`, so these local-only tests are absent there.

2. Notepad example HKDF mismatch is confirmed and not regression-tested.
Evidence: `examples/notepad_client.py:118-123` uses `salt=None` and `info=b"exphttp-notepad"`, while server uses `_HKDF_SALT = b"\x00" * 32`, `_HKDF_INFO = b"notepad-e2e-key"` in `src/security/keys.py:41-42` and derives with those constants at `src/security/keys.py:135-140`. Browser UI matches server at `src/data/static/ui/notepad.js:501-507`. CI only runs `python examples/notepad_client.py --help` at `.github/workflows/ci.yml:163`; no example round-trip exists.

3. ACME tests are useful but over-mocked for issuance behavior.
Evidence: `tests/test_security/test_tls.py:250-292` monkeypatches `_acme_client_for_key`, `_ensure_account`, `_http01_challenges`, and `_challenge_server`. This covers local orchestration, paths, write modes, invalid domains, and bind errors, but not real ClientV2/order/challenge behavior. No CI job exercises live ACME or staging issuance.

4. ACME fresh cert + missing key lacks regression coverage.
Evidence: `src/security/tls_manager.py:109-135` reuses a fresh `fullchain.pem` based only on cert freshness, then sets `key_file` to `privkey.pem`; `_build_context` loads both at `src/security/tls_manager.py:148-152`. Existing tests cover existing cert+key (`tests/test_security/test_tls_manager.py:112-145`), renewal (`:146-180`), and legacy cert+key (`:181-214`), but not fresh cert with absent key.

5. CLI lower-bound validation is missing.
Evidence: `src/cli.py:44-46`, `:72-85` parse `--port`, `--max-size`, and `--workers` as plain ints. Validation only checks ACME combinations and `--acme-http-port` at `src/cli.py:175-182`. `tests/test_cli.py:298-310` only rejects invalid ACME combinations. Runtime parser checks confirmed `-p 0 -m 0 -w 0` and negative values are accepted.

6. Stale `exphttp[crypto]` strings are still locked into tests/UI.
Evidence: runtime errors still mention it at `src/request_pipeline.py:208-212` and `src/handlers/notepad.py:38-40`; UI strings at `src/data/static/ui/core.js:257,277,552,572`; browser smoke expects those exact stale strings at `tools/browser_smoke.playwright.js:2677-2680`. `[crypto]` is empty in `pyproject.toml:49-50`.

7. UI redaction coverage is targeted, not broad.
Evidence: inspector redaction tests cover advanced upload and notepad secrets at `tests/test_ui_inspector_redaction.py:192-245`. The UI still has many `innerHTML` sinks, including `src/data/static/ui/files.js:155`, `upload.js:199,376`, `requests.js:1112,1472,1478,1493,1523,2044`, `notepad.js:184,755,767`, and `inspector.js:462`. No confirmed XSS defect found in this read-only pass, but coverage is not systematic across file names, note titles, request paths, and response summaries.

## Issues Found

- [MEDIUM] Local confidence can diverge from CI because ignored `tests/test_close_plan_stages.py` is collected locally but absent from tracked CI checkout.
- [MEDIUM] `examples/notepad_client.py` likely cannot interoperate with current Secure Notepad encryption due HKDF mismatch, and CI only verifies `--help`.
- [MEDIUM] ACME cached certificate reuse can proceed with a missing private key, failing later at SSL context load instead of renewing/recovering.
- [MEDIUM] CLI accepts invalid zero/negative `--port`, `--max-size`, and `--workers`, shifting user-facing failures to lower-level socket/thread/runtime errors.
- [LOW] Stale `exphttp[crypto]` guidance remains in runtime/UI copy, and browser smoke currently preserves it.

## Concrete Recommendations

1. Decide whether `tools/close_plan_stages.py` is project code. If yes, track both tool and tests. If no, move the ignored test out of `tests/test_*.py` or add an explicit pytest ignore so local and CI collection match.

2. Add a functional example regression: start a temp live server, run `examples/notepad_client.py --url ... --title ... --text ...`, and assert the output includes the decrypted text. This will catch the HKDF mismatch.

3. Add `TLSManager` tests for fresh `fullchain.pem` with missing `privkey.pem`, missing cert with existing key, and invalid fresh cert. Expected behavior should be renew or fail early with actionable error.

4. Add CLI validation and tests for `--port` range `1..65535`, `--max-size >= 1`, and `--workers >= 1`.

5. Update stale `exphttp[crypto]` copy and adjust browser smoke assertions to the new message.

6. Add a small UI injection/redaction matrix for file names, note titles, request paths, and inspector summaries using payloads like `<img src=x onerror=...>` and advanced-upload secret fields.

## Quick Wins

- Add `tests/test_cli.py` parametrized invalid lower-bound cases.
- Add one notepad example live subprocess test.
- Add one `test_try_letsencrypt_renews_when_cached_key_missing`.
- Remove `exphttp[crypto]` from runtime/UI messages and browser smoke expected strings.
- Align pre-commit deps: `.pre-commit-config.yaml:21-27` pins only `cryptography==46.0.5`, while runtime deps are `acme>=5.5,<6`, `cryptography>=48.0` in `pyproject.toml:37-40`.

## Deeper Improvements

- Add an opt-in manual ACME staging workflow gated by env secrets/domain and explicit operator trigger; keep it out of default PR CI.
- Split browser smoke into smaller named flows so inspector redaction failures point to a specific surface.
- Add CI collection diff guard: compare `pytest --collect-only` output against tracked files, or fail if ignored `tests/test_*.py` exists.

## Open Questions

- Are `tools/close_plan_stages.py` and `tests/test_close_plan_stages.py` intended local-only agent tooling or project-supported tooling?
- Should `[crypto]` remain visible anywhere, or only stay as a silent compatibility extra?
- Is live ACME staging acceptable as a manual release gate with required domain/port-80 infrastructure?
