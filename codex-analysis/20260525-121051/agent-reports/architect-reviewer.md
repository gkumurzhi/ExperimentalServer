# architect-reviewer Report
_Generated: 2026-05-25 12:40:21 MSK_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260525-121051/analysis-plan.md_

## Summary

Scope analyzed: package/API layout, handler registry/mixins, `RequestPipeline`, feature exposure, auth/feature boundaries, and storage ownership across the requested files plus directly related handlers/docs.

Read-only review only. I did not modify files or run tests. The current architecture is coherent for the current all-features lab server, but it is not a good base for future public API development or safer file-server operation until package naming and feature profiles are introduced.

## Documentation Checks

- **Setuptools** `>=75.0` - Context7 topic checked: `pyproject.toml` package discovery, `src` layout, `package-dir`, package data, console scripts; impact on recommendation: use `src/` as a layout directory with a project-named import package, not as the public import package.
- **Python Packaging User Guide** `current/unknown` - Context7 topic checked: distribution package vs import package, `src` layout, `[project] import-names`; impact on recommendation: `exphttp` can remain the distribution name while the import package migrates from `src` to `exphttp`.

## Detailed Findings

The registry/pipeline split is mostly sound for today: `RequestPipeline.process()` owns parse/auth/browser-origin/size/dispatch/send ordering in [src/request_pipeline.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/request_pipeline.py:104), while `HandlerRegistry` gives a first-class method map in [src/handlers/registry.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/registry.py:18). Existing tests cover the normal pipeline path, auth/size/browser-origin failures, WebSocket upgrade failures, and registry behavior.

The architecture breaks down around future variation. `ExperimentalHTTPServer` is still the composition root for auth, TLS views, metrics, locks, upload/notes directories, ECDH, WebSocket limits, temp SMUGGLE files, and feature flags in [src/server.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/server.py:125). That is acceptable for one product mode, but it makes safer profiles hard to express without scattered conditionals.

## Issues Found

- [HIGH] No capability boundary between safe file serving and experimental/offensive features
  - File/area: [src/server.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/server.py:148), [src/handlers/__init__.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/__init__.py:36), [src/cli.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/cli.py:90)
  - Evidence: `advanced_upload_enabled = True`; `--advanced-upload` is a deprecated no-op; `GET/POST/PUT/PATCH/DELETE/FETCH/INFO/PING/NONE/NOTE/SMUGGLE` are always registered; unknown methods with advanced payload dispatch to advanced upload.
  - Detail: Basic Auth is all-or-nothing and runs before dispatch, but there is no method/profile authorization after auth. A credentialed user gets file upload, delete/clear, Notepad, SMUGGLE, and unknown-method advanced upload together.
  - Impact: Operators cannot run a least-privilege file-server mode. A leaked credential or misconfigured trusted-lab deployment exposes the full experimental surface.
  - Confidence: high

- [MEDIUM] Public API is currently the generic `src` package
  - File/area: [pyproject.toml](/home/user/PycharmProjects/ExperimentalHTTPServer/pyproject.toml:6), [src/__init__.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/__init__.py:54), [README.md](/home/user/PycharmProjects/ExperimentalHTTPServer/README.md:483)
  - Evidence: distribution name is `exphttp`, console script is `src.cli:main`, package discovery includes `src*`, docs expose `from src import ...`, and `python -m src` is documented.
  - Detail: I found 161 `src` import/module references across source, tests, tools, examples, docs, and config in the non-generated project surface.
  - Impact: Every release that documents `src` as public API increases rename cost and creates confusing downstream imports.
  - Confidence: high

- [MEDIUM] Handler and pipeline boundaries are coherent but too coupled for profiles
  - File/area: [src/request_pipeline.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/request_pipeline.py:26), [src/handlers/base.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/base.py:109), [src/http/cors.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/http/cors.py:7)
  - Evidence: `RequestPipelineServer` depends on many private server methods plus `_ecdh_manager`; `BaseHandler` depends on server attributes such as `upload_dir`, `notes_dir`, locks, temp files, metrics, and ECDH; CORS methods are static and list all capabilities.
  - Detail: A future profile would need coordinated changes in registry construction, CORS, browser mutation guards, PING capability reporting, WebSocket upgrade handling, and UI docs.
  - Impact: Feature gating is likely to drift unless capabilities become a single source of truth.
  - Confidence: high

- [HIGH] User-writable storage lacks an aggregate policy boundary
  - File/area: [src/server.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/server.py:84), [src/handlers/files.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/files.py:418), [src/notepad_service.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/notepad_service.py:390)
  - Evidence: `--max-size` is per request; uploads and advanced uploads write unique files; Notepad caps each blob at 1 MiB but lists every `*.enc`; SMUGGLE creates temp files under uploads.
  - Detail: There is no total-byte quota, file-count cap, retention rule, or write reservation shared across `uploads/`, `notes/`, and temporary SMUGGLE output.
  - Impact: Repeated valid writes can fill disk even when every single request respects size limits.
  - Confidence: high

- [MEDIUM] Documented programmatic auth mutates server state without restoring invariants
  - File/area: [README.md](/home/user/PycharmProjects/ExperimentalHTTPServer/README.md:489), [src/server.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/server.py:196)
  - Evidence: README shows `server.authenticator = auth` after construction. `_rate_limiter` is initialized only during `__init__` when `self.authenticator` already exists.
  - Detail: Following the example enables custom auth but leaves `_rate_limiter` unset.
  - Impact: The documented public API silently loses the advertised auth rate limiting.
  - Confidence: high

## Concrete Recommendations

Introduce a small `FeatureSet` / `ServerProfile` first, not a rewrite. Build `HandlerRegistry`, CORS methods/headers, browser mutation guards, PING capability output, and WebSocket availability from that object. Suggested profiles: `serve` for read-only file/UI, `workspace` for ordinary upload/delete, and `lab` for NOTE, SMUGGLE, and advanced upload. Keep `lab` as the compatibility default for 2.x if needed, but make docs and Docker examples use a safer profile.

Start the package migration now: add or move to an `exphttp` import package, update `exphttp = "exphttp.cli:main"`, document `from exphttp import ...`, and keep a deprecated `src` compatibility shim for one release. When the physical layout moves, use Setuptools `package-dir = {"" = "src"}` and `where = ["src"]`.

Add a `StoragePolicy` owned by the server or a storage service, with total bytes, file count, and retention/backpressure checks before upload, advanced upload, note save, and SMUGGLE temp writes.

Replace post-init auth mutation with a constructor parameter or `set_authenticator()` method that also initializes or refreshes rate limiting.

## Quick Wins

- Make `advanced_upload_enabled` actually gate unknown-method advanced upload dispatch.
- Change PING’s `advanced_upload: true` to report the real configured value.
- Add a grep/stale-doc guard for `from src`, `import src`, and `python -m src` once the `exphttp` package exists.
- Update the README custom-auth example so rate limiting remains enabled.

## Deeper Improvements

- Move from implicit handler server attributes to a small `HandlerContext` protocol.
- Make CORS and UI capability discovery registry/profile-derived.
- Add method-level authorization only after coarse profiles exist; profiles give most of the risk reduction with less complexity.
- Decide whether Notepad is part of “workspace” or only “lab,” given its non-durable key model.

## Open Questions

- Should the future default be `serve`, `workspace`, or backward-compatible `lab` until a major release?
- Should disabled experimental methods return `404` to hide capability or `405` for clearer API feedback?
- What default aggregate quota is acceptable for local use?
- Is `src` import compatibility required through all 2.x releases, or only one deprecation cycle?
