"""
Main HTTP server with custom method support.
"""

import atexit
import json
import logging
import os
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
from .http import HTTPRequest, HTTPResponse
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

import re as _re

_NOTE_ID_RE_WS = _re.compile(r"^[a-f0-9]{1,32}$")
from .security.auth import AuthRateLimiter, BasicAuthenticator, generate_random_credentials
from .security.tls import (
    check_cert_needs_renewal,
    check_certbot_available,
    check_openssl_available,
    generate_self_signed_cert,
    obtain_letsencrypt_cert,
)

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

        # TLS settings
        self.tls_enabled = tls
        self.cert_file = cert_file
        self.key_file = key_file
        self.letsencrypt = letsencrypt
        self.domain = domain
        self.email = email
        self.ssl_context: ssl.SSLContext | None = None
        self._temp_cert_files: list[str] = []  # For cleanup of temp files

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
        self._metrics_lock = threading.Lock()
        self._start_time: float = 0.0
        self._request_count: int = 0
        self._error_count: int = 0
        self._bytes_sent: int = 0
        self._status_counts: dict[int, int] = {}

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

        # Register method handlers
        self.method_handlers = {
            "GET": self.handle_get,
            "POST": self.handle_post,
            "PUT": self.handle_none,  # PUT also handles file upload
            "PATCH": self.handle_patch,  # PATCH also handles file upload
            "OPTIONS": self.handle_options,
            "FETCH": self.handle_fetch,
            "INFO": self.handle_info,
            "PING": self.handle_ping,
            "NONE": self.handle_none,
            "NOTE": self.handle_note,
            "SMUGGLE": self.handle_smuggle,
        }

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
            handler.setFormatter(logging.Formatter(
                "%(asctime)s [%(levelname)s] %(message)s",
                datefmt="%H:%M:%S"
            ))
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
        """Set up the TLS context."""
        if not self.tls_enabled:
            return

        # Let's Encrypt
        if self.letsencrypt and self.domain:
            if not check_certbot_available():
                print("[WARNING] certbot not found. Falling back to self-signed certificate.")
                print("  Install certbot: https://certbot.eff.org/")
                # fallthrough to self-signed logic below
            else:
                config_dir = Path.home() / ".exphttp" / "letsencrypt"
                cert_path = config_dir / "live" / self.domain / "fullchain.pem"
                key_path = config_dir / "live" / self.domain / "privkey.pem"

                if not cert_path.exists() or check_cert_needs_renewal(cert_path):
                    print(f"[TLS] Obtaining Let's Encrypt certificate for {self.domain}...")
                    cert_path, key_path = obtain_letsencrypt_cert(
                        domain=self.domain, email=self.email, config_dir=config_dir,
                    )
                    print(f"[TLS] Certificate obtained: {cert_path}")
                else:
                    print(
                        f"[TLS] Using existing Let's Encrypt"
                        f" certificate for {self.domain}"
                    )

                self.cert_file = str(cert_path)
                self.key_file = str(key_path)

        # If no certificate provided, generate a self-signed one
        if not self.cert_file or not self.key_file:
            if not check_openssl_available():
                print("[WARNING] OpenSSL not found. TLS disabled.")
                print("  Install OpenSSL or provide --cert and --key files.")
                self.tls_enabled = False
                return

            print("[TLS] Generating self-signed certificate...")
            cert_path, key_path = generate_self_signed_cert(
                common_name=self.host if self.host != "0.0.0.0" else "localhost"
            )
            self.cert_file = str(cert_path)
            self.key_file = str(key_path)
            self._temp_cert_files = [self.cert_file, self.key_file]

            # Delete temp files on exit
            atexit.register(self._cleanup_temp_files)

        # Create SSL context
        self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.ssl_context.load_cert_chain(self.cert_file, self.key_file)

        # Modern security settings
        self.ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
        self.ssl_context.set_ciphers('ECDHE+AESGCM:DHE+AESGCM:ECDHE+CHACHA20:DHE+CHACHA20')

    def _record_metric(
        self, status_code: int, response_size: int, *, error: bool = False,
    ) -> None:
        """Record request metrics (thread-safe)."""
        with self._metrics_lock:
            self._request_count += 1
            self._bytes_sent += response_size
            self._status_counts[status_code] = (
                self._status_counts.get(status_code, 0) + 1
            )
            if error:
                self._error_count += 1

    def get_metrics(self) -> dict[str, object]:
        """Return current server metrics snapshot."""
        with self._metrics_lock:
            uptime = time.monotonic() - self._start_time if self._start_time else 0
            return {
                "uptime_seconds": round(uptime, 1),
                "total_requests": self._request_count,
                "total_errors": self._error_count,
                "bytes_sent": self._bytes_sent,
                "status_counts": dict(self._status_counts),
            }

    def _cleanup_temp_files(self) -> None:
        """Clean up temporary certificate files."""
        for path in self._temp_cert_files:
            try:
                Path(path).unlink()
            except OSError:
                pass

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

        self._start_time = time.monotonic()
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
        print(f"  Max upload: {self.max_upload_size // (1024*1024)} MB")
        print(f"  Methods: {', '.join(self.method_handlers.keys())}")

        if self.tls_enabled:
            if self.letsencrypt and self.domain:
                cert_info = f"Let's Encrypt ({self.domain})"
            elif self._temp_cert_files:
                cert_info = "self-signed"
            else:
                cert_info = self.cert_file or "unknown"
            print(f"\n  [TLS]     certificate: {cert_info}")

        if self.authenticator:
            print("  [AUTH]    Basic Auth enabled")

        if self.sandbox_mode:
            print("  [SANDBOX] access restricted to uploads/")

        if self.opsec_mode:
            print("  [OPSEC]   randomized methods -> .opsec_config.json")
            print(f"            upload: {self.opsec_methods['upload']}, "
                  f"download: {self.opsec_methods['download']}")
            print(f"            info: {self.opsec_methods['info']}, "
                  f"ping: {self.opsec_methods['ping']}")

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
                    client_socket = self.ssl_context.wrap_socket(
                        client_socket, server_side=True
                    )
                except ssl.SSLError as e:
                    logger.debug(f"SSL handshake failed: {e}")
                    client_socket.close()
                    return

            requests_on_conn = 0

            while self.running:
                # For subsequent requests, use keep-alive idle timeout
                idle_timeout = (
                    self.KEEP_ALIVE_TIMEOUT if requests_on_conn > 0 else None
                )

                data = self._receive_request(client_socket, idle_timeout=idle_timeout)
                if not data:
                    break

                requests_on_conn += 1
                keep_alive = self._process_request(
                    data, client_socket, client_address, requests_on_conn,
                )
                if not keep_alive:
                    break
        except Exception:
            pass
        finally:
            client_socket.close()

    def _process_request(
        self,
        data: bytes,
        client_socket: socket.socket,
        client_address: tuple[str, int],
        request_num: int,
    ) -> bool:
        """
        Process a single HTTP request on the connection.

        Returns True if the connection should be kept alive for more requests.
        """
        start_time = time.monotonic()
        request_id = secrets.token_hex(4)
        _bld = {"opsec_mode": self.opsec_mode, "cors_origin": self.cors_origin}

        try:
            request = HTTPRequest(data)

            # Determine keep-alive intent
            want_keep_alive = self._should_keep_alive(request)
            remaining = self.KEEP_ALIVE_MAX - request_num
            use_keep_alive = want_keep_alive and remaining > 0

            _bld["keep_alive"] = use_keep_alive
            if use_keep_alive:
                _bld["keep_alive_timeout"] = self.KEEP_ALIVE_TIMEOUT
                _bld["keep_alive_max"] = remaining

            # Basic Auth check
            if self.authenticator:
                # Rate limiting check
                if self._rate_limiter and self._rate_limiter.is_blocked(client_address[0]):
                    logger.warning(f"Rate limited: {client_address[0]}")
                    response = HTTPResponse(429)
                    response.set_body(
                        json.dumps({"error": "Too Many Requests", "status": 429}),
                        "application/json",
                    )
                    client_socket.sendall(response.build(**_bld))
                    return False

                auth_header = request.headers.get("authorization")
                if not self.authenticator.authenticate(auth_header):
                    if self._rate_limiter:
                        self._rate_limiter.record_failure(client_address[0])
                    logger.warning(f"Auth rejected: {client_address[0]}")
                    response = HTTPResponse(401)
                    response.set_header(
                        "WWW-Authenticate",
                        self.authenticator.get_www_authenticate_header()
                    )
                    response.set_body(
                        json.dumps({"error": "Unauthorized", "status": 401}),
                        "application/json",
                    )
                    client_socket.sendall(response.build(**_bld))
                    return False

                # Auth successful — reset rate limiter
                if self._rate_limiter:
                    self._rate_limiter.reset(client_address[0])

            # WebSocket upgrade detection for notepad real-time
            if (request.path.startswith("/notes/ws")
                    and check_websocket_upgrade(request)):
                self._handle_notepad_ws(client_socket, request)
                return False  # connection taken over by WS

            # Check Content-Length before processing
            try:
                content_length = int(request.headers.get("content-length", 0))
            except ValueError:
                content_length = 0
            if content_length > self.max_upload_size:
                max_mb = self.max_upload_size // (1024 * 1024)
                response = HTTPResponse(413)
                response.set_body(
                    json.dumps({
                        "error": f"Payload too large. Max size: {max_mb} MB",
                        "status": 413,
                    }),
                    "application/json",
                )
                client_socket.sendall(response.build(**_bld))
                return False

            if self.opsec_mode:
                handler = self._get_opsec_handler(request)
            else:
                handler = self.method_handlers.get(request.method)

            if handler:
                logger.debug(
                    "[%s] %s - %s %s -> %s",
                    request_id, client_address[0], request.method, request.path,
                    getattr(handler, "__name__", "handler"),
                )
                response = handler(request)
            else:
                if self.opsec_mode:
                    response = HTTPResponse(404)
                    response.set_body(
                        json.dumps({"error": "Not Found", "status": 404}),
                        "application/json"
                    )
                else:
                    response = self._method_not_allowed(request.method)

            if not self.opsec_mode:
                response.set_header("X-Request-Id", request_id)

            # Streaming responses always close (simplifies keep-alive logic)
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
                self._record_metric(response.status_code, bytes_sent)
                use_keep_alive = False  # streamed — close connection
            else:
                response_bytes = response.build(**_bld)
                client_socket.sendall(response_bytes)
                self._record_metric(response.status_code, len(response_bytes))

            # Log response status + latency (not in OPSEC mode)
            if not self.opsec_mode:
                duration_ms = (time.monotonic() - start_time) * 1000
                logger.info(
                    "[%s] %s - %s %s -> %d (%dms)",
                    request_id, client_address[0], request.method,
                    request.path, response.status_code, duration_ms,
                )

            return use_keep_alive

        except Exception:
            logger.exception("[%s] Request handling error from %s", request_id, client_address[0])
            self._record_metric(500, 0, error=True)
            error_response = HTTPResponse(500)
            if self.opsec_mode:
                error_response.set_body(
                    json.dumps({"error": "Error", "status": 500}),
                    "application/json"
                )
            else:
                error_response.set_body(
                    json.dumps({"error": "Internal Server Error", "status": 500}),
                    "application/json"
                )
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
        """
        Receive a complete HTTP request.

        Args:
            client_socket: The client socket.
            idle_timeout: If set, use this as the initial socket timeout
                          (for keep-alive idle wait). None uses default 5s.
        """
        chunks: list[bytes] = []
        total_size = 0
        start_time = time.monotonic()
        HEADER_TIMEOUT = 30.0
        BODY_TIMEOUT = 300.0

        # For keep-alive idle wait, use the specified timeout for the first recv
        initial_timeout = idle_timeout if idle_timeout is not None else 5.0
        client_socket.settimeout(initial_timeout)
        headers_received = False
        content_length = 0
        header_end_pos = 0
        first_recv = True

        while True:
            elapsed = time.monotonic() - start_time
            if not headers_received and elapsed > HEADER_TIMEOUT:
                logger.warning(f"Header receive timeout ({elapsed:.0f}s)")
                return b""
            if headers_received and elapsed > HEADER_TIMEOUT + BODY_TIMEOUT:
                logger.warning(f"Body receive timeout ({elapsed:.0f}s)")
                return b""

            try:
                chunk = client_socket.recv(65536)
                if not chunk:
                    break

                # After first data arrives, switch to standard 5s timeout
                if first_recv and idle_timeout is not None:
                    client_socket.settimeout(5.0)
                    first_recv = False

                chunks.append(chunk)
                total_size += len(chunk)

                # DoS protection: max request size
                if total_size > self.max_upload_size + 65536:
                    logger.warning(f"Request too large ({total_size} bytes), dropping")
                    return b""

                if not headers_received:
                    # Join to find header end (headers are small, O(n^2) is negligible)
                    data = b"".join(chunks)
                    if b"\r\n\r\n" in data:
                        header_end_pos = data.find(b"\r\n\r\n")
                        headers_part = data[:header_end_pos].decode("utf-8", errors="replace")

                        for line in headers_part.split("\r\n"):
                            if line.lower().startswith("content-length:"):
                                try:
                                    content_length = int(line.split(":")[1].strip())
                                except ValueError:
                                    content_length = 0
                                break

                        headers_received = True
                        body_received = total_size - header_end_pos - 4
                        if body_received >= content_length:
                            break
                else:
                    # Body phase: just count bytes, no joining needed
                    body_received = total_size - header_end_pos - 4
                    if body_received >= content_length:
                        break

            except TimeoutError:
                if not headers_received:
                    # No data within timeout during header phase — give up
                    break
                # During body phase, continue until total timeout
                continue

        result = b"".join(chunks)
        if result:
            logger.debug(f"Received {len(result)} bytes")
        return result

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
        if request.body:
            return self.handle_opsec_upload

        return None

    def _handle_notepad_ws(
        self, sock: socket.socket, request: HTTPRequest,
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
                    frame = parse_ws_frame(buf)
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
        import base64 as _b64
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
