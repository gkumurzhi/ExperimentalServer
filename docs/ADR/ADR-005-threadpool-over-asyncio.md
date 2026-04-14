# ADR-005: ThreadPoolExecutor for concurrency, not asyncio

- **Status:** accepted

## Context

Python offers three mainstream concurrency models for a network server:

1. **Thread-per-connection / ThreadPoolExecutor** — blocking I/O, stdlib
   `socket`, `ssl`, `threading`.
2. **asyncio** — non-blocking I/O, `asyncio.StreamReader/Writer`,
   `asyncio.start_server`, or `uvloop`.
3. **Multiprocessing** — separate processes per request (overkill for
   a file server).

The server's workload is dominated by file I/O (uploads, downloads, CAPTCHA
rendering) and occasional crypto (ECDH, AES-GCM). Target scale is up to
~10 concurrent clients — small teams, research labs, CTFs.

## Decision

Use `ThreadPoolExecutor(max_workers=self.max_workers)` with blocking sockets.

- Default pool size is 10 (tunable via `--max-workers`).
- TLS handshake happens in the worker thread, so a slow handshake does not
  block the accept loop.
- Keep-alive is per-worker — a thread processes all requests on its
  connection until idle timeout or MAX_REQUESTS.

## Consequences

### Positive

- Handlers are written in straight-line, blocking style — much easier to
  read than async coroutines, which matters for a learning-oriented
  project.
- `ssl.SSLContext.wrap_socket` works natively; the async equivalent
  (`asyncio.start_server(ssl=context)`) has historical footguns.
- File I/O uses regular `open()`, `read()`, `write()`; no need for
  `aiofiles` / thread-offload tricks.
- Debugging is straightforward: threads show up in `py-spy`, `gdb` with
  Python extensions, and plain `threading.enumerate()`.

### Negative

- Limited to ~hundreds of concurrent connections before the GIL and
  context-switch overhead dominate. **Not a design target** — a
  production file server at that scale should be behind nginx/Caddy.
- Graceful shutdown is implemented with polling (`settimeout(1.0)` on
  accept) rather than event-driven; the 1-second shutdown latency is a
  known trade-off.
- Some primitives (e.g. the WebSocket notepad) poll their socket — an
  async rewrite could be more efficient, but the complexity cost is not
  justified at current scale.

### If we ever need to revisit

Revisit this ADR when:

- Benchmarks show ThreadPool becomes the bottleneck (GIL contention, not
  I/O).
- A major new feature requires long-lived thousands of concurrent WebSocket
  connections.
- Python's default concurrency model changes (PEP 703 / no-GIL).
