"""
Конфигурация сервера.
"""

from dataclasses import dataclass, field
from pathlib import Path

# Версия проекта (единый источник правды)
__version__ = "2.0.0"


@dataclass
class ServerConfig:
    """Конфигурация HTTP-сервера."""

    # Сетевые настройки
    host: str = "127.0.0.1"
    port: int = 8080

    # Пути
    root_dir: Path = field(default_factory=lambda: Path(".").resolve())

    # Лимиты
    max_upload_size: int = 100 * 1024 * 1024  # 100 MB
    max_workers: int = 10
    socket_timeout: float = 1.0
    recv_buffer_size: int = 65536

    # Режимы работы
    opsec_mode: bool = False
    sandbox_mode: bool = False
    quiet: bool = False

    # TLS
    tls_enabled: bool = False
    cert_file: str | None = None
    key_file: str | None = None

    # Аутентификация
    auth: str | None = None  # "user:password" или "random"

    def __post_init__(self):
        """Преобразование типов после инициализации."""
        if isinstance(self.root_dir, str):
            self.root_dir = Path(self.root_dir).resolve()

    @property
    def upload_dir(self) -> Path:
        """Директория для загрузок."""
        return self.root_dir / "uploads"

    @property
    def protocol(self) -> str:
        """Протокол (http/https)."""
        return "https" if self.tls_enabled else "http"

    @property
    def base_url(self) -> str:
        """Базовый URL сервера."""
        return f"{self.protocol}://{self.host}:{self.port}"


# Скрытые файлы, недоступные через GET
HIDDEN_FILES: frozenset[str] = frozenset({
    ".opsec_config.json",
    ".env",
    ".gitignore",
    ".git",
    "__pycache__",
})

# Префиксы для генерации OPSEC методов
OPSEC_METHOD_PREFIXES: tuple[str, ...] = (
    "CHECK", "SYNC", "VERIFY", "UPDATE", "QUERY",
    "REPORT", "SUBMIT", "VALIDATE", "PROCESS", "EXECUTE"
)

OPSEC_METHOD_SUFFIXES: tuple[str, ...] = (
    "DATA", "STATUS", "INFO", "CONTENT", "RESOURCE",
    "ITEM", "OBJECT", "RECORD", "ENTRY", ""
)

# HTTP статус коды
HTTP_STATUS_MESSAGES: dict[int, str] = {
    200: "OK",
    201: "Created",
    204: "No Content",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    413: "Payload Too Large",
    500: "Internal Server Error",
}
