# performance-engineer Report
_Generated: 2026-05-25 12:43:11 MSK_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260525-121051/analysis-plan.md_

## Summary

Read-only performance/resource review completed for the requested server, HTTP I/O, response, file, advanced upload, Notepad, WebSocket, and related tests. No files were modified and I did not run tests to avoid creating cache/runtime artifacts.

Existing controls are meaningful: worker admission is bounded before `ThreadPoolExecutor.submit`, request headers/bodies have per-request caps, streamed `GET`/`FETCH` avoids full response buffering, gzip skips streamed files, keep-alive has request and idle limits, WebSocket connections and frames are capped, and ECDH session state has TTL/LRU bounds.

The main operational risks are still aggregate resource exhaustion: disk has no total quota/retention, standard uploads are fully buffered in memory, slow request bodies/download readers can pin workers, and note/directory listing does full scans.

## Documentation Checks

- **Python / CPython stdlib** `3.10-3.13 target, docs current via /python/cpython` - Context7 topic checked: `socket.settimeout`, `socket.sendall`, `socket.sendfile`, `ThreadPoolExecutor`, `os.scandir`; impact on recommendation: confirmed long-lived blocking socket work occupies worker threads, `sendall()` timeout applies to each send operation, `sendfile()` is the stdlib high-performance file-send path, and `os.scandir()` is preferred for large directory iteration.

## Detailed Findings

Scope analyzed:
`src/server.py`, `src/http/io.py`, `src/http/response.py`, `src/handlers/files.py`, `src/handlers/advanced_upload.py`, `src/notepad_service.py`, `src/websocket.py`, `src/request_pipeline.py`, `src/http/request.py`, `src/http/utils.py`, `src/handlers/notepad.py`, `src/handlers/info.py`, `src/handlers/smuggle.py`, `src/security/keys.py`, and relevant tests including HTTP I/O, WebSocket, server live/method tests, metrics, Notepad, advanced upload, and content-length smuggling tests.

Validated by static evidence:
- Normal path: streamed file responses use `HTTPResponse.set_file()` and `_send_response()` chunking.
- Failure path: oversized declared bodies and invalid framing are rejected before handler dispatch.
- Integration edge: worker admission and WebSocket admission have live/unit coverage.

Not runtime-validated:
- Actual memory high-water under concurrent max-size uploads.
- Slow-body, slow-download, and large-directory latency under load.
- Disk exhaustion behavior under repeated uploads/notes/SMUGGLE artifacts.

## Issues Found

- [HIGH] No aggregate disk quota or retention for uploads, notes, or SMUGGLE artifacts
  - File/area: `src/handlers/files.py:418-439`, `src/handlers/advanced_upload.py:385-405`, `src/notepad_service.py:305-401`, `src/handlers/smuggle.py:68-90`
  - Evidence: per-request caps exist, but successful writes always create files; notes have a 1 MiB per-note blob cap; SMUGGLE writes temp HTML and only cleans it after serving/start/stop.
  - Detail: repeated valid writes can fill disk even when every request respects `--max-size` or Notepad limits.
  - Impact: disk-full errors, failed writes, degraded host/service behavior.
  - Confidence: high

- [HIGH] Standard uploads are fully buffered, so memory scales with `max_workers * max_upload_size`
  - File/area: `src/http/io.py:102-201`, `src/http/request.py:39-40`, `src/handlers/files.py:418-419`, `src/cli.py:97-119`
  - Evidence: `receive_request()` stores chunks and returns `b"".join(chunks)`; `HTTPRequest` stores `self.body`; `handle_none()` writes `request.body`; defaults are 10 workers and 100 MB.
  - Detail: default concurrent upload ceiling is roughly 1 GB of request body memory before Python/object overhead. Higher `--workers` or `--max-size` multiplies this directly.
  - Impact: OOM, swap thrash, latency spikes, worker loss under normal-looking concurrent uploads.
  - Confidence: high

- [HIGH] Slow or incomplete request bodies can occupy all worker slots for up to about 330 seconds
  - File/area: `src/http/io.py:17-19`, `src/http/io.py:114-123`, `src/http/io.py:196-199`, `src/server.py:530-540`
  - Evidence: body timeout is `HEADER_TIMEOUT + BODY_TIMEOUT` = 30 + 300 seconds; after headers are received, timeout exceptions continue until the total budget expires.
  - Detail: a client can declare an allowed `Content-Length`, send headers, then stall the body. With `max_workers` such clients, admission rejects new work.
  - Impact: small-connection denial of service; keep-alive and per-request size caps do not prevent it.
  - Confidence: high

- [MEDIUM] Slow response readers can pin worker threads during streamed downloads
  - File/area: `src/server.py:680-705`
  - Evidence: streamed responses loop over 64 KiB reads and blocking `client_socket.sendall(chunk)` with no total response deadline.
  - Detail: streaming avoids memory copies, but a slow client can keep a worker busy for the full transfer. Socket timeout limits one blocked send, not the full response lifetime.
  - Impact: reduced throughput and worker starvation under slow downloads or large files.
  - Confidence: medium

- [MEDIUM] Directory and note listings scan/sort everything before returning limited output
  - File/area: `src/handlers/info.py:69-89`, `src/notepad_service.py:390-401`, `src/handlers/notepad.py:291-294`
  - Evidence: `INFO` builds `all_items` from sorted full `iterdir()` before slicing; Notepad `list_notes()` scans all `*.enc`, stats/reads sidecars, sorts, and returns all notes.
  - Detail: pagination in `INFO` limits response size only after full server-side work. Notepad has no pagination.
  - Impact: large directories or many notes create latency, memory pressure, and worker occupancy.
  - Confidence: high

- [LOW] WebSocket resource knobs exist in code but are not operator-exposed
  - File/area: `src/server.py:112-140`, `src/cli.py:95-119`, `src/server.py:902-1011`
  - Evidence: constructor accepts `max_websocket_connections` and `websocket_frame_idle_timeout`; CLI exposes only `--workers`, `--max-size`, and `--max-header-size`.
  - Detail: default WebSocket budget is `max_workers // 2`; `--workers 1` defaults WebSockets to zero slots. Operators cannot tune WebSocket capacity or incomplete-frame timeout without code/API use.
  - Impact: capacity surprises and limited operational control.
  - Confidence: high

## Concrete Recommendations

1. Add aggregate storage budgets before operational use:
   - `--max-upload-bytes-total`
   - `--max-note-bytes-total`
   - `--max-note-count`
   - retention/TTL for SMUGGLE temp files

2. Add an aggregate in-flight body memory budget now, even before full streaming upload refactor:
   - reserve declared `Content-Length` against a process-wide counter/semaphore before reading body
   - release after request processing
   - return `503` or `413` when the budget is full

3. Reduce slow-body worker exhaustion:
   - make body timeout configurable
   - add minimum body read rate or per-body idle limit
   - count slow-body closes in metrics separately from header timeout

4. Add response transfer protection:
   - set a response send deadline for streamed files
   - consider `socket.sendfile()` where available
   - record stream timeout/abort metrics

5. Replace full listing scans:
   - `INFO`: use `os.scandir()` and apply pagination during iteration where possible
   - Notepad: add pagination and/or maintain a metadata index updated on save/delete

## Quick Wins

- Document `max_workers * max_upload_size` as the real memory planning bound.
- Add CLI flags for WebSocket connection limit and incomplete-frame timeout.
- Add metrics for current upload bytes, upload disk bytes, note count/bytes, and SMUGGLE temp count/bytes.
- Cap SMUGGLE temp artifacts by count/age and clean them periodically.

## Deeper Improvements

- Stream standard uploads to same-directory temp files instead of buffering full bodies.
- Use an indexed Notepad metadata store or append-only manifest to avoid scanning all note files.
- Add a load test profile covering:
  - 10 concurrent max-size uploads
  - max-workers stalled body clients
  - slow download readers
  - 10k upload files and 10k notes list paths

## Open Questions

- What operational memory budget should constrain `--workers` and `--max-size` defaults?
- Should the server enforce disk quotas itself, or rely on Docker/host filesystem quotas?
- Is Notepad intended to support thousands of notes, or should it remain a small scratchpad feature?
- Should SMUGGLE artifacts expire even if never fetched?
