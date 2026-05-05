# websocket-engineer Report
_Generated: 2026-05-05 19:59:10 Europe/Moscow_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260505-193249/analysis-plan.md_

## Summary

Affected real-time path: browser/custom client NOTE key exchange (`NOTE /notes/key`, `NOTE /notes/exchange`) and optional WebSocket transport (`GET /notes/ws`) through `RequestPipeline`, `ExperimentalHTTPServer._handle_notepad_ws`, `src/websocket.py`, and `NotepadHandlersMixin`.

Read-only validation only. I inspected the requested source/test files plus supporting ECDH/example/API/test files. I did not run tests or write files.

## Documentation Checks

- **MDN Web Docs WebSocket API** `unknown` - Context7 topic checked: `WebSocket.send(), close(), close event semantics`; impact on recommendation: browser sends are queued, `close()` is asynchronous, and sends on closing/closed sockets may be discarded, so reconnect needs connection-generation guards plus application-level ack/idempotency.
- **cryptography** `>=48.0` - Context7 topic checked by parent plan: `ECDH/HKDF/AES-GCM`; impact on recommendation: I did not repeat it. HKDF findings below are based on project constants and browser/example code.

## Detailed Findings

The server validates upgrade shape before switching protocols: `src/request_pipeline.py:195-227` checks RFC-style headers, origin, crypto availability, and admission budget before calling `src/server.py:676-779`. Basic Auth runs before upgrade at `src/request_pipeline.py:120-126`.

Origin behavior is explicit: missing `Origin` is allowed, same-origin is allowed, configured CORS origins and wildcard are allowed, and other origins are rejected in `src/server.py:610-634`. Tests cover those cases in `tests/test_server_methods.py:216-319` and live rejection in `tests/test_security/test_websocket_upgrade.py:51-143`.

Frame handling is mostly bounded and defensive. Client frames are required to be masked in the live loop via `parse_ws_frame(..., require_mask=True)` at `src/server.py:737-739`; frame size is capped at 10 MB in `src/websocket.py:16` and `src/websocket.py:187-188`; protocol errors close with code 1002 or 1007, oversized frames close with 1009, and incomplete frames time out through `src/server.py:717-725`.

HTTP NOTE and WebSocket NOTE share `NotepadService`, so save/list/load/delete/clear storage behavior is aligned. Tests verify response parity in `tests/test_websocket_handlers.py:373-460`. The input shape differs by transport: HTTP save uses `id`, while WS save uses `noteId`, matching `API.md:540-548`.

## Issues Found

- [HIGH] Secure Notepad stores persistent blobs with a per-page session key that is not recoverable across sessions
  - File/area: `src/data/static/ui/notepad.js`, `src/security/keys.py`, `src/notepad_service.py`
  - Evidence: browser generates a fresh ECDH key at `notepad.js:450-459`, keeps `notepadDerivedKey` only in memory at `notepad.js:4-5` and `notepad.js:501-512`; server session keys are in-memory/TTL-bound in `keys.py:72-78` and `keys.py:142-151`; storage only writes opaque bytes in `notepad_service.py:198-207`.
  - Detail: a reload/new browser/client derives a different AES-GCM key, but stored notes are later decrypted only with the current page key at `notepad.js:820-822`.
  - Impact: notes saved in one page/client session can become unreadable after reload, from another client, or after server restart.
  - Confidence: high

- [HIGH] Example client uses a different HKDF contract than server/browser
  - File/area: `examples/notepad_client.py`
  - Evidence: example uses `salt=None` and `info=b"exphttp-notepad"` at `examples/notepad_client.py:118-123`; server uses 32 zero bytes and `notepad-e2e-key` at `src/security/keys.py:41-42`; browser matches server at `notepad.js:501-507`.
  - Detail: server does not decrypt or verify note ciphertext, so the mismatch is silent.
  - Impact: example-created notes are not compatible with browser-created notes, and vice versa.
  - Confidence: high

- [MEDIUM] Browser reconnect path can churn sockets and duplicate create side effects
  - File/area: `src/data/static/ui/notepad.js`
  - Evidence: `notepadConnectWs()` closes an old socket then immediately resets the global `wsIntentionalClose` flag at `notepad.js:561-566`; old `onclose` handlers can still schedule reconnect at `notepad.js:583-587`; saves have no client operation id at `notepad.js:688-696`; new server notes are generated when `note_id` is empty at `src/notepad_service.py:173-181`.
  - Detail: a stale close event can schedule a reconnect that closes a healthy socket. If a `save` create was sent and the `saved` response is lost, `notepadCurrentId` remains empty, so retry/fallback can create another note.
  - Impact: unstable networks can cause connection churn, stuck saving state, or duplicate notes.
  - Confidence: medium

- [LOW] Worker occupancy is mitigated by default but still easy to make unavailable or starving
  - File/area: `src/server.py`, CLI worker config
  - Evidence: default WS budget is `max_workers // 2` at `src/server.py:106-114`; with one worker it becomes zero, tested at `tests/test_server_methods.py:583-592`; each accepted WS occupies a worker in `src/server.py:711-779`.
  - Detail: CLI exposes `--workers` but not WS budget, so `--workers 1` disables WS admission. Programmatic callers can set WS budget equal to all workers.
  - Impact: WS can be unexpectedly unavailable or can starve HTTP fallback/admission responses.
  - Confidence: high

- [LOW] Text-only WebSocket contract is looser than documented
  - File/area: `src/server.py`, `src/handlers/notepad.py`, `API.md`
  - Evidence: API says all messages are UTF-8 JSON text frames at `API.md:534`; server dispatches both `WS_TEXT` and `WS_BINARY` at `src/server.py:773-774`; invalid UTF-8 becomes an app JSON error at `src/handlers/notepad.py:269-273`.
  - Detail: binary frames and invalid text payloads are treated as application errors rather than protocol close cases.
  - Impact: low protocol ambiguity and weaker negative-path behavior for custom clients/fuzzers.
  - Confidence: high

## Concrete Recommendations

Fix `examples/notepad_client.py` to use the exact server/browser HKDF salt and info, then add a fixed-key regression proving Python and browser-compatible derivation match.

Decide the durable-notes key contract. If notes should survive reloads, introduce a recoverable key mechanism; if notes are intentionally session-only, update UI/API/docs and avoid presenting old ciphertext as normally loadable.

Add WS client operation IDs or client-generated note IDs for first save, and make save retries idempotent. Guard reconnect handlers with a connection generation/token so stale `onclose` cannot affect the active socket.

## Quick Wins

Add tests for example HKDF parity, invalid UTF-8 text frames, binary frame rejection or documentation, and a WS create where the response is lost before retry.

Document the current WS worker budget behavior and warn that `--workers 1` disables WebSocket admission.

## Deeper Improvements

Add browser-level unstable-network tests: save over WS, drop before ack, reconnect, verify no duplicate note and dirty state is retried or resolved.

Add load testing for slow incomplete frames occupying the WS budget while HTTP fallback remains responsive.

## Open Questions

Is Secure Notepad intended to be durable across page reloads and server restarts, or only usable inside one browser session?

Should `/notes/ws` be an exact upgrade path instead of accepting any `/notes/ws*` prefix?

Should wildcard CORS intentionally allow cross-origin WebSocket upgrades for notepad?

