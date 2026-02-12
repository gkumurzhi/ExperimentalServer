"""
HTTP Request parser.
"""

import logging
from urllib.parse import parse_qs, unquote, urlparse

logger = logging.getLogger("httpserver")


class HTTPRequest:
    """HTTP request parser."""

    def __init__(self, raw_data: bytes):
        self.method: str = ""
        self.path: str = ""
        self.query_params: dict[str, str] = {}
        self.http_version: str = ""
        self.headers: dict[str, str] = {}
        self.body: bytes = b""
        self._parse(raw_data)

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
                parts = lines[0].split(" ")
                if len(parts) >= 3:
                    self.method = parts[0]
                    raw_url = parts[1]
                    parsed = urlparse(raw_url)
                    self.path = unquote(parsed.path)
                    # Single-value query params (last value wins)
                    self.query_params = {
                        k: v[-1] for k, v in parse_qs(parsed.query).items()
                    }
                    self.http_version = parts[2]

            # Parse headers
            for line in lines[1:]:
                if ":" in line:
                    key, value = line.split(":", 1)
                    self.headers[key.lower()] = value.strip()

        except Exception as e:
            logger.error(f"Request parsing error: {e}")

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
