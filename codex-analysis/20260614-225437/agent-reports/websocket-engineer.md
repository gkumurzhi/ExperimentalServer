# websocket-engineer Report
_Generated: 2026-06-15 00:11:11 Europe/Moscow_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/analysis-plan.md_

## Summary

Subagent execution note: I attempted to run the configured `websocket-engineer` through local `codex exec` in read-only mode, but its sandbox failed before it could read files. I completed the read-only analysis from this session using the same WebSocket criteria. No files were modified.

Affected real-time path: HTTP upgrade for `/notes/ws` in [src/request_pipeline.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/request_pipeline.py:206), connection loop in [src/server.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/server.py:1126), RFC 6455 helpers in [src/websocket.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/websocket.py:130), and Notepad message handling in [src/handlers/notepad.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/notepad.py:287).

Current minimal/no-fragmentation implementation is enough for the bundled browser/lab client, but not enough to present `/notes/ws` as a general workspace-grade sync protocol. The main gaps are application-level: retry idempotency, conflicts, send-failure visibility, stale session semantics, and future capability checks.

## Documentation Checks

Read: source plan, completed product/security/API/architecture/QA reports, `API.md`, WebSocket/server/notepad source, and listed tests.

No new Context7 check was needed. The recommendations are repo-internal protocol and state-contract decisions, not current library/platform guidance. Parent Context7 checks are already recorded in [analysis-plan.md](/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/analysis-plan.md:67).

## Detailed Findings

Upgrade lifecycle is reasonably safe for reconnects: each new socket re-enters HTTP parsing, Basic Auth, WebSocket validation, origin checks, crypto availability, and admission limits before upgrade ([src/request_pipeline.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/request_pipeline.py:128), [src/request_pipeline.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/request_pipeline.py:213)). Active WebSockets are capped separately and default to `workers // 2` ([src/server.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/server.py:220)).

The frame parser is intentionally minimal: masked client frames are enforced, RSV bits rejected, close payloads validated, control frame size capped, and frames over 10 MiB rejected ([src/websocket.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/websocket.py:154), [src/websocket.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/websocket.py:167), [src/websocket.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/websocket.py:187)). Fragmentation and continuation frames are rejected ([src/websocket.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/websocket.py:158), [src/websocket.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/websocket.py:162)). That is acceptable for controlled clients, but not full RFC-client compatibility.

Message ordering is per-connection FIFO because frames are processed serially in the socket loop ([src/server.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/server.py:1188)). Cross-connection ordering and reconnect replay have no server contract.

`opId` is correlation only. The server echoes it on save responses ([src/handlers/notepad.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/notepad.py:370)); it does not store or dedupe operation IDs. The browser mitigates first-save retries by generating a stable client note ID and using `createIfMissing` ([src/data/static/ui/notepad.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/notepad.js:798), [src/data/static/ui/notepad.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/notepad.js:1033)).

Conflict behavior is last-write-wins. `save_note` serializes writes with `_notes_lock`, preserves `created_at`, and atomically replaces the note pair, but there is no revision, ETag, base version, or conflict response ([src/notepad_service.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/notepad_service.py:410), [src/notepad_service.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/notepad_service.py:425), [src/notepad_service.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/notepad_service.py:436)).

Backpressure is basic. Responses use blocking `sendall`, and `_ws_send_json` swallows send failures ([src/handlers/notepad.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/notepad.py:387)). If a save succeeds but the ack is lost, the client can retry and either duplicate a server-generated note or overwrite a stable client note.

Idle ping is keepalive, not liveness. The server sends ping after 60 seconds idle but does not require a timely pong; incoming pong frames are ignored ([src/server.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/server.py:1180), [src/server.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/server.py:1225)).

Incomplete-frame timeout works for idle partial frames, but likely not continuous trickle traffic: the timeout deadline is checked on `TimeoutError`, not after every small chunk ([src/server.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/server.py:1167)). This is bounded by connection limits and frame size, but not by an absolute frame-completion deadline.

## Issues Found

- **Medium:** no server-side idempotency for duplicate `opId`; retry safety currently depends on client-provided `noteId`.
- **Medium:** no conflict contract for concurrent edits; workspace-grade Notepad needs revisions or explicit last-write-wins documentation.
- **Medium:** send failures are swallowed after side effects, making ack loss indistinguishable from operation failure to clients.
- **Low/Medium:** WebSocket `delete` and `clear` do not re-check `note_delete` / `note_clear` per message if future profiles diverge ([src/handlers/notepad.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/notepad.py:312)).
- **Low:** docs say all messages are UTF-8 JSON text frames, but the server dispatches both text and binary payloads to JSON handling ([API.md](/home/user/PycharmProjects/ExperimentalHTTPServer/API.md:708), [src/server.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/server.py:1228)).
- **Low:** no-fragmentation is fine for current clients, but should be explicitly scoped as a lab limitation before broader clients rely on it.

## Concrete Recommendations

Keep the current minimal implementation for lab/bundled-browser use.

If Notepad becomes a real workspace feature, define a v1 WebSocket message envelope with `opId`, `noteId`, `baseRevision`, `clientSeq`, and stable error codes. Make `opId` a true idempotency key with a TTL cache: same `opId` plus same operation returns cached ack; same `opId` with different payload returns conflict/error.

Define close-code policy: `1000` normal, `1001` shutdown or ping timeout, `1002` protocol/incomplete/fragmentation if unsupported, `1003` unsupported binary if text-only, `1007` invalid UTF-8, `1008` capability/auth policy violation, `1009` too large, `1011` internal error.

## Quick Wins

- Document clearly that legacy `opId` is ack correlation, not server deduplication.
- Add tests for duplicate `opId` without stable `noteId`, duplicate `opId` with conflicting payload, and WS ack-loss retry behavior.
- Add message-level capability checks for WS `delete` and `clear`.
- Make `_ws_send_json` return success/failure, record metrics, and close the socket on send failure instead of silently continuing.
- Add a test for continuous slow incomplete-frame trickle, not only idle partial-frame timeout.
- Decide whether binary JSON is supported; either document it or close binary frames with `1003`.

## Deeper Improvements

- Add fragmentation support only if `/notes/ws` becomes public-client compatible.
- Add revision-based conflict handling for saves.
- Add ping/pong liveness with a missed-pong close policy.
- Add reconnect/resume semantics: initial snapshot, optional resume token, replay window, and deduped operation log.
- Add load tests for slow clients, burst saves, reconnect storms, and many idle sockets.

## Open Questions

- Is Notepad intended as single-client convenience sync or multi-client collaborative workspace?
- Should legacy `/notes/ws` remain prefix-matched, or should a future v1 route be exact?
- Should stale `sessionId` remain silently ignored, or become an explicit warning/error in workspace mode?
- Is last-write-wins acceptable, or should saves require `baseRevision`?
- Should future clients be expected to handle fragmentation, or is the bundled browser the only supported client?
