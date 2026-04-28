# performance-engineer Report
_Generated: 2026-04-28 12:04:00 MSK_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/analysis-plan.md_

## Summary

Read-only performance analysis completed against the current worktree. I did not read encrypted `notes/*.enc` contents or modify files.

The standalone `performance-engineer` Codex subagent was launched in read-only mode, but its own sandbox could not read the repo. The findings below are from direct read-only inspection in this session, using the same performance-engineer scope.

## Documentation Checks

- **Python stdlib** `>=3.10` — Context7 topic checked: `socket timeouts, ThreadPoolExecutor, gzip streaming/compress APIs`; impact on recommendation: parent Context7 MCP was quota-blocked, so I used official Python docs as fallback. Docs confirm `ThreadPoolExecutor` runs at most `max_workers`, `gzip.compress(data)` returns a full `bytes` object, `GzipFile` supports file-like streaming, and `sendall()` timeout behavior is socket-timeout dependent. Sources: https://docs.python.org/3.10/library/concurrent.futures.html, https://docs.python.org/3.10/library/gzip.html, https://docs.python.org/3.10/library/socket.html

## Detailed Findings

Scope analyzed: `src/server.py`, `src/http/io.py`, `src/http/request.py`, `src/http/response.py`, `src/handlers/files.py`, `src/handlers/advanced_upload.py`, `src/handlers/notepad.py`, `src/handlers/smuggle.py`, `src/utils/smuggling.py`, `src/notepad_service.py`, `src/websocket.py`, `src/metrics.py`, `docs/ADR/ADR-005-threadpool-over-asyncio.md`, `CHANGELOG.md`, `tests/test_server_live.py`, `tests/test_http/test_io.py`, `tests/test_server_methods.py`, `tests/test_request_pipeline.py`, and benchmark config signals in `pyproject.toml`/`uv.lock`.

Normal GET/FETCH file responses are streamed: `HTTPResponse.set_file()` stores `stream_path`, and `ExperimentalHTTPServer._send_response()` reads `64 KiB` chunks from disk. That streaming property is lost when gzip post-processing, SMUGGLE generation, advanced base64 upload, notepad load/save, or WebSocket frame parsing enters the path.

No benchmark test files were present. `pytest-benchmark` is declared in `pyproject.toml`, but `git ls-files`/`rg` found no benchmark scenarios.

## Issues Found

- [HIGH] Large-file responses stop being streamed when gzip or SMUGGLE is involved
  - File/area: `src/server.py::_maybe_gzip_response`, `src/handlers/files.py::_serve_file`, `src/handlers/smuggle.py::handle_smuggle`, `src/utils/smuggling.py`
  - Evidence: `server.py:262-275` reads `response.stream_path.read_bytes()` then calls `gzip.compress(raw)`; `tests/test_server_methods.py:490-503` asserts gzip converts streamed file responses into buffered bodies. `smuggle.py:52-68` reads the full source file and writes full generated HTML. `utils/smuggling.py:52-62` base64-encodes the full payload. `files.py:91-115` fully reads temporary SMUGGLE HTML before deleting it.
  - Detail: Plain GET/FETCH streams, but `Accept-Encoding: gzip` on compressible files turns the file into a full in-memory body. SMUGGLE has multiple full-size representations: original bytes, optional XOR output, base64 string, HTML string/file, and then a full read when serving the temp HTML.
  - Impact: With the default `100 MB` upload cap and `10` workers, a few concurrent large gzip/SMUGGLE requests can consume hundreds of MB to multiple GB and contradict the changelog’s broad “streaming file I/O” claim.
  - Confidence: high

- [MEDIUM] Upload receive path buffers and copies full request bodies before handler writes
  - File/area: `src/http/io.py::receive_request`, `src/http/request.py::HTTPRequest._parse`, `src/handlers/files.py::handle_none`, `src/request_pipeline.py`
  - Evidence: `io.py:67-130` accumulates chunks then `b"".join(chunks)`; `request.py:28-30` splits raw bytes into `self.body`; `files.py:391-393` writes `request.body`; `_check_payload_size()` runs after `HTTPRequest(data)` in `request_pipeline.py:96-113`.
  - Detail: The max upload setting limits accepted payload size, not peak memory. A near-limit upload can exist as chunk objects, one joined raw request, and one body copy before disk write. Oversized `Content-Length` is not rejected before body read; `io.py:100-102` drops after reading up to `max_upload_size + 64 KiB`.
  - Impact: Ten simultaneous near-limit uploads can exceed memory headroom even though each request is “within limit”; oversized clients also get connection drop behavior rather than an early 413.
  - Confidence: high

- [MEDIUM] Advanced upload and notepad transports multiply payload memory
  - File/area: `src/handlers/advanced_upload.py`, `src/security/crypto.py`, `src/notepad_service.py`, `src/handlers/notepad.py`
  - Evidence: advanced JSON body decode/load at `advanced_upload.py:58-64`; chunked header join at `advanced_upload.py:124-133`; base64 decode at `advanced_upload.py:201-205`; decrypt replacement at `advanced_upload.py:224-227`; XOR allocates `bytearray` plus `bytes` at `crypto.py:167-173`; note save decodes full base64 at `notepad_service.py:165-207`; note load reads full blob and base64-encodes it at `notepad_service.py:241-250`.
  - Detail: Base64 body/header/url transports require the encoded string and decoded bytes at the same time. Encrypted paths can add another full decrypted copy. Notepad loads produce raw bytes, base64 bytes/string, JSON body, and possibly gzip body.
  - Impact: Practical safe payload size is far below `--max-size`, especially for advanced upload and NOTE load/save.
  - Confidence: high

- [MEDIUM] Keep-alive and WebSocket connections can occupy the full worker pool
  - File/area: `src/server.py`, `src/websocket.py`, `docs/ADR/ADR-005-threadpool-over-asyncio.md`
  - Evidence: default `max_workers=10` at `server.py:67`; executor at `server.py:351-357`; keep-alive is per worker with `KEEP_ALIVE_TIMEOUT=15` and `KEEP_ALIVE_MAX=100` at `server.py:380-414`; WebSocket loop holds the worker until close at `server.py:640-690`; ADR target is `~10 concurrent clients` at `ADR-005:16-28`.
  - Detail: HTTP/1.1 defaults to keep-alive, so ten idle keep-alive clients can consume all ten workers for up to 15 seconds after a response. WebSockets consume workers for their full lifetime.
  - Impact: New requests can queue behind idle or long-lived connections even though the accept loop is healthy and backlog is 128.
  - Confidence: high

- [MEDIUM] WebSocket frame buffering can retain near-limit payloads and copies
  - File/area: `src/server.py::_handle_notepad_ws`, `src/websocket.py::parse_ws_frame`
  - Evidence: `server.py:648` uses `buf += chunk`; `websocket.py:16` allows `10 MB` frames; `websocket.py:116-117` returns `None` until a complete frame is present; masked parsing copies via `raw_payload`, `bytearray`, and `bytes` at `websocket.py:119-127`; tests only cover over-limit headers at `tests/test_security/test_websocket_frame_limit.py:35-54`.
  - Detail: A client can declare a frame at the allowed limit and trickle or stall before completion. The worker retains the partial buffer and continues pinging on timeout instead of closing partial-frame connections.
  - Impact: Slow WebSocket clients can create memory retention and worker starvation without exceeding the nominal frame limit.
  - Confidence: high

- [MEDIUM] Metrics undercount application errors and lack performance investigation signals
  - File/area: `src/metrics.py`, `src/request_pipeline.py`, `src/handlers/info.py`, `docs/api.md`
  - Evidence: `metrics.py:25-32` increments `total_errors` only when `error=True`; normal responses record without error flag at `request_pipeline.py:120-122` and direct errors at `request_pipeline.py:153-162`; exceptions only set `error=True` at `request_pipeline.py:139-146`. Valid WebSocket upgrades record no metrics, asserted at `tests/test_request_pipeline.py:319-346`. Docs show `404` status counts paired with `total_errors` at `docs/api.md:207-215`, which current code will not produce.
  - Detail: `total_errors` is effectively “unhandled exceptions,” not HTTP 4xx/5xx error rate. Metrics also omit latency, bytes received, active connections, active WebSockets, in-flight requests, and queue pressure.
  - Impact: `/metrics` and PING cannot explain slowdowns, saturation, large transfer pressure, or real application error rate.
  - Confidence: high

- [LOW] Benchmark tooling is declared but no reproducible performance suite exists
  - File/area: `pyproject.toml`, `uv.lock`, tests
  - Evidence: `pyproject.toml:59-62` declares `pytest-benchmark`; `uv.lock` includes `pytest-benchmark 5.2.3`; no benchmark/perf/load test files were found.
  - Detail: There are unit/live tests for behavior, but no memory/latency baseline for large upload, streamed download, gzip, SMUGGLE, advanced upload, or WebSocket slow-frame cases.
  - Impact: Performance fixes will be hard to validate before/after.
  - Confidence: high

## Concrete Recommendations

1. For the smallest high-impact fix, skip gzip for streamed files above a small threshold, or skip gzip for `response.stream_path` entirely until streaming gzip is implemented. Preserve `set_file()` streaming for large downloads.

2. Add early `Content-Length` rejection in `receive_request()` immediately after headers are parsed. Longer-term, split header receive from body receive so regular uploads can stream directly to a temp file.

3. Add explicit lower caps for advanced upload header/url transports and document body transport as the only large-payload mode. Consider rejecting base64 decoded payloads whose decoded size exceeds a tighter cap.

4. Put a source-size limit on SMUGGLE generation and skip gzip on generated SMUGGLE temp HTML. This gives an immediate memory ceiling.

5. For WebSocket, replace `buf += chunk` with a `bytearray`, track expected frame length once the header is available, and close connections that keep an incomplete frame across a timeout.

6. Change metrics semantics so `total_errors` includes `status_code >= 400`, and add at least latency count/sum/max, bytes received, active connections, active WebSockets, and in-flight request gauges.

## Quick Wins

- Disable gzip for `stream_path` responses over `1 MiB`.
- Count `status_code >= 400` as errors in `MetricsCollector.record()`.
- Record WebSocket handshakes and closes in metrics.
- Add caps for `X-D`, `X-D-*`, and URL `d` advanced upload payload length.
- Add one benchmark per hotspot: plain GET large file, gzip GET large text, POST upload, advanced base64 upload, SMUGGLE generation, and slow/incomplete WebSocket frame.

## Deeper Improvements

- Stream upload bodies to disk for standard upload methods instead of constructing full `HTTPRequest.body`.
- Implement streaming gzip with `gzip.GzipFile(fileobj=...)` or delegate gzip/static compression to a reverse proxy.
- Move long-lived WebSocket handling out of the fixed request worker pool if WebSocket concurrency becomes a real target.
- Add a bounded executor queue or connection admission guard so accepted sockets cannot grow unbounded behind occupied workers.

## Open Questions

- What memory budget should the default `100 MB` upload limit fit within?
- Should SMUGGLE support files near `--max-size`, or is it acceptable to cap it much lower?
- Is gzip required for user uploads, or only for bundled UI/static JSON?
- Should `/metrics` be a lightweight debug endpoint or a stable operational contract?
