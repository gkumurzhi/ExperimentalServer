"""
HTTP Request parser.
"""

import logging
import re
from urllib.parse import parse_qs, unquote, urlparse

logger = logging.getLogger("httpserver")

_HTTP_METHOD_RE = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")
_HTTP_VERSION_RE = re.compile(r"^HTTP/\d+\.\d+$")
_REQUEST_TARGET_INVALID_RE = re.compile(r"[\x00-\x20\x7f]")


class HTTPRequest:
    """HTTP request parser."""

    def __init__(self, raw_data: bytes):
        self.method: str = ""
        self.path: str = ""
        self.query_string: str = ""
        self.query_params: dict[str, str] = {}
        self.http_version: str = ""
        self.headers: dict[str, str] = {}
        self.body: bytes = b""
        self.parse_error: str | None = None
        self._parse(raw_data)

    @property
    def is_valid(self) -> bool:
        """Return True when the request line parsed into a usable HTTP request."""
        return self.parse_error is None

    def _parse(self, raw_data: bytes) -> None:
        """Parse raw HTTP data."""
        try:
            # Split headers and body
            if b"\r\n\r\n" in raw_data:
                header_part, self.body = raw_data.split(b"\r\n\r\n", 1)
            else:
                header_part = raw_data
                self.body = b""

            lines = header_part.decode("utf-8").split("\r\n")

            # Parse request line
            if lines:
                self._parse_request_line(lines[0])
            else:
                self.parse_error = "Malformed request line"

            # Parse headers
            for line in lines[1:]:
                if ":" in line:
                    key, value = line.split(":", 1)
                    self.headers[key.lower()] = value.strip()

        except Exception as e:
            self.parse_error = self.parse_error or "Request parse error"
            logger.error(f"Request parsing error: {e}")

    def _parse_request_line(self, request_line: str) -> None:
        """Parse and validate the HTTP request line."""
        parts = request_line.split(" ")
        if len(parts) != 3:
            self.parse_error = "Malformed request line"
            return

        method, raw_url, http_version = parts
        if not _HTTP_METHOD_RE.fullmatch(method):
            self.parse_error = "Invalid HTTP method"
            return
        if not raw_url or _REQUEST_TARGET_INVALID_RE.search(raw_url):
            self.parse_error = "Invalid request target"
            return
        if not _HTTP_VERSION_RE.fullmatch(http_version):
            self.parse_error = "Invalid HTTP version"
            return

        parsed = urlparse(raw_url)
        self.method = method
        self.path = unquote(parsed.path)
        self.query_string = parsed.query
        # Single-value query params (last value wins)
        self.query_params = {k: v[-1] for k, v in parse_qs(parsed.query).items()}
        self.http_version = http_version

    @property
    def content_length(self) -> int:
        """Get Content-Length from headers."""
        try:
            return int(self.headers.get("content-length", 0))
        except ValueError:
            return 0

    @property
    def content_type(self) -> str:
        """Get Content-Type from headers."""
        return self.headers.get("content-type", "application/octet-stream")

    def get_header(self, name: str, default: str = "") -> str:
        """Get header by name (case-insensitive)."""
        return self.headers.get(name.lower(), default)

    def __repr__(self) -> str:
        return f"HTTPRequest(method={self.method!r}, path={self.path!r})"
