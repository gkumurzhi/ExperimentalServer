# Architecture

## Module layout

```
src/
  __main__.py          # python -m src entry point
  cli.py               # argparse
  server.py            # ExperimentalHTTPServer: socket lifecycle + WS helpers
  metrics.py           # MetricsCollector (thread-safe counters)
  notepad_service.py   # NOTE domain logic shared by HTTP and WebSocket
  request_pipeline.py  # auth/dispatch/send orchestration
  config.py            # constants: hidden files, status map
  websocket.py         # RFC 6455 frame parser and handshake
  http/
    request.py         # HTTPRequest parser
    response.py        # HTTPResponse builder
    io.py              # socket reader with Content-Length enforcement
    utils.py           # path helpers + shared descendant resolver
  handlers/
    base.py            # BaseHandler (shared utilities)
    registry.py        # HandlerRegistry (method -> callable)
    files.py           # GET/POST/PUT/DELETE/FETCH/NONE
    info.py            # INFO, PING
    notepad.py         # NOTE HTTP handlers
    advanced_upload.py # advanced upload transports
    smuggle.py         # SMUGGLE (HTML smuggling demo)
  security/
    auth.py            # Basic Auth + rate limiter
    crypto.py          # XOR/HMAC helpers
    keys.py            # ECDH P-256 for Secure Notepad
    tls.py             # cert generation helpers + Let's Encrypt integration
    tls_manager.py     # TLSManager: SSL context lifecycle + temp files
  utils/
    captcha.py         # PIL-free CAPTCHA renderer
    smuggling.py       # HTML smuggling template
```

## Request flow

```mermaid
sequenceDiagram
    Client->>Server: TCP connect (maybe TLS)
    Server->>TLSManager: wrap_socket (if TLS)
    Server->>IO: receive_request()
    IO-->>Server: raw bytes
    Server->>RequestPipeline: process()
    RequestPipeline->>HTTPRequest: parse
    RequestPipeline->>Auth: _authenticate_request()
    RequestPipeline->>WS: check_websocket_upgrade() for /notes/ws
    RequestPipeline->>RequestPipeline: _check_payload_size()
    RequestPipeline->>HandlerRegistry: dispatch
    HandlerRegistry-->>Handler: bound method
    Handler->>NotepadService: NOTE/WS note operations (when applicable)
    Handler-->>RequestPipeline: HTTPResponse
    RequestPipeline->>MetricsCollector: record()
    RequestPipeline-->>Client: response bytes
```

## Concurrency

See [ADR-005](ADR/ADR-005-threadpool-over-asyncio.md). One accept loop,
`ThreadPoolExecutor` pool (10 workers by default), keep-alive per worker.

## Security layers

1. **Transport** — TLS 1.2+ via `TLSManager`.
2. **Authentication** — Basic Auth with PBKDF2-SHA256
   (`BasicAuthenticator`), rate-limited (`AuthRateLimiter`).
3. **Authorisation** — path containment via
   `src.http.utils.resolve_descendant_path()` under
   `BaseHandler._get_file_path()` / `_resolve_safe_path()`, plus
   `HIDDEN_FILES` checks in handler policy.
4. **Upload scope** — all user-visible file reads and writes are constrained
   to `<root>/uploads/`; the built-in UI and `/static/...` are served
   read-only package resources.
5. **Advanced upload** — unknown non-standard methods carrying upload payload
   data are routed to `AdvancedUploadHandlersMixin`, which supports JSON body,
   header, chunked-header, and URL transports.

See the [threat model](threat-model.md) for what each layer buys you.
