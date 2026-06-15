# architect-reviewer Report
_Generated: 2026-06-14 23:41:06 Europe/Moscow_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/analysis-plan.md_

## Summary

Scope analyzed: `src/features.py`, `src/server.py`, `src/request_pipeline.py`, `src/handlers/*`, `src/http/*`, `src/notepad_service.py`, `src/websocket.py`, `exphttp/*`, static UI capability use, tests, and `docs/architecture.md`.

Overall: the post-remediation architecture is coherent enough for the current product. The next risk is not a broken boundary, but policy sprawl: profile/capability behavior is defined in `features.py`, interpreted in `server.py`, `http/cors.py`, handler mixins, and static UI code.

## Documentation Checks

No new Context7 lookup was needed; recommendations are repo-internal architecture choices. I relied on the parent Context7 checks recorded in [analysis-plan.md](/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/analysis-plan.md:67).

`docs/architecture.md` accurately shows request flow through `RequestPipeline`, handlers, and `NotepadService`, but its module layout omits `src/features.py` and `src/storage.py`, both now architecturally important.

## Detailed Findings

Server lifecycle is mostly well-contained in [src/server.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/server.py:612): socket setup, worker admission, TLS wrapping, keep-alive receive loop, and shutdown cleanup stay there. `RequestPipeline` cleanly owns parse/auth/dispatch/send ordering in [src/request_pipeline.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/request_pipeline.py:93).

The extraction is still adapter-heavy: `RequestPipelineServer` depends on many private server hooks, including auth, CORS, browser mutation policy, WebSocket admission, dispatch, metrics, and send behavior in [src/request_pipeline.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/request_pipeline.py:27). This is acceptable now, but will resist additional upgrade routes or policy variants.

Capability profiles are centralized as immutable `FeatureSet`s in [src/features.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/features.py:26), and handler registration derives from `features.methods` in [src/handlers/__init__.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/__init__.py:33). That is a good core.

Policy enforcement is scattered: CORS method exposure is in [src/server.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/server.py:970), browser mutation classification is in [src/server.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/server.py:975), WebSocket enablement is in [src/server.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/server.py:1067), and destructive-handler gates live in handlers such as [src/handlers/files.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/files.py:197) and [src/handlers/notepad.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/notepad.py:74).

Storage boundaries are mostly clean: uploads go through `UploadStorageService` under `uploads/`, notes are isolated through `NotepadService` under `notes/`, with note ID/path validation in [src/notepad_service.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/notepad_service.py:665). The weak boundary is SMUGGLE temp artifacts: they are generated directly under `uploads/` in [src/handlers/smuggle.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/smuggle.py:171) and served as `/uploads/...` in [src/handlers/smuggle.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/smuggle.py:141), but use separate quota logic.

Static UI responsibilities are acceptable for a bundled no-build UI. It consumes `PING` capabilities in [src/data/static/ui/core.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/core.js:815), then disables controls by method/capability. For the next feature wave, this should become a documented capability schema rather than more hardcoded booleans.

Package shims are coherent and low-risk: `exphttp` lazy-reexports `src` implementation symbols in [exphttp/__init__.py](/home/user/PycharmProjects/ExperimentalHTTPServer/exphttp/__init__.py:57), while `src.__init__` preserves compatibility with a deprecation warning in [src/__init__.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/__init__.py:74). Import-boundary tests cover the ACME side-effect concern.

## Issues Found

No critical architectural defect found.

Medium: profile/capability policy is not yet a single reusable boundary. Expected risk: changing default profile or adding capabilities requires coordinated edits across server, CORS, handlers, UI, docs, and tests.

Medium: SMUGGLE temp artifacts blur user-owned upload storage and generated temporary storage. Expected risk: confusing lifecycle/quota behavior when upload storage limits become a stronger product promise.

Low/medium: WebSocket routing is embedded in `server.py`/`RequestPipeline`; `/notes/ws` prefix matching is documented, but it will not scale cleanly to more real-time endpoints.

Low: architecture docs lag the remediated boundaries around features, storage services, and static UI capability flow.

## Concrete Recommendations

Move capability policy one step out of `server.py`: add a small `CapabilityPolicy` or grow `FeatureSet` helpers for allowed methods, CORS exposure, browser-mutation classification, and WebSocket route enablement. Gain: safer default-profile migration. Cost: modest test updates.

Create an explicit SMUGGLE temp artifact service or storage-domain object. Either enforce both SMUGGLE and upload quotas on generated files, or move temp artifacts to a separate internal directory with a serving route. Gain: clearer data ownership and recovery. Cost: migration/doc update for `/uploads/smuggle_*.html`.

Keep `HandlerRegistry`; do not do a full handler DI rewrite yet. The mixin coupling is known and documented in [ADR-001](/home/user/PycharmProjects/ExperimentalHTTPServer/docs/ADR/ADR-001-handler-registry.md:27), but the current registry already reduces routing risk.

If capability profiles become public API, add an intentional `exphttp.features` shim instead of letting users import `src.features`.

## Quick Wins

Add `features.py` and `storage.py` to `docs/architecture.md`.

Introduce shared constants/helpers for capability keys and `/notes/ws` route policy.

Make handler test stubs provide explicit `features`; the current fallback to default `lab` in [src/handlers/base.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/base.py:138) can mask missing setup.

Add a focused test that asserts one profile change flows through `PING`, registry, CORS preflight, browser mutation guard, and UI capability mapping.

## Deeper Improvements

Add an `UpgradeRouter` only when a second WebSocket/upgrade endpoint appears.

Add a declarative action/capability manifest consumed by API docs and UI.

Split handler mixins into injected domain handlers only if plugin-style extension or larger feature ownership becomes a real goal.

## Open Questions

Should `lab` remain the default, or is a compatibility deprecation path toward `serve`/`workspace` planned?

Should aggregate upload storage limits include generated SMUGGLE pages?

Is `/notes/ws*` prefix compatibility intentional long-term, or should the route become exact before more WebSocket paths exist?

Will capability/profile definitions be public Python API or only wire-level `PING` contract?
