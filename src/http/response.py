"""
HTTP Response построитель.
"""

from datetime import datetime, timezone

from ..config import HTTP_STATUS_MESSAGES, __version__


class HTTPResponse:
    """Построитель HTTP-ответов."""

    def __init__(self, status_code: int = 200):
        self.status_code = status_code
        self.headers: dict[str, str] = {}
        self.body: bytes = b""

    def set_header(self, key: str, value: str) -> None:
        """Установка заголовка."""
        self.headers[key] = value

    def set_body(self, body: bytes | str, content_type: str = "text/plain") -> None:
        """Установка тела ответа."""
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.body = body
        self.set_header("Content-Type", content_type)
        self.set_header("Content-Length", str(len(self.body)))

    def build(self, opsec_mode: bool = False) -> bytes:
        """Сборка HTTP ответа в байты."""
        status_message = HTTP_STATUS_MESSAGES.get(self.status_code, "Unknown")
        response = f"HTTP/1.1 {self.status_code} {status_message}\r\n"

        # Добавляем стандартные заголовки
        if opsec_mode:
            # В OPSEC режиме маскируемся под nginx
            self.set_header("Server", "nginx")
        else:
            self.set_header("Server", f"ExperimentalHTTPServer/{__version__}")

        self.set_header(
            "Date",
            datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
        )
        self.set_header("Connection", "close")

        # CORS заголовки для работы из браузера
        self._set_cors_headers(opsec_mode)

        for key, value in self.headers.items():
            response += f"{key}: {value}\r\n"

        response += "\r\n"
        return response.encode("utf-8") + self.body

    def _set_cors_headers(self, opsec_mode: bool) -> None:
        """Установка CORS заголовков."""
        if "Access-Control-Allow-Origin" not in self.headers:
            self.set_header("Access-Control-Allow-Origin", "*")

        if "Access-Control-Allow-Methods" not in self.headers:
            if opsec_mode:
                # В OPSEC режиме не раскрываем все методы
                self.set_header("Access-Control-Allow-Methods", "GET, POST, PUT, OPTIONS")
            else:
                self.set_header(
                    "Access-Control-Allow-Methods",
                    "GET, POST, PUT, FETCH, INFO, PING, NONE, OPTIONS"
                )

        if "Access-Control-Allow-Headers" not in self.headers:
            self.set_header("Access-Control-Allow-Headers", "Content-Type, X-File-Name")

        if "Access-Control-Expose-Headers" not in self.headers and not opsec_mode:
            self.set_header(
                "Access-Control-Expose-Headers",
                "X-File-Name, X-File-Size, X-File-Path, X-Upload-Status, X-Fetch-Status, X-Ping-Response"
            )

    def __repr__(self) -> str:
        return f"HTTPResponse(status={self.status_code})"
