# websocket-engineer Report
_Generated: 2026-04-28 11:54:00 MSK_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/analysis-plan.md_

## Summary

Affected path: `GET /notes/ws` in `RequestPipeline._process_websocket_upgrade()` -> `ExperimentalHTTPServer._handle_notepad_ws()` -> `parse_ws_frame()` -> `NotepadHandlersMixin._handle_ws_message()` -> `NotepadService`.

The upgrade/auth/origin boundary is mostly clear: Basic Auth runs before upgrade, origin is checked before `101`, and crypto-unavailable mode rejects upgrade with `501`. The main gaps are in WebSocket framing semantics, worker exhaustion under long-lived sockets, and reconnect/idempotency behavior for note saves.

Validation performed: read the listed source/tests plus relevant NOTE HTTP tests, UI reconnect code, API docs, README, threat model, and CLI config. Ran targeted tests: `73 passed` for WebSocket/live/property suites and `49 passed` for NOTE handler tests. Also ran small read-only probes showing unmasked frames and no-Host/no-Origin upgrade inputs are currently accepted.

## Documentation Checks

- **IETF WebSocket RFC** `RFC 6455` — Context7 topic checked: `not applicable; official RFC checked instead` ([RFC 6455](https://datatracker.ietf.org/doc/rfc6455/)); impact on recommendation: client frames must be masked, RSV/unknown opcodes/control frames must be validated, fragmented messages must not be processed before message completion, invalid handshakes should fail.
- **Python stdlib concurrent.futures** `Python 3.x` — Context7 topic checked: `not applicable; official Python docs checked instead` ([ThreadPoolExecutor](https://docs.python.org/3/library/concurrent.futures.html)); impact on recommendation: one long-running WebSocket loop occupies one worker, so concurrency limits/backpressure need to be explicit.
- **exphttp project docs** `2.0.0` — Context7 topic checked: `local docs/API/README/threat model`; impact on recommendation: docs promise masked client frames and default `--workers 10`, but the implementation accepts unmasked frames and can let idle WS clients consume all workers.

## Detailed Findings

Normal stream path: valid upgrade reaches `_handle_notepad_ws()`, sends `101`, reads frames into `buf`, responds to ping/pong/close, and routes text/binary payloads into NotepadService. HTTP and WS NOTE operations mostly share validation through `SaveNoteRequest` and `NotepadService`.

Degraded path: reconnect exists only in the browser client (`scheduleReconnect()`), but there is no message id, request id, save idempotency key, ack correlation, or pending-operation replay. The server protocol is stateless command/response, not a synchronized stream.

## Issues Found

- [HIGH] Client masking is not enforced
  - File/area: [src/websocket.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/websocket.py:74), [src/server.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/server.py:657)
  - Evidence: `parse_ws_frame()` treats `masked=False` as valid and returns raw payload; `tests/test_websocket.py::test_unmasked_server_frame` asserts unmasked parsing.
  - Detail: RFC 6455 requires client-to-server frames to be masked and protocol failure on unmasked client frames. This parser is used on inbound client traffic but also as a generic test helper for server frames.
  - Impact: non-compliant clients can inject raw frames; this weakens the project’s documented “client sends masked frames” contract and WebSocket frame-smuggling assumptions.
  - Confidence: high

- [MEDIUM] FIN/fragmentation/RSV/unsupported opcode rules are not enforced
  - File/area: [src/websocket.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/websocket.py:87), [src/server.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/server.py:689)
  - Evidence: parser only extracts `opcode = data[0] & 0x0F`; FIN and RSV bits are ignored. `_handle_notepad_ws()` processes `WS_TEXT`/`WS_BINARY` immediately and silently ignores continuation/unknown opcodes.
  - Detail: A `FIN=0` text frame can trigger NOTE side effects before the WebSocket message is complete. Continuation frames are ignored rather than assembled or rejected. RSV bits and unknown opcodes are not closed with protocol error.
  - Impact: compliant fragmented clients can fail; malicious clients can cause premature note operations on incomplete messages.
  - Confidence: high

- [MEDIUM] Long-lived or slow WebSocket connections can pin all worker threads
  - File/area: [src/server.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/server.py:351), [src/server.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/server.py:640), [README.md](/home/user/PycharmProjects/ExperimentalHTTPServer/README.md:157)
  - Evidence: server uses `ThreadPoolExecutor(max_workers=self.max_workers)` with default `10`; `_handle_notepad_ws()` runs an indefinite recv loop in that worker. Timeout sends ping and continues.
  - Detail: Ten idle WS clients can occupy all default workers. A peer can also advertise a payload up to `_MAX_FRAME_SIZE` and drip data, keeping per-connection buffer and worker state alive.
  - Impact: HTTP and NOTE requests queue behind idle WebSockets; public deployments can suffer simple availability loss.
  - Confidence: high

- [MEDIUM] Reconnect path can duplicate new-note saves after lost acknowledgements
  - File/area: [src/data/static/ui/notepad.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/notepad.js:545), [src/data/static/ui/notepad.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/notepad.js:684), [src/notepad_service.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/notepad_service.py:173)
  - Evidence: client reconnects but does not replay/correlate pending operations. New WS saves omit `noteId`; server generates a new ID; client only records it after receiving `saved`.
  - Detail: If the server saves a new note but the socket closes before the client receives the response, the next autosave still has no `notepadCurrentId` and creates another note.
  - Impact: duplicate notes and confusing state after unstable networks.
  - Confidence: medium

- [LOW] Close/error semantics can send duplicate close frames and mask the real close reason
  - File/area: [src/server.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/server.py:672), [src/server.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/server.py:695), [tests/test_server_methods.py](/home/user/PycharmProjects/ExperimentalHTTPServer/tests/test_server_methods.py:727)
  - Evidence: close handling sends a close frame then returns; `finally` sends another normal close. Oversized frames send `1009` then a final default `1000`; tests assert both frames.
  - Detail: After sending a close response, the connection should close without emitting a second contradictory close frame.
  - Impact: clients may observe normal close instead of the real policy/size error.
  - Confidence: high

- [LOW] Invalid WebSocket handshakes without `Host` can pass when `Origin` is absent
  - File/area: [src/websocket.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/websocket.py:29), [src/server.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/server.py:557)
  - Evidence: `check_websocket_upgrade()` does not require `Host`; `_is_websocket_origin_allowed()` returns `True` immediately when `Origin` is missing.
  - Detail: RFC handshake requires `Host`. Existing origin tests cover missing Host only when Origin is present.
  - Impact: malformed non-browser handshakes can reach `101`.
  - Confidence: high

- [LOW] WS application error contract is inconsistent with docs and UI assumptions
  - File/area: [src/handlers/notepad.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/notepad.py:292), [src/handlers/notepad.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/notepad.py:318), [docs/api.md](/home/user/PycharmProjects/ExperimentalHTTPServer/docs/api.md:447)
  - Evidence: nonexistent valid delete returns `{"error":"Note not found","status":404,"type":"deleted"}`. Docs list `error` as the error response type and omit WS `clear`/`cleared`.
  - Detail: Operation-typed error payloads are tolerated in some client paths but `deleted` is treated as success by UI code.
  - Impact: delete failures can clear local editor state or mislead clients.
  - Confidence: high

## Concrete Recommendations

1. Split inbound client parsing from generic frame parsing. For client frames, require mask, reject RSV unless negotiated, reject unknown/reserved opcodes, reject fragmented control frames and control payloads over 125 bytes, validate close payloads, and close with `1002`/`1003`/`1007`/`1009` as appropriate.
2. Either implement fragmented message assembly with an aggregate message cap or explicitly fail fragmented data frames with protocol error. Do not process a data message until FIN completes it.
3. Track whether a close frame was already sent and avoid the unconditional final `1000` close.
4. Require `Host` during upgrade validation. For TLS behind reverse proxies, add an explicit external-origin/proto setting or document that `--cors-origin` must be configured.
5. Add a small WS connection budget or semaphore, an incomplete-frame idle deadline, and metrics for active WS connections/rejected WS upgrades.
6. Add `clientRequestId`/operation id echoing for WS messages, especially `save`, and make new-note creation idempotent across reconnect.
7. Normalize WS errors to a documented schema such as `{type:"error", op:"delete", status:404, error:"..."}` and update docs/tests for `clear`.

## Quick Wins

- Add tests for unmasked client frames, `FIN=0`, RSV set, unknown opcode, fragmented control frames, missing Host, and duplicate close suppression.
- Lower-risk parser change: add a `require_mask=True` parameter used only on inbound server traffic while keeping test helpers for unmasked server frames.
- Update `docs/api.md` to include WS `clear`/`cleared`, binary-frame policy, and wildcard origin implications.

## Deeper Improvements

- Add unstable-network integration tests: save response lost before client receives ID, reconnect during autosave, slow incomplete frame, and ten idle WS connections with `--workers 10`.
- Add bounded per-connection message processing: max buffered bytes, max messages per burst, and optional close after repeated unanswered pings.
- Consider client-generated note IDs for first save, or a server-side idempotency table keyed by `clientRequestId`.

## Open Questions

- Should WS accept binary JSON, or should `/notes/ws` be text-only as documented?
- Is `/notes/ws*` intentionally accepted, or should the upgrade path be exactly `/notes/ws`?
- Is `--cors-origin "*"` intended to authorize WebSocket writes from any browser origin?
- What is the expected maximum concurrent WS client count for supported deployments?
- Will TLS commonly terminate before this Python server? If yes, same-origin checks need an explicit proxy-aware configuration.
