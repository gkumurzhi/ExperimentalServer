"""
HTTP Request парсер.
"""

import logging
from urllib.parse import unquote

logger = logging.getLogger("httpserver")


class HTTPRequest:
    """Парсер HTTP-запросов."""

    def __init__(self, raw_data: bytes):
        self.method: str = ""
        self.path: str = ""
        self.http_version: str = ""
        self.headers: dict[str, str] = {}
        self.body: bytes = b""
        self._parse(raw_data)

    def _parse(self, raw_data: bytes) -> None:
        """Парсинг сырых HTTP данных."""
        try:
            # Разделяем заголовки и тело
            if b"\r\n\r\n" in raw_data:
                header_part, self.body = raw_data.split(b"\r\n\r\n", 1)
            else:
                header_part = raw_data
                self.body = b""

            lines = header_part.decode("utf-8").split("\r\n")

            # Парсим стартовую строку
            if lines:
                parts = lines[0].split(" ")
                if len(parts) >= 3:
                    self.method = parts[0]
                    self.path = unquote(parts[1])
                    self.http_version = parts[2]

            # Парсим заголовки
            for line in lines[1:]:
                if ": " in line:
                    key, value = line.split(": ", 1)
                    self.headers[key.lower()] = value

        except Exception as e:
            logger.error(f"Ошибка парсинга запроса: {e}")

    @property
    def content_length(self) -> int:
        """Получение Content-Length из заголовков."""
        try:
            return int(self.headers.get("content-length", 0))
        except ValueError:
            return 0

    @property
    def content_type(self) -> str:
        """Получение Content-Type из заголовков."""
        return self.headers.get("content-type", "application/octet-stream")

    def get_header(self, name: str, default: str = "") -> str:
        """Получение заголовка по имени (case-insensitive)."""
        return self.headers.get(name.lower(), default)

    def __repr__(self) -> str:
        return f"HTTPRequest(method={self.method!r}, path={self.path!r})"
