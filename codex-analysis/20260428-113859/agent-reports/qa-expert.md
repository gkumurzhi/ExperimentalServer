# qa-expert Report
_Generated: 2026-04-28 11:58:00 MSK_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/analysis-plan.md_

## Summary

Scope analyzed: current dirty worktree in `/home/user/PycharmProjects/ExperimentalHTTPServer`, focused on `tests/`, pytest/CI/security workflows, browser smoke tooling, and the listed high-risk source paths.

No files were modified and no tests were executed. The highest-confidence risks are WebSocket client-frame masking enforcement, gzip behavior for streamed files, no-crypto AES upload behavior, and local/CI tool drift.

## Documentation Checks

- **pytest** `9.0.2 in constraints/ci.txt` — Context7 topic checked: pytest pyproject config was requested, but live Context7 returned monthly quota exhaustion. Fallback checked official pytest 9 docs: https://docs.pytest.org/en/9.0.x/reference/customize.html. Impact on recommendation: current `[tool.pytest.ini_options]` is still supported; native `[tool.pytest]` is optional, not required.

## Detailed Findings

The test suite has broad coverage for request smuggling, `Transfer-Encoding` rejection, advanced upload transports, TLS manager control flow, ECDH sessions, WebSocket size limits, and browser UI happy/unavailable paths. The gaps below are not generic coverage requests; they map to concrete implementation behavior.

Pytest config in [pyproject.toml](/home/user/PycharmProjects/ExperimentalHTTPServer/pyproject.toml:94) is sufficient for pytest 9. Moving to `[tool.pytest]` would mainly allow native TOML types such as list `addopts`; it is not a release blocker.

## Issues Found

- [MEDIUM] WebSocket server accepts unmasked client frames
  - File/area: [src/websocket.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/websocket.py:91), [src/server.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/server.py:660)
  - Evidence: `parse_ws_frame` accepts `masked == False` and returns raw payload; `_handle_notepad_ws` uses it for client frames without enforcing client masking. [tests/test_websocket.py](/home/user/PycharmProjects/ExperimentalHTTPServer/tests/test_websocket.py:286) explicitly expects unmasked frames to parse.
  - Detail: RFC client-to-server masking is treated as optional. Existing tests cover masked happy paths and oversized rejection, but not server rejection of unmasked client frames.
  - Impact: non-compliant clients can send frames the server should close, weakening protocol hardening around the notepad WebSocket path.
  - Confidence: high

- [HIGH] Gzip of streamed files can read large files fully into memory
  - File/area: [src/server.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/server.py:262)
  - Evidence: `_maybe_gzip_response` calls `response.stream_path.read_bytes()` before compression. [tests/test_server_methods.py](/home/user/PycharmProjects/ExperimentalHTTPServer/tests/test_server_methods.py:490) asserts streamed files are converted into in-memory gzip bodies.
  - Detail: default uploads can be large, and `max_workers` defaults to 10. Concurrent gzip downloads of large text files can multiply memory use quickly.
  - Impact: user-visible latency or OOM under large/compressible downloads.
  - Confidence: high

- [MEDIUM] No-crypto AES advanced upload can silently store corrupted output
  - File/area: [src/security/crypto.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/security/crypto.py:147), [src/handlers/advanced_upload.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/advanced_upload.py:224)
  - Evidence: if `HAS_CRYPTOGRAPHY` is false, `decrypt()` falls through to XOR even for AES-versioned bytes. `handle_advanced_upload` replaces `file_data` whenever decrypt returns bytes. AES tests are skipped without crypto in [tests/test_security/test_crypto.py](/home/user/PycharmProjects/ExperimentalHTTPServer/tests/test_security/test_crypto.py:194), and CI installs `.[crypto,...]` in [ci.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/.github/workflows/ci.yml:40).
  - Detail: simulated no-ECDH paths are covered, but an actual no-cryptography install is not.
  - Impact: basic installs receiving `e=aes` payloads may write garbage instead of rejecting or preserving ciphertext.
  - Confidence: high

- [MEDIUM] Pre-commit tool versions lag behind CI constraints
  - File/area: [.pre-commit-config.yaml](/home/user/PycharmProjects/ExperimentalHTTPServer/.pre-commit-config.yaml:14), [constraints/ci.txt](/home/user/PycharmProjects/ExperimentalHTTPServer/constraints/ci.txt:37)
  - Evidence: pre-commit uses Ruff `v0.9.0` and mypy `v1.14.0`; CI constraints pin Ruff `0.15.5` and mypy `1.20.1`.
  - Detail: CI runs constrained tools, while local pre-commit can apply older fixes and miss newer diagnostics.
  - Impact: contributors can pass pre-commit locally and fail CI.
  - Confidence: high

- [LOW] Browser smoke depends on floating Playwright CLI packages
  - File/area: [ci.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/.github/workflows/ci.yml:153), [tools/browser_smoke.py](/home/user/PycharmProjects/ExperimentalHTTPServer/tools/browser_smoke.py:81)
  - Evidence: CI runs `npx --yes playwright install`; smoke fallback runs `npx --yes --package @playwright/cli playwright-cli`, both unpinned.
  - Detail: the command name is valid, but the package version can drift independently from Python constraints.
  - Impact: release smoke can fail due to upstream CLI/browser changes unrelated to repo changes.
  - Confidence: medium

## Concrete Recommendations

1. Add a failing regression test for an unmasked client frame reaching `_handle_notepad_ws`, then close with protocol error `1002`. Keep unmasked parsing only for server-frame test helpers or add a `require_mask=True` parser mode.

2. Stop gzip-compressing streamed files unless a size cap or true streaming gzip implementation is added. Minimum fix: skip gzip when `response.stream_path` exceeds a small threshold and keep streaming semantics.

3. In advanced upload, reject `e=aes` when `HAS_CRYPTOGRAPHY` is false. Add a monkeypatch-based unit test plus one no-crypto CI smoke job.

4. Align `.pre-commit-config.yaml` with `constraints/ci.txt`, or document pre-commit as convenience-only and make the exact CI command prominent.

5. Pin Playwright CLI/browser tooling used by browser smoke.

## Quick Wins

- Add WebSocket unmasked rejection regression.
- Add no-crypto AES advanced upload regression.
- Update local docs to include the exact CI pytest gate: `pytest --cov=src --cov-report=term-missing --cov-report=xml --cov-fail-under=65`.
- Bump pre-commit Ruff/mypy hook versions to match current CI pins.

## Deeper Improvements

- Add stricter WebSocket parser coverage for RSV bits, reserved opcodes, control-frame size, and fragmentation policy.
- Replace all-at-once gzip with streaming gzip if compressed file downloads are required.
- Add a minimal-install CI job without `crypto` extras for optional dependency behavior.

## Open Questions

- Is unmasked frame parsing intentionally shared for server-frame test decoding only?
- Should large streamed files ever be gzip-compressed, or is preserving low memory more important?
- Is AES advanced upload officially supported without `exphttp[crypto]`, or should it fail fast?
