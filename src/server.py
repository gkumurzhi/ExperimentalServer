"""
Main HTTP server with custom method support.
"""

import gzip
import json
import logging
import secrets
import socket
import ssl
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlsplit

from .config import HIDDEN_FILES, __version__
from .handlers import HandlerMixin
from .http import HTTPRequest, HTTPResponse
from .http.io import receive_request as _receive_request_io
from .metrics import MetricsCollector
from .request_pipeline import RequestPipeline, ResponseBuildArgs
from .security.auth import AuthRateLimiter, BasicAuthenticator, generate_random_credentials
from .security.tls_manager import TLSManager
from .websocket import (
    WS_BINARY,
    WS_CLOSE,
    WS_PING,
    WS_PONG,
    WS_TEXT,
    WebSocketProtocolError,
    build_ws_close_frame,
    build_ws_frame,
    build_ws_handshake_response,
    parse_ws_frame,
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
        cors_origin: str | None = None,
        # Advanced upload
        advanced_upload: bool = False,
    ):
        self.host = host
        self.port = port
        self.root_dir = Path(root_dir).resolve()
        self.socket: socket.socket | None = None
        self.max_upload_size = max_upload_size
        self.max_workers = max_workers
        self.running = False
        self.debug = debug
        self.open_browser = open_browser
        self.json_log = json_log
        self.cors_origin = cors_origin or None
        self.advanced_upload_enabled = advanced_upload

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

        # Directory for encrypted notepad blobs, kept separate from uploads/.
        self.notes_dir = self.root_dir / "notes"
        self.notes_dir.mkdir(exist_ok=True)

        # Clean up stale SMUGGLE files from previous sessions
        self._cleanup_old_smuggle_files()

        self.method_handlers = self.build_method_handlers()
        self._request_pipeline = RequestPipeline(self)

    def _setup_auth(self, auth: str | None) -> None:
        """Set up Basic Auth."""
        if not auth:
            return

        if auth == "random":
            username, password = generate_random_credentials()
            self.authenticator = BasicAuthenticator({username: password})
            self._print_generated_credentials(username, password)
        elif ":" in auth:
            username, password = auth.split(":", 1)
            self.authenticator = BasicAuthenticator({username: password})
        else:
            # Username only, password = random
            password = secrets.token_urlsafe(16)
            self.authenticator = BasicAuthenticator({auth: password})
            self._print_generated_credentials(auth, password)

    @staticmethod
    def _print_generated_credentials(username: str, password: str) -> None:
        """Print generated credentials only for an interactive terminal."""
        if not sys.stdout.isatty():
            raise RuntimeError(
                "--auth random refuses to print generated credentials to non-interactive "
                "stdout; pass explicit --auth user:password instead."
            )
        print("\n[AUTH] Generated credentials:")
        print(f"  Username: {username}")
        print(f"  Password: {password}")

    def _setup_logging(self, quiet: bool) -> None:
        """Set up logging."""
        if self.debug:
            level = logging.DEBUG
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

        # Keep streamed files streamed; gzip here would require buffering the
        # entire file before sending it.
        if response.stream_path is not None:
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
        print(f"  File access: uploads/ only ({self.upload_dir})")
        print(f"  Notepad storage: notes/ ({self.notes_dir})")
        print(f"  Max upload: {self.max_upload_size // (1024 * 1024)} MB")
        print(f"  Methods: {', '.join(self.method_handlers.keys())}")
        print(f"  Advanced upload: {'enabled' if self.advanced_upload_enabled else 'disabled'}")

        if self.tls_enabled:
            print(f"\n  [TLS]     certificate: {self._tls.describe()}")

        if self.authenticator:
            print("  [AUTH]    Basic Auth enabled")

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

    def _send_response(
        self,
        response: HTTPResponse,
        client_socket: socket.socket,
        _bld: ResponseBuildArgs,
    ) -> int:
        """Send *response* to *client_socket* and return bytes sent.

        Handles both streamed (file) and buffered (body) responses.
        For streamed responses, ``_bld`` is overridden to close the connection.
        """
        try:
            if response.stream_path is not None:
                _bld_close: ResponseBuildArgs = {**_bld, "keep_alive": False}
                bytes_sent = 0
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
        finally:
            if response.stream_cleanup is not None:
                response.stream_cleanup()
                response.stream_cleanup = None

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
        """Apply response decorations."""
        response.set_header("X-Request-Id", request_id)
        if request.headers.get("x-exphttp-no-gzip", "").lower() in {"1", "true", "yes"}:
            return
        if "gzip" in request.headers.get("accept-encoding", ""):
            self._maybe_gzip_response(response)

    def _build_error_response(self, status: int, message: str) -> HTTPResponse:
        response = HTTPResponse(status)
        response.set_body(
            json.dumps({"error": message, "status": status}),
            "application/json",
        )
        return response

    def _is_websocket_origin_allowed(self, request: HTTPRequest) -> bool:
        """Allow same-origin upgrades by default; cross-origin requires explicit opt-in."""
        origin = request.headers.get("origin", "")
        if not origin:
            return True

        configured_origin = self.cors_origin
        if configured_origin == "*":
            return True

        if configured_origin:
            allowed_origins = {
                item.strip() for item in configured_origin.split(",") if item.strip()
            }
            if origin in allowed_origins:
                return True

        host = request.headers.get("host", "")
        if not host:
            return False

        expected_scheme = "https" if self.tls_enabled else "http"
        parsed = urlsplit(origin)
        expected_origin = f"{expected_scheme}://{host}"
        return (
            parsed.scheme == expected_scheme
            and parsed.netloc == host
            and parsed.path in ("", "/")
            and expected_origin == origin.rstrip("/")
        )

    @staticmethod
    def _is_websocket_upgrade_attempt(request: HTTPRequest) -> bool:
        """Return True when the request appears to target the WebSocket handshake path."""
        return request.path.startswith("/notes/ws") and any(
            (
                request.headers.get("upgrade"),
                request.headers.get("connection"),
                request.headers.get("sec-websocket-key"),
                request.headers.get("sec-websocket-version"),
                request.headers.get("origin"),
            )
        )

    def _process_request(
        self,
        data: bytes,
        client_socket: socket.socket,
        client_address: tuple[str, int],
        request_num: int,
    ) -> bool:
        """Delegate request orchestration to the extracted request pipeline."""
        return self._request_pipeline.process(
            data,
            client_socket,
            client_address,
            request_num,
        )

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
                        frame = parse_ws_frame(buf, require_mask=True)
                    except WebSocketProtocolError:
                        try:
                            sock.sendall(build_ws_close_frame(1002, "Protocol error"))
                        except Exception:
                            pass
                        return
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
