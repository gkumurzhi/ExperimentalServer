# performance-engineer Report
_Generated: 2026-05-05 19:59:00 Europe/Moscow_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260505-193249/analysis-plan.md_

## Summary

Scope analyzed: `src/server.py`, `src/http/io.py`, response building, file/advanced-upload/SMUGGLE/NOTE/WebSocket handlers, TLS/ACME startup path, metrics, CLI limits, and focused tests around upload, streaming, WebSocket limits, metrics, TLS mocks, and live server behavior.

The main confirmed performance risks are inbound body buffering before handler limits, worker-pool starvation/backlog under long-lived or slow connections, invalid CLI limits reaching runtime, and insufficient metrics for diagnosing latency/resource pressure. Positive controls: file downloads are streamed, SMUGGLE has a 10 MiB source cap and one-shot streamed artifact delivery, advanced upload header/URL paths have explicit caps, and WebSocket frames have a 10 MiB cap plus incomplete-frame timeout tests.

No files were modified. I did not run tests or benchmarks to avoid read-only analysis side effects such as cache writes.

## Documentation Checks

- **Python stdlib / CPython** `3.10-3.13` - Context7 topic checked: `ThreadPoolExecutor max_workers and blocking worker behavior`; impact on recommendation: long-lived WebSocket/keep-alive/body-read work should be treated as worker capacity, and preserving worker headroom is a real requirement.
- **Certbot/acme** `5.5.x / unknown from Context7` - Context7 topic checked: `HTTP-01 standalone challenge server`; impact on recommendation: confirms HTTP-01 uses a temporary reachable HTTP server, commonly port 80, so ACME issuance during startup is expected to block until challenge/order completion or timeout.

## Detailed Findings

Inbound HTTP requests are fully buffered in `receive_request`: chunks are appended, joined during header detection, and joined again for the final raw request at `src/http/io.py:67`, `src/http/io.py:105`, and `src/http/io.py:137`. `HTTPRequest` then splits raw bytes into headers/body at `src/http/request.py:39-40`, so handlers operate on a fully materialized `request.body`.

Outbound file responses are better: `HTTPResponse.set_file()` stores a path, not file bytes, at `src/http/response.py:42-55`, and `_send_response()` streams in 64 KiB chunks at `src/server.py:527-540`. Tests cover this in `tests/test_server_live.py:206-230` and `tests/test_server_methods.py:840-864`.

Advanced upload has good caps for header and URL transports (`64 KiB` and `16 KiB`) and a default decoded cap of `16 MiB` in `src/handlers/advanced_upload.py:21-23`. However, JSON body transport decodes/parses the whole request body before checking the encoded field limit: `json.loads(request.body.decode(...))` at `src/handlers/advanced_upload.py:141-185`, while the encoded-size check happens later at `src/handlers/advanced_upload.py:292-296`.

SMUGGLE is bounded but memory-amplifying. It caps source files at `10 MiB` in `src/handlers/smuggle.py:16`, reads at most one byte beyond the cap at `src/handlers/smuggle.py:68-72`, then base64-embeds the source into HTML at `src/utils/smuggling.py:52-62`. Encrypted SMUGGLE adds an XOR output copy before base64. Tests cover over-limit rejection and streamed temp delivery at `tests/test_server_methods.py:659-756`.

NOTE is bounded indirectly, not by a note-specific limit. HTTP NOTE relies on global `max_upload_size`; WebSocket NOTE relies on `_MAX_FRAME_SIZE = 10 MiB` in `src/websocket.py:16`. Saves decode base64 into memory and write bytes at `src/notepad_service.py:165-207`; loads read the full note and base64-encode it into JSON at `src/notepad_service.py:241-250`.

ACME/sslip setup runs before the main server socket is bound or marked running: `_setup_tls()` is called before `socket.bind()` and `self.running = True` at `src/server.py:343-359`. `--sslip` can add public-IP lookup at `src/security/tls_manager.py:89-95` and `src/security/tls.py:386-399`; missing/renewing ACME certs call `obtain_letsencrypt_cert()` at `src/security/tls_manager.py:109-130`.

## Issues Found

- [MEDIUM] Advanced upload JSON body can consume large memory before its own 16 MiB cap applies
  - File/area: `src/handlers/advanced_upload.py`, `src/http/io.py`
  - Evidence: request bytes are fully buffered in `src/http/io.py:67-137`; JSON body upload parses the full body at `src/handlers/advanced_upload.py:141-185`; encoded-size validation is deferred to `src/handlers/advanced_upload.py:292-296`.
  - Detail: default `max_upload_size` is 100 MiB, while advanced upload decoded cap is 16 MiB. A body containing a much larger base64 JSON field can be fully read, UTF-8 decoded, and JSON-parsed before returning 413.
  - Impact: concurrent oversized advanced-upload requests can create avoidable memory pressure and CPU work before rejection.
  - Confidence: high

- [MEDIUM] Worker pool has no global admission/backpressure for slow, queued, or long-lived connections
  - File/area: `src/server.py`, `src/request_pipeline.py`
  - Evidence: accept loop submits every accepted socket to `ThreadPoolExecutor` at `src/server.py:390-396`; WebSocket handling occupies a worker until disconnect at `src/server.py:711-775`; body reads can wait up to `HEADER_TIMEOUT + BODY_TIMEOUT` in `src/http/io.py:15-16` and `src/http/io.py:79-135`.
  - Detail: default WebSocket slots preserve some worker headroom (`max_workers // 2`) at `src/server.py:106-114`, but explicit `max_websocket_connections` can exceed safe headroom, and non-WebSocket slow clients still occupy workers.
  - Impact: bursts of slow uploads, idle keep-alive clients, or long WebSockets can queue normal requests and make latency look like an outage.
  - Confidence: medium; no load test was run.

- [MEDIUM] Invalid `--workers` / `--max-size` values reach runtime
  - File/area: `src/cli.py`, `src/server.py`, `src/http/io.py`
  - Evidence: CLI validates ACME port only at `src/cli.py:175-182`; it passes `args.max_size * 1024 * 1024` and `args.workers` directly at `src/cli.py:184-190`; executor creation happens at `src/server.py:390`.
  - Detail: `--workers 0` or negative reaches `ThreadPoolExecutor`; negative `--max-size` makes even zero-length requests compare greater than the cap in `src/http/io.py:116-122`.
  - Impact: avoidable startup failure or a server that drops ordinary requests.
  - Confidence: high

- [LOW] NOTE load/save lacks a dedicated encrypted-blob size contract
  - File/area: `src/notepad_service.py`, `src/handlers/notepad.py`, `src/websocket.py`
  - Evidence: save decodes full base64 at `src/notepad_service.py:165-167`; load reads full note and base64-encodes it at `src/notepad_service.py:241-250`; WebSocket frame cap is transport-level only at `src/websocket.py:16`.
  - Detail: HTTP NOTE can scale with `--max-size`, and disk-resident notes can be loaded into a single buffered JSON response.
  - Impact: large note blobs multiply memory through raw bytes, base64 text, JSON body, and optional gzip.
  - Confidence: high

- [LOW] ACME and sslip can block startup before the service listens
  - File/area: `src/server.py`, `src/security/tls_manager.py`, `src/security/tls.py`
  - Evidence: TLS setup precedes bind/listen at `src/server.py:343-359`; public IP lookup has a 3s timeout at `src/security/tls.py:386-399`; ACME defaults include `network_timeout=45`, `challenge_timeout=30`, and `order_timeout=90` at `src/security/tls.py:301-313`.
  - Detail: this is bounded and only applies to explicit ACME/sslip modes, but operators see no listening port until DNS/IP lookup, challenge binding, and order finalization complete.
  - Impact: slow/failing issuance looks like startup hang or failed health check.
  - Confidence: high for code path, medium for production timing.

- [LOW] Metrics do not expose latency or resource pressure
  - File/area: `src/metrics.py`, `src/request_pipeline.py`
  - Evidence: metrics snapshot includes counters/status/bytes/WebSocket active only at `src/metrics.py:59-75`; request duration is logged but not recorded at `src/request_pipeline.py:146-155`.
  - Detail: no active worker count, queued accepts, request bytes received, body/header timeout counts, per-route latency, upload rejection counts, or ACME duration/error metrics.
  - Impact: bottlenecks above would be hard to diagnose from `/metrics`.
  - Confidence: high

## Concrete Recommendations

Add pre-parse body guardrails for advanced upload JSON. Before `json.loads`, reject body transport when `len(request.body)` exceeds the encoded limit plus a small JSON-envelope allowance. This does not solve socket-level buffering, but it removes the avoidable JSON/string/base64 work.

Validate CLI lower bounds early: `--workers >= 1`, `--max-size >= 1` or an explicit documented `0` behavior, and ideally cap `max_websocket_connections <= max_workers - 1` when configured through API.

Add a global client admission semaphore around accepted sockets or submitted workers. If a slot cannot be acquired, close immediately or return a small 503 before enqueueing work. Keep the existing WebSocket semaphore as a feature-specific sub-budget.

Add NOTE-specific limits: `max_note_size` for decoded encrypted blobs and a response-side guard for `load_note()`. Default should be lower than generic upload size, for example 16 MiB, unless docs explicitly promise larger notes.

Record minimal performance metrics: request duration buckets or totals, active workers/connections, WebSocket active/rejected/closed-by-reason, body/header timeout drops, request bytes received, and upload/NOTE/SMUGGLE 413 counters.

## Quick Wins

Validate `--workers` and `--max-size` in `src/cli.py`.

Move `ThreadPoolExecutor(max_workers=...)` inside the `try/finally` or create it before binding the server socket so startup failures clean up predictably.

Add one regression test for advanced upload body transport where `request.body` exceeds `_advanced_upload_encoded_size_limit("body")` and assert it returns 413 before JSON parsing.

Expose `request_duration_ms_total` / `request_duration_count` or simple min/max/avg in `MetricsCollector` before adding histograms.

## Deeper Improvements

Stream standard uploads from socket to disk instead of materializing `request.body` for `POST`/`PUT`/`PATCH`/`NONE`. This is the largest memory reduction but touches the request pipeline contract.

Replace WebSocket full-frame unmasking loops with lower-copy handling or stricter message caps for NOTE JSON messages. Current 10 MiB cap is safe enough, but parsing still creates buffer, payload, decoded string, JSON object, and decoded note bytes.

Make ACME issuance an explicit startup phase with timing logs and clear messages for public-IP lookup, challenge bind, challenge answer, and finalize. For production, consider requiring cached certs at service startup and doing renewal out of band.

## Open Questions

Should `max_upload_size` remain the generic cap for all methods, or should advanced upload, NOTE, and SMUGGLE each have documented independent limits?

Is this server expected to be internet-facing under real concurrent traffic, or mainly local/demo use? That determines whether worker admission backpressure is a must-fix or an operational hardening item.

Should successful WebSocket upgrades count as requests in `/metrics`, or stay separate under the WebSocket metric namespace?

