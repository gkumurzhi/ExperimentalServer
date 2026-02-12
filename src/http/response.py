"""
HTTP Response builder.
"""

from datetime import datetime, timezone
from pathlib import Path

from ..config import HTTP_STATUS_MESSAGES, __version__


class HTTPResponse:
    """HTTP response builder."""

    def __init__(self, status_code: int = 200):
        self.status_code = status_code
        self.headers: dict[str, str] = {}
        self.body: bytes = b""
        self.stream_path: Path | None = None

    def set_header(self, key: str, value: str) -> None:
        """Set a response header."""
        self.headers[key] = value

    def set_body(self, body: bytes | str, content_type: str = "text/plain") -> None:
        """Set the response body."""
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.body = body
        self.set_header("Content-Type", content_type)
        self.set_header("Content-Length", str(len(self.body)))

    def set_file(self, file_path: Path, content_type: str) -> None:
        """Set a file for streaming response (no memory copy)."""
        self.stream_path = file_path
        size = file_path.stat().st_size
        self.set_header("Content-Type", content_type)
        self.set_header("Content-Length", str(size))

    def build_headers(
        self,
        opsec_mode: bool = False,
        cors_origin: str = "*",
        keep_alive: bool = False,
        keep_alive_timeout: int = 15,
        keep_alive_max: int = 100,
    ) -> bytes:
        """Build only the HTTP header portion (for streaming)."""
        self._finalize_headers(
            opsec_mode, cors_origin, keep_alive, keep_alive_timeout, keep_alive_max,
        )

        status_message = HTTP_STATUS_MESSAGES.get(self.status_code, "Unknown")
        response = f"HTTP/1.1 {self.status_code} {status_message}\r\n"

        for key, value in self.headers.items():
            response += f"{key}: {value}\r\n"

        response += "\r\n"
        return response.encode("utf-8")

    def build(
        self,
        opsec_mode: bool = False,
        cors_origin: str = "*",
        keep_alive: bool = False,
        keep_alive_timeout: int = 15,
        keep_alive_max: int = 100,
    ) -> bytes:
        """Build the full HTTP response as bytes."""
        return self.build_headers(
            opsec_mode, cors_origin, keep_alive, keep_alive_timeout, keep_alive_max,
        ) + self.body

    def _finalize_headers(
        self,
        opsec_mode: bool,
        cors_origin: str = "*",
        keep_alive: bool = False,
        keep_alive_timeout: int = 15,
        keep_alive_max: int = 100,
    ) -> None:
        """Add standard headers (Server, Date, Connection, CORS)."""
        if opsec_mode:
            self.set_header("Server", "nginx")
        else:
            self.set_header("Server", f"ExperimentalHTTPServer/{__version__}")

        self.set_header(
            "Date",
            datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
        )

        if keep_alive:
            self.set_header("Connection", "keep-alive")
            self.set_header(
                "Keep-Alive", f"timeout={keep_alive_timeout}, max={keep_alive_max}"
            )
        else:
            self.set_header("Connection", "close")

        self._set_cors_headers(opsec_mode, cors_origin)

    def _set_cors_headers(self, opsec_mode: bool, cors_origin: str = "*") -> None:
        """Set CORS headers."""
        if "Access-Control-Allow-Origin" not in self.headers:
            self.set_header("Access-Control-Allow-Origin", cors_origin)

        if "Access-Control-Allow-Methods" not in self.headers:
            if opsec_mode:
                # In OPSEC mode, do not expose all methods
                self.set_header("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, OPTIONS")
            else:
                self.set_header(
                    "Access-Control-Allow-Methods",
                    "GET, POST, PUT, PATCH, FETCH, INFO, PING, NONE, NOTE, OPTIONS"
                )

        if "Access-Control-Allow-Headers" not in self.headers:
            self.set_header("Access-Control-Allow-Headers", "Content-Type, X-File-Name, X-Session-Id")

        if "Access-Control-Expose-Headers" not in self.headers and not opsec_mode:
            self.set_header(
                "Access-Control-Expose-Headers",
                "X-File-Name, X-File-Size, X-File-Path, "
                "X-Upload-Status, X-Fetch-Status, X-Ping-Response",
            )

    def __repr__(self) -> str:
        return f"HTTPResponse(status={self.status_code})"
