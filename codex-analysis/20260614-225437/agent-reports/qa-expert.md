# qa-expert Report
_Generated: 2026-06-14 23:44:49 Europe/Moscow_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/analysis-plan.md_

## Summary
Scope analyzed: read-only QA review of `tests/`, `pyproject.toml`, CI/security/release workflows, docs/smoke tooling, and related early-check hooks in `/home/user/PycharmProjects/ExperimentalHTTPServer`. I did not modify files or run artifact-generating validation.

The test suite is broad, but the gates are not risk-specific. CI has one global coverage gate at 65% in [ci.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/.github/workflows/ci.yml:64), while the plan already identifies missing explicit gates for auth/parser/WebSocket/storage/CORS in [analysis-plan.md](/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/analysis-plan.md:83).

## Documentation Checks
Docs drift is confirmed by parent validation: `API.md -> docs/api.md` and `CONTRIBUTING.md -> docs/contributing.md` are out of sync in [analysis-plan.md](/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/analysis-plan.md:57). CI would catch this in the docs job via `python tools/sync_docs.py --check` in [ci.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/.github/workflows/ci.yml:95).

`sync_docs.py` is exact mirror enforcement for `API.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, and `SECURITY.md` in [sync_docs.py](/home/user/PycharmProjects/ExperimentalHTTPServer/tools/sync_docs.py:23). `check_stale_docs.py` is semantic/stale-phrase scanning, not mirror equivalence, so it can pass while mirror drift fails in [check_stale_docs.py](/home/user/PycharmProjects/ExperimentalHTTPServer/tools/check_stale_docs.py:70).

Docs sync is documented for contributors in [CONTRIBUTING.md](/home/user/PycharmProjects/ExperimentalHTTPServer/CONTRIBUTING.md:158), but pre-commit only has static UI/browser JS hooks, not docs mirror hooks, in [.pre-commit-config.yaml](/home/user/PycharmProjects/ExperimentalHTTPServer/.pre-commit-config.yaml:33).

## Detailed Findings
Modules needing explicit gates:

- Auth/admission: `src/security/auth.py` and server auth behavior. Evidence includes Basic Auth parser/auth-file tests in [test_auth.py](/home/user/PycharmProjects/ExperimentalHTTPServer/tests/test_security/test_auth.py:19), live 401/200 auth flow in [test_server_live.py](/home/user/PycharmProjects/ExperimentalHTTPServer/tests/test_server_live.py:366), and limiter tests in [test_handler_integration.py](/home/user/PycharmProjects/ExperimentalHTTPServer/tests/test_handlers/test_handler_integration.py:1038).
- HTTP parser/framing/pipeline: `src/http/io.py`, `src/http/request.py`, `src/request_pipeline.py`. Evidence includes Content-Length/TE rejection in [test_content_length_smuggling.py](/home/user/PycharmProjects/ExperimentalHTTPServer/tests/test_http/test_content_length_smuggling.py:77), receive guards in [test_io.py](/home/user/PycharmProjects/ExperimentalHTTPServer/tests/test_http/test_io.py:21), parser fuzzing in [test_request_parser.py](/home/user/PycharmProjects/ExperimentalHTTPServer/tests/test_property/test_request_parser.py:11), and pipeline failure ordering in [test_request_pipeline.py](/home/user/PycharmProjects/ExperimentalHTTPServer/tests/test_request_pipeline.py:155).
- WebSocket/Notepad transport: `src/websocket.py`, `src/handlers/notepad.py`, `src/notepad_service.py`, WebSocket paths in `src/server.py`. Evidence includes frame/handshake tests in [test_websocket.py](/home/user/PycharmProjects/ExperimentalHTTPServer/tests/test_websocket.py:27), fuzzing in [test_ws_frame_parser.py](/home/user/PycharmProjects/ExperimentalHTTPServer/tests/test_property/test_ws_frame_parser.py:17), upgrade security in [test_websocket_upgrade.py](/home/user/PycharmProjects/ExperimentalHTTPServer/tests/test_security/test_websocket_upgrade.py:56), live WS roundtrip in [test_server_live.py](/home/user/PycharmProjects/ExperimentalHTTPServer/tests/test_server_live.py:637), and HTTP/WS parity in [test_websocket_handlers.py](/home/user/PycharmProjects/ExperimentalHTTPServer/tests/test_websocket_handlers.py:609).
- Storage/quota/destructive operations: `src/storage.py`, upload handlers, SMUGGLE temp storage, and Notepad storage. Evidence includes atomic upload/quota tests in [test_files.py](/home/user/PycharmProjects/ExperimentalHTTPServer/tests/test_handlers/test_files.py:185), Notepad quota/atomic failure tests in [test_notepad.py](/home/user/PycharmProjects/ExperimentalHTTPServer/tests/test_handlers/test_notepad.py:248), and clear/delete behavior in [test_notepad.py](/home/user/PycharmProjects/ExperimentalHTTPServer/tests/test_handlers/test_notepad.py:529).
- CORS/browser-origin/profile policy: `src/http/cors.py`, `src/features.py`, and server profile dispatch. Evidence includes profile definitions in [features.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/features.py:62), profile tests in [test_server_methods.py](/home/user/PycharmProjects/ExperimentalHTTPServer/tests/test_server_methods.py:220), CORS contract tests in [test_server_methods.py](/home/user/PycharmProjects/ExperimentalHTTPServer/tests/test_server_methods.py:540), and browser mutation guard tests in [test_server_methods.py](/home/user/PycharmProjects/ExperimentalHTTPServer/tests/test_server_methods.py:714).

Smoke split:

- PR CI should block on fast deterministic gates: lint/type, pytest critical lanes, docs mirror/stale docs, static UI asset/source checks, and JS syntax.
- Release should block on artifact-realistic gates: built wheel install/import smoke, installed-package browser smoke, static UI wheel check, pinned dependency audit/SBOM, provenance, and Docker smoke if container distribution is treated as a release surface.
- Current CI already runs browser and Docker smoke on PRs in [ci.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/.github/workflows/ci.yml:173), while release workflow runs installed-wheel browser smoke but not Docker smoke in [release.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/.github/workflows/release.yml:68).

Profile-specific browser/Docker expansion:

- Browser smoke currently hardcodes `profile="lab"` in [browser_smoke.py](/home/user/PycharmProjects/ExperimentalHTTPServer/tools/browser_smoke.py:78) and asserts advanced upload is available in [browser_smoke.playwright.js](/home/user/PycharmProjects/ExperimentalHTTPServer/tools/browser_smoke.playwright.js:2684).
- Expand browser smoke only when profile-specific UI behavior becomes release-critical, especially if default changes from `lab`. Add minimal `serve`/`workspace` checks for disabled advanced upload/Notepad controls rather than duplicating the whole lab happy path.
- Docker smoke currently validates HTTP health/PING and TLS+auth PING in [ci.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/.github/workflows/ci.yml:251). Add profile-specific Docker smoke only if Docker docs/examples recommend non-lab profiles or if images become published artifacts.

## Issues Found
P1: Docs mirror drift is present now. Risk: docs job blocks PR/main and users see inconsistent root/docs-site content. Evidence: [analysis-plan.md](/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/analysis-plan.md:76).

P2: Critical test coverage is not explicitly gated. Risk: a high-risk module can regress while global 65% still passes. Evidence: [pyproject.toml](/home/user/PycharmProjects/ExperimentalHTTPServer/pyproject.toml:103) has strict markers but no custom lanes; CI uses only global `--cov-fail-under=65`.

P2: Browser smoke is lab-only. Risk: safe/default profile changes could ship with broken disabled-state UI despite live server profile tests passing. Evidence: [browser_smoke.py](/home/user/PycharmProjects/ExperimentalHTTPServer/tools/browser_smoke.py:83).

P3: Docs drift is caught by CI but not earlier by automation. Risk: avoidable PR failures. Evidence: pre-commit local hooks omit docs sync in [.pre-commit-config.yaml](/home/user/PycharmProjects/ExperimentalHTTPServer/.pre-commit-config.yaml:33).

## Concrete Recommendations
Add custom pytest markers or named CI commands for `auth`, `parser`, `websocket`, `storage`, `cors`, `profile`, and `live`. Register them in `pyproject.toml` before use because `--strict-markers` is enabled.

Add a critical coverage check after the existing coverage run, but baseline it from current measured coverage first. Prefer module/file thresholds or no-regression checks for `src/security/auth.py`, `src/http/io.py`, `src/http/request.py`, `src/http/cors.py`, `src/websocket.py`, `src/notepad_service.py`, `src/storage.py`, and `src/features.py`.

Keep full lab browser smoke as a release blocker. Add short profile browser smoke for `serve` and `workspace` only when the product/default profile roadmap changes.

Add `python tools/sync_docs.py --check` and `python tools/check_stale_docs.py` to local pre-commit for root-canonical docs and `docs/` mirrors.

## Quick Wins
Regenerate docs mirrors with `python tools/sync_docs.py --write`, then verify `--check`.

Add pre-commit docs-sync hooks scoped to `API.md|CHANGELOG.md|CONTRIBUTING.md|SECURITY.md|docs/(api|changelog|contributing|security).md|tools/sync_docs.py`.

Add CI named pytest commands for existing tests first, without inventing new tests: parser/framing, auth, WebSocket/Notepad, storage/quota, CORS/profile.

## Deeper Improvements
Create a small `tools/check_critical_coverage.py` that reads `coverage.xml` and enforces per-file thresholds for the critical modules above.

Add `--profile` support to `tools/browser_smoke.py`, then run full lab smoke plus minimal `serve`/`workspace` capability-disabled assertions.

Decide whether Docker is a release artifact. If yes, Docker HTTP/TLS/auth smoke should move into or be required by the release workflow; if no, keep it PR/scheduled and Dockerfile-change gated.

## Open Questions
Should the default profile remain `lab`, or should QA prepare gates for a `workspace`/`serve` default migration?

Is Docker intended as a supported release artifact or a convenience smoke target?

What minimum per-module coverage policy is acceptable after measuring the current baseline?
