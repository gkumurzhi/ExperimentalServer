"""
Main HTTP server with custom method support.
"""

import gzip
import json
import logging
import os
import re as _re
import secrets
import socket
import ssl
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .config import (
    HIDDEN_FILES,
    OPSEC_METHOD_PREFIXES,
    OPSEC_METHOD_SUFFIXES,
    __version__,
)
from .handlers import HandlerMixin
from .handlers.registry import HandlerRegistry
from .http import HTTPRequest, HTTPResponse
from .http.io import receive_request as _receive_request_io
from .metrics import MetricsCollector
from .security.auth import AuthRateLimiter, BasicAuthenticator, generate_random_credentials
from .security.tls_manager import TLSManager
from .websocket import (
    WS_BINARY,
    WS_CLOSE,
    WS_PING,
    WS_PONG,
    WS_TEXT,
    build_ws_close_frame,
    build_ws_frame,
    build_ws_handshake_response,
    check_websocket_upgrade,
    parse_ws_frame,
)

_NOTE_ID_RE_WS = _re.compile(r"^[a-f0-9]{1,32}$")

# Logging setup
logger = logging.getLogger("httpserver")


class _JSONLogFormatter(logging.Formatter):
    """Structured JSON log formatter."""

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "msg": record.getMessage(),
        }
        if record.exc_info and record.exc_info[1]:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry, ensure_ascii=False)


class ExperimentalHTTPServer(HandlerMixin):
    """HTTP server with custom method support."""

    # Hidden files not accessible via GET
    HIDDEN_FILES = HIDDEN_FILES

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8080,
        root_dir: str = ".",
        opsec_mode: bool = False,
        sandbox_mode: bool = False,
        max_upload_size: int = 100 * 1024 * 1024,  # 100 MB
        max_workers: int = 10,
        quiet: bool = False,
        # TLS options
        tls: bool = False,
        cert_file: str | None = None,
        key_file: str | None = None,
        # Let's Encrypt
        letsencrypt: bool = False,
        domain: str | None = None,
        email: str | None = None,
        # Auth options
        auth: str | None = None,  # "user:password" or "random"
        # Debug
        debug: bool = False,
        # Browser
        open_browser: bool = False,
        # Logging
        json_log: bool = False,
        # CORS
        cors_origin: str = "*",
    ):
        self.host = host
        self.port = port
        self.root_dir = Path(root_dir).resolve()
        self.socket: socket.socket | None = None
        self.opsec_mode = opsec_mode
        self.sandbox_mode = sandbox_mode
        self.max_upload_size = max_upload_size
        self.max_workers = max_workers
        self.running = False
        self.debug = debug
        self.open_browser = open_browser
        self.json_log = json_log
        self.cors_origin = cors_origin

        # TLS settings (delegated to TLSManager; these fields stay as read-only
        # views used by status printing and request handling).
        self._tls = TLSManager(
            enabled=tls,
            cert_file=cert_file,
            key_file=key_file,
            letsencrypt=letsencrypt,
            domain=domain,
            email=email,
            host=host,
        )
        self.letsencrypt = letsencrypt
        self.domain = domain
        self.email = email

        # Temporary SMUGGLE files (deleted after serving)
        self._temp_smuggle_files: set[str] = set()
        self._smuggle_lock = threading.Lock()

        # Notes lock for thread-safe notepad writes
        self._notes_lock = threading.Lock()

        # ECDH key manager for Secure Notepad v2
        self._ecdh_manager = None
        try:
            from .security.keys import ECDHKeyManager

            self._ecdh_manager = ECDHKeyManager()
        except (ImportError, RuntimeError):
            pass

        # In-memory metrics
        self._metrics = MetricsCollector()

        # Basic Auth
        self.authenticator: BasicAuthenticator | None = None
        self._setup_auth(auth)

        # Rate limiting for auth
        self._rate_limiter = AuthRateLimiter() if self.authenticator else None

        # Logging setup
        self._setup_logging(quiet)

        # Directory for uploaded files
        self.upload_dir = self.root_dir / "uploads"
        self.upload_dir.mkdir(exist_ok=True)

        # Clean up stale SMUGGLE files from previous sessions
        self._cleanup_old_smuggle_files()

        # OPSEC: generate random method names on each startup
        self.opsec_methods: dict[str, str] = {}
        if opsec_mode:
            self._generate_opsec_methods()
            logger.debug(f"OPSEC methods generated: {self.opsec_methods}")

        # Register method handlers via registry (exposed as a dict-like Mapping
        # so tests and handlers that expect `self.method_handlers[...]` keep
        # working unchanged).
        self.method_handlers: HandlerRegistry = HandlerRegistry()
        self.method_handlers.register_many(
            {
                "GET": self.handle_get,
                "HEAD": self.handle_head,
                "POST": self.handle_post,
                "PUT": self.handle_none,  # PUT also handles file upload
                "PATCH": self.handle_patch,  # PATCH also handles file upload
                "DELETE": self.handle_delete,
                "OPTIONS": self.handle_options,
                "FETCH": self.handle_fetch,
                "INFO": self.handle_info,
                "PING": self.handle_ping,
                "NONE": self.handle_none,
                "NOTE": self.handle_note,
                "SMUGGLE": self.handle_smuggle,
            }
        )

    def _setup_auth(self, auth: str | None) -> None:
        """Set up Basic Auth."""
        if not auth:
            return

        if auth == "random":
            username, password = generate_random_credentials()
            self.authenticator = BasicAuthenticator({username: password})
            print("\n[AUTH] Generated credentials:")
            print(f"  Username: {username}")
            print(f"  Password: {password}")
        elif ":" in auth:
            username, password = auth.split(":", 1)
            self.authenticator = BasicAuthenticator({username: password})
        else:
            # Username only, password = random
            password = secrets.token_urlsafe(16)
            self.authenticator = BasicAuthenticator({auth: password})
            print(f"\n[AUTH] Generated password for '{auth}': {password}")

    def _setup_logging(self, quiet: bool) -> None:
        """Set up logging."""
        if self.debug:
            level = logging.DEBUG
        elif self.opsec_mode:
            level = logging.ERROR if quiet else logging.WARNING
        else:
            level = logging.WARNING if quiet else logging.INFO

        handler = logging.StreamHandler()
        if self.json_log:
            handler.setFormatter(_JSONLogFormatter())
        else:
            handler.setFormatter(
                logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
            )
        logger.handlers = [handler]
        logger.setLevel(level)

    def _generate_opsec_methods(self) -> None:
        """Generate random method names for OPSEC mode."""
        self.opsec_methods = {
            "upload": self._random_method_name(),
            "download": self._random_method_name(),
            "info": self._random_method_name(),
            "ping": self._random_method_name(),
            "notepad": self._random_method_name(),
        }
        config_path = self.root_dir / ".opsec_config.json"
        fd = os.open(str(config_path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            json.dump(self.opsec_methods, f, indent=2)

    @staticmethod
    def _random_method_name() -> str:
        """Generate a random method name."""
        prefix = secrets.choice(OPSEC_METHOD_PREFIXES)
        suffix = secrets.choice(OPSEC_METHOD_SUFFIXES)
        return f"{prefix}{suffix}" if suffix else prefix

    def _setup_tls(self) -> None:
        """Set up the TLS context (delegated to TLSManager)."""
        self._tls.setup()

    @property
    def tls_enabled(self) -> bool:
        return self._tls.enabled

    @property
    def ssl_context(self) -> ssl.SSLContext | None:
        return self._tls.ssl_context

    @property
    def cert_file(self) -> str | None:
        return self._tls.cert_file

    @property
    def key_file(self) -> str | None:
        return self._tls.key_file

    @property
    def _temp_cert_files(self) -> list[str]:
        return self._tls.temp_cert_files

    def _record_metric(
        self,
        status_code: int,
        response_size: int,
        *,
        error: bool = False,
    ) -> None:
        """Record request metrics (thread-safe)."""
        self._metrics.record(status_code, response_size, error=error)

    def get_metrics(self) -> dict[str, object]:
        """Return current server metrics snapshot."""
        return self._metrics.snapshot()

    # Content types eligible for gzip compression
    _COMPRESSIBLE_TYPES = (
        "text/",
        "application/json",
        "application/javascript",
        "application/xml",
        "application/xhtml+xml",
        "image/svg+xml",
    )

    def _maybe_gzip_response(self, response: HTTPResponse) -> None:
        """Compress the response body with gzip if appropriate."""
        content_type = response.headers.get("Content-Type", "")
        if not any(content_type.startswith(ct) for ct in self._COMPRESSIBLE_TYPES):
            return

        # For streamed files: read into memory, compress, convert to body
        if response.stream_path is not None:
            try:
                raw = response.stream_path.read_bytes()
            except OSError:
                return
            if len(raw) < 256:
                return
            compressed = gzip.compress(raw)
            if len(compressed) >= len(raw):
                return  # no benefit
            response.body = compressed
            response.stream_path = None
            response.set_header("Content-Length", str(len(compressed)))
            response.set_header("Content-Encoding", "gzip")
            response.set_header("Vary", "Accept-Encoding")
            return

        # For body responses
        if len(response.body) < 256:
            return
        compressed = gzip.compress(response.body)
        if len(compressed) >= len(response.body):
            return
        response.body = compressed
        response.set_header("Content-Length", str(len(compressed)))
        response.set_header("Content-Encoding", "gzip")
        response.set_header("Vary", "Accept-Encoding")

    def _cleanup_temp_files(self) -> None:
        """Clean up temporary certificate files."""
        self._tls.cleanup()

    def _cleanup_old_smuggle_files(self) -> None:
        """Clean up stale SMUGGLE files from previous sessions."""
        count = 0
        for file_path in self.upload_dir.glob("smuggle_*.html"):
            try:
                file_path.unlink()
                count += 1
            except OSError:
                pass
        if count > 0:
            logger.info(f"Cleaned up {count} stale SMUGGLE files")

    def start(self) -> None:
        """Start the server."""
        # Set up TLS
        self._setup_tls()

        if self.debug:
            logger.debug("Debug logging enabled")

        self._metrics.mark_started()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, self.port))
        sock.listen(128)
        self.socket = sock
        self.running = True

        protocol = "https" if self.tls_enabled else "http"
        url = f"{protocol}://{self.host}:{self.port}"

        print("=" * 60)
        print(f"  exphttp v{__version__}")
        print(f"  {url}")
        print()
        print(f"  Root directory: {self.root_dir}")
        print(f"  Max upload: {self.max_upload_size // (1024 * 1024)} MB")
        print(f"  Methods: {', '.join(self.method_handlers.keys())}")

        if self.tls_enabled:
            print(f"\n  [TLS]     certificate: {self._tls.describe()}")

        if self.authenticator:
            print("  [AUTH]    Basic Auth enabled")

        if self.sandbox_mode:
            print("  [SANDBOX] access restricted to uploads/")

        if self.opsec_mode:
            print("  [OPSEC]   randomized methods -> .opsec_config.json")
            print(
                f"            upload: {self.opsec_methods['upload']}, "
                f"download: {self.opsec_methods['download']}"
            )
            print(
                f"            info: {self.opsec_methods['info']}, "
                f"ping: {self.opsec_methods['ping']}"
            )

        print("\n  Ctrl+C to stop")
        print("=" * 60)

        if self.open_browser:
            import webbrowser

            webbrowser.open(url)

        executor = ThreadPoolExecutor(max_workers=self.max_workers)
        try:
            while self.running:
                try:
                    sock.settimeout(1.0)  # For graceful shutdown
                    client_socket, client_address = sock.accept()
                    executor.submit(self._handle_client, client_socket, client_address)
                except TimeoutError:
                    continue
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            self.running = False
            executor.shutdown(wait=True, cancel_futures=True)
            sock.close()
            self._cleanup_temp_files()
            # Clean up temp smuggle files
            for path_str in list(self._temp_smuggle_files):
                try:
                    Path(path_str).unlink(missing_ok=True)
                except OSError:
                    pass
            self._temp_smuggle_files.clear()
            print("Server stopped")

    def stop(self) -> None:
        """Stop the server."""
        self.running = False

    # Keep-alive settings
    KEEP_ALIVE_TIMEOUT: int = 15  # seconds idle between requests
    KEEP_ALIVE_MAX: int = 100  # max requests per connection

    def _should_keep_alive(self, request: HTTPRequest) -> bool:
        """Determine whether to keep the connection alive after this request."""
        # OPSEC mode: always close to minimize fingerprint
        if self.opsec_mode:
            return False

        conn_header = request.headers.get("connection", "").lower()
        if conn_header == "close":
            return False

        # HTTP/1.1 defaults to keep-alive; HTTP/1.0 defaults to close
        if request.http_version == "HTTP/1.1":
            return conn_header != "close"
        return conn_header == "keep-alive"

    def _handle_client(self, client_socket: socket.socket, client_address: tuple[str, int]) -> None:
        """Handle a client connection (with keep-alive support)."""
        try:
            # TLS handshake in worker thread (not blocking accept loop)
            if self.tls_enabled and self.ssl_context:
                try:
                    client_socket.settimeout(5.0)
                    client_socket = self.ssl_context.wrap_socket(client_socket, server_side=True)
                except ssl.SSLError as e:
                    logger.debug(f"SSL handshake failed: {e}")
                    client_socket.close()
                    return

            requests_on_conn = 0

            while self.running:
                # For subsequent requests, use keep-alive idle timeout
                idle_timeout = self.KEEP_ALIVE_TIMEOUT if requests_on_conn > 0 else None

                data = self._receive_request(client_socket, idle_timeout=idle_timeout)
                if not data:
                    break

                requests_on_conn += 1
                keep_alive = self._process_request(
                    data,
                    client_socket,
                    client_address,
                    requests_on_conn,
                )
                if not keep_alive:
                    break
        except Exception:
            pass
        finally:
            client_socket.close()

    def _authenticate_request(
        self,
        request: HTTPRequest,
        client_address: tuple[str, int],
    ) -> HTTPResponse | None:
        """Check Basic Auth and rate limiting.

        Returns an error HTTPResponse to send back, or None if auth passed.
        """
        if not self.authenticator:
            return None

        ip = client_address[0]

        if self._rate_limiter and self._rate_limiter.is_blocked(ip):
            logger.warning(f"Rate limited: {ip}")
            response = HTTPResponse(429)
            response.set_body(
                json.dumps({"error": "Too Many Requests", "status": 429}),
                "application/json",
            )
            return response

        auth_header = request.headers.get("authorization")
        if not self.authenticator.authenticate(auth_header):
            if self._rate_limiter:
                self._rate_limiter.record_failure(ip)
            logger.warning(f"Auth rejected: {ip}")
            response = HTTPResponse(401)
            response.set_header(
                "WWW-Authenticate",
                self.authenticator.get_www_authenticate_header(),
            )
            response.set_body(
                json.dumps({"error": "Unauthorized", "status": 401}),
                "application/json",
            )
            return response

        if self._rate_limiter:
            self._rate_limiter.reset(ip)
        return None

    def _dispatch_handler(self, request: HTTPRequest) -> HTTPResponse:
        """Look up and invoke the handler for *request*.method."""
        if self.opsec_mode:
            handler = self._get_opsec_handler(request)
        else:
            handler = self.method_handlers.get(request.method)

        if handler:
            return handler(request)

        if self.opsec_mode:
            response = HTTPResponse(404)
            response.set_body(
                json.dumps({"error": "Not Found", "status": 404}),
                "application/json",
            )
            return response
        return self._method_not_allowed(request.method)

    def _send_response(
        self,
        response: HTTPResponse,
        client_socket: socket.socket,
        _bld: dict,
    ) -> int:
        """Send *response* to *client_socket* and return bytes sent.

        Handles both streamed (file) and buffered (body) responses.
        For streamed responses, ``_bld`` is overridden to close the connection.
        """
        if response.stream_path is not None:
            _bld_close = {**_bld, "keep_alive": False}
            header_bytes = response.build_headers(**_bld_close)
            client_socket.sendall(header_bytes)
            bytes_sent = len(header_bytes)
            with response.stream_path.open("rb") as f:
                while True:
                    chunk = f.read(65536)
                    if not chunk:
                        break
                    client_socket.sendall(chunk)
                    bytes_sent += len(chunk)
            return bytes_sent

        response_bytes = response.build(**_bld)
        client_socket.sendall(response_bytes)
        return len(response_bytes)

    def _check_payload_size(self, request: HTTPRequest) -> HTTPResponse | None:
        """Reject requests whose Content-Length exceeds the configured cap."""
        try:
            content_length = int(request.headers.get("content-length", 0))
        except ValueError:
            return None
        if content_length <= self.max_upload_size:
            return None

        max_mb = self.max_upload_size // (1024 * 1024)
        response = HTTPResponse(413)
        response.set_body(
            json.dumps(
                {
                    "error": f"Payload too large. Max size: {max_mb} MB",
                    "status": 413,
                }
            ),
            "application/json",
        )
        return response

    def _resolve_keep_alive(
        self,
        request: HTTPRequest,
        request_num: int,
    ) -> tuple[bool, int]:
        """Return ``(use_keep_alive, remaining_requests)`` for this connection."""
        want_keep_alive = self._should_keep_alive(request)
        remaining = self.KEEP_ALIVE_MAX - request_num
        return want_keep_alive and remaining > 0, remaining

    def _post_process_response(
        self,
        request: HTTPRequest,
        response: HTTPResponse,
        request_id: str,
    ) -> None:
        """Apply non-OPSEC response decorations (request-id, gzip)."""
        if self.opsec_mode:
            return
        response.set_header("X-Request-Id", request_id)
        if "gzip" in request.headers.get("accept-encoding", ""):
            self._maybe_gzip_response(response)

    def _build_error_response(self, status: int, message: str) -> HTTPResponse:
        response = HTTPResponse(status)
        response.set_body(
            json.dumps({"error": message, "status": status}),
            "application/json",
        )
        return response

    def _process_request(
        self,
        data: bytes,
        client_socket: socket.socket,
        client_address: tuple[str, int],
        request_num: int,
    ) -> bool:
        """Process a single HTTP request; return True to keep the connection alive."""
        start_time = time.monotonic()
        request_id = secrets.token_hex(4)
        _bld = {"opsec_mode": self.opsec_mode, "cors_origin": self.cors_origin}

        try:
            request = HTTPRequest(data)

            use_keep_alive, remaining = self._resolve_keep_alive(request, request_num)
            _bld["keep_alive"] = use_keep_alive
            if use_keep_alive:
                _bld["keep_alive_timeout"] = self.KEEP_ALIVE_TIMEOUT
                _bld["keep_alive_max"] = remaining

            auth_error = self._authenticate_request(request, client_address)
            if auth_error:
                client_socket.sendall(auth_error.build(**_bld))
                return False

            if request.path.startswith("/notes/ws") and check_websocket_upgrade(request):
                self._handle_notepad_ws(client_socket, request)
                return False

            size_error = self._check_payload_size(request)
            if size_error:
                client_socket.sendall(size_error.build(**_bld))
                return False

            response = self._dispatch_handler(request)
            self._post_process_response(request, response, request_id)

            bytes_sent = self._send_response(response, client_socket, _bld)
            self._record_metric(response.status_code, bytes_sent)

            if response.stream_path is not None:
                use_keep_alive = False

            if not self.opsec_mode:
                duration_ms = (time.monotonic() - start_time) * 1000
                logger.info(
                    "[%s] %s - %s %s -> %d (%dms)",
                    request_id,
                    client_address[0],
                    request.method,
                    request.path,
                    response.status_code,
                    duration_ms,
                )

            return use_keep_alive

        except Exception:
            logger.exception(
                "[%s] Request handling error from %s",
                request_id,
                client_address[0],
            )
            self._record_metric(500, 0, error=True)
            msg = "Error" if self.opsec_mode else "Internal Server Error"
            error_response = self._build_error_response(500, msg)
            try:
                client_socket.sendall(error_response.build(**_bld))
            except Exception:
                pass
            return False

    def _receive_request(
        self,
        client_socket: socket.socket,
        idle_timeout: float | None = None,
    ) -> bytes:
        """Delegate to :func:`src.http.io.receive_request`."""
        return _receive_request_io(
            client_socket,
            max_upload_size=self.max_upload_size,
            idle_timeout=idle_timeout,
        )

    def _get_opsec_handler(self, request: HTTPRequest) -> Callable[..., HTTPResponse] | None:
        """Get the handler for OPSEC mode."""
        method = request.method

        # Standard methods always work
        if method in self.method_handlers:
            return self.method_handlers.get(method)

        if method == self.opsec_methods.get("upload"):
            return self.handle_opsec_upload
        elif method == self.opsec_methods.get("download"):
            return self.handle_fetch
        elif method == self.opsec_methods.get("info"):
            return self.handle_info
        elif method == self.opsec_methods.get("ping"):
            return self.handle_ping
        elif method == self.opsec_methods.get("notepad"):
            return self.handle_note

        # Any unknown method in OPSEC mode -> upload
        has_data = (
            request.body
            or request.headers.get("x-d")
            or request.headers.get("x-d-0")
            or request.query_params.get("d")
        )
        if has_data:
            return self.handle_opsec_upload

        return None

    def _handle_notepad_ws(
        self,
        sock: socket.socket,
        request: HTTPRequest,
    ) -> None:
        """Handle a WebSocket connection for real-time notepad streaming."""
        ws_key = request.headers.get("sec-websocket-key", "")
        try:
            sock.sendall(build_ws_handshake_response(ws_key))
        except Exception:
            return

        buf = b""
        try:
            sock.settimeout(60.0)
            while self.running:
                try:
                    chunk = sock.recv(65536)
                    if not chunk:
                        break
                    buf += chunk
                except TimeoutError:
                    # Send ping to keep alive
                    try:
                        sock.sendall(build_ws_frame(b"", opcode=WS_PING))
                    except Exception:
                        break
                    continue

                # Process all complete frames in buffer
                while True:
                    try:
                        frame = parse_ws_frame(buf)
                    except ValueError:
                        try:
                            sock.sendall(build_ws_close_frame(1009, "Message too big"))
                        except Exception:
                            pass
                        return
                    if frame is None:
                        break
                    opcode, payload, consumed = frame
                    buf = buf[consumed:]

                    if opcode == WS_CLOSE:
                        try:
                            sock.sendall(build_ws_close_frame())
                        except Exception:
                            pass
                        return

                    if opcode == WS_PING:
                        try:
                            sock.sendall(build_ws_frame(payload, opcode=WS_PONG))
                        except Exception:
                            return
                        continue

                    if opcode == WS_PONG:
                        continue

                    if opcode in (WS_TEXT, WS_BINARY):
                        self._handle_ws_message(sock, payload)

        except Exception as e:
            logger.debug("WS connection error: %s", e)
        finally:
            try:
                sock.sendall(build_ws_close_frame())
            except Exception:
                pass

    def _handle_ws_message(self, sock: socket.socket, payload: bytes) -> None:
        """Process a single WebSocket JSON message for notepad ops."""
        try:
            msg = json.loads(payload.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._ws_send_json(sock, {"type": "error", "error": "Invalid JSON"})
            return

        msg_type = msg.get("type", "")

        if msg_type == "save":
            self._ws_handle_save(sock, msg)
        elif msg_type == "load":
            self._ws_handle_load(sock, msg)
        elif msg_type == "list":
            # Reuse the existing list handler
            resp = self._note_list()
            result = json.loads(resp.body)
            result["type"] = "list"
            self._ws_send_json(sock, result)
        elif msg_type == "delete":
            note_id = msg.get("id", "")
            if note_id and _NOTE_ID_RE_WS.match(note_id):
                resp = self._note_delete(note_id)
                result = json.loads(resp.body)
                result["type"] = "deleted"
                self._ws_send_json(sock, result)
            else:
                self._ws_send_json(sock, {"type": "error", "error": "Invalid note ID"})
        else:
            self._ws_send_json(sock, {"type": "error", "error": f"Unknown type: {msg_type}"})

    def _ws_handle_save(self, sock: socket.socket, msg: dict) -> None:
        """Handle a WS save message by building a fake HTTP request."""
        title = msg.get("title", "")
        data = msg.get("data", "")
        note_id = msg.get("noteId", "")
        session_id = msg.get("sessionId", "")

        payload = {"title": title, "data": data}
        if note_id:
            payload["id"] = note_id

        body = json.dumps(payload).encode("utf-8")
        # Build minimal raw HTTP for HTTPRequest parser
        headers = f"NOTE /notes HTTP/1.1\r\nContent-Length: {len(body)}\r\n"
        if session_id:
            headers += f"X-Session-Id: {session_id}\r\n"
        raw = headers.encode() + b"\r\n" + body
        req = HTTPRequest(raw)
        resp = self.handle_note(req)
        result = json.loads(resp.body)
        result["type"] = "saved"
        self._ws_send_json(sock, result)

    def _ws_handle_load(self, sock: socket.socket, msg: dict) -> None:
        """Handle a WS load message."""
        note_id = msg.get("id", "")
        if not note_id or not _NOTE_ID_RE_WS.match(note_id):
            self._ws_send_json(sock, {"type": "error", "error": "Invalid note ID"})
            return
        resp = self._note_load(note_id)
        result = json.loads(resp.body)
        result["type"] = "loaded"
        self._ws_send_json(sock, result)

    @staticmethod
    def _ws_send_json(sock: socket.socket, data: dict) -> None:
        """Send a JSON message over WebSocket."""
        frame = build_ws_frame(json.dumps(data).encode("utf-8"))
        try:
            sock.sendall(frame)
        except Exception:
            pass
