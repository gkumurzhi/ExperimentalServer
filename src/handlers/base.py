"""
Базовый класс для обработчиков HTTP-методов.
"""

import importlib.resources
from pathlib import Path
from typing import TYPE_CHECKING

from ..http import HTTPRequest, HTTPResponse, format_file_size, get_safe_path
from ..config import HIDDEN_FILES

if TYPE_CHECKING:
    from ..server import ExperimentalHTTPServer


def get_package_resource(resource_path: str) -> Path | None:
    """
    Получение пути к ресурсу из пакета.

    Работает как в установленном пакете, так и в dev режиме.

    Args:
        resource_path: Путь к ресурсу (например, "index.html" или "static/crypto-js.min.js")

    Returns:
        Path к ресурсу или None если не найден
    """
    # Пробуем найти в пакете (installed mode)
    try:
        # Python 3.9+
        files = importlib.resources.files("src.data")
        resource_ref = files.joinpath(resource_path)

        # Проверяем существование через as_file
        with importlib.resources.as_file(resource_ref) as path:
            if path.exists():
                return path
    except (TypeError, FileNotFoundError, ModuleNotFoundError, AttributeError):
        pass

    # Fallback: ищем относительно src/data (dev mode)
    dev_path = Path(__file__).parent.parent / "data" / resource_path
    if dev_path.exists():
        return dev_path

    return None


class BaseHandler:
    """Базовый класс с общей логикой для обработчиков."""

    # Атрибуты, которые будут установлены из сервера
    root_dir: Path
    upload_dir: Path
    method_handlers: dict
    sandbox_mode: bool
    opsec_mode: bool

    @staticmethod
    def format_size(size: int) -> str:
        """Форматирование размера файла в человекочитаемый вид."""
        return format_file_size(size)

    def _get_file_path(self, url_path: str, for_sandbox: bool = False) -> Path | None:
        """
        Преобразование URL пути в путь файловой системы.

        Args:
            url_path: URL путь запроса
            for_sandbox: Если True и sandbox_mode включён, ограничивает доступ папкой uploads
        """
        if url_path == "/":
            url_path = "/index.html"

        # Убираем начальный слеш и нормализуем путь
        clean_path = url_path.lstrip("/")

        # В sandbox режиме для определённых операций работаем только с uploads
        if for_sandbox and self.sandbox_mode:
            # Убираем префикс uploads/ если он есть
            if clean_path.startswith("uploads/"):
                clean_path = clean_path[8:]  # len("uploads/") = 8
            elif clean_path.startswith("static/"):
                # static/ - сначала ищем в root_dir, потом в пакете
                file_path = (self.root_dir / clean_path).resolve()
                if file_path.exists() and str(file_path).startswith(str(self.root_dir / "static")):
                    return file_path
                # Fallback на ресурсы пакета
                return get_package_resource(clean_path)
            file_path = (self.upload_dir / clean_path).resolve()

            # Проверяем, что путь находится внутри upload_dir
            if not str(file_path).startswith(str(self.upload_dir)):
                return None
        else:
            file_path = (self.root_dir / clean_path).resolve()

            # Проверяем, что путь находится внутри root_dir (защита от path traversal)
            if not str(file_path).startswith(str(self.root_dir)):
                return None

            # Если файл не найден в root_dir, пробуем ресурсы пакета
            # (для index.html и static/)
            if not file_path.exists():
                if clean_path == "index.html" or clean_path.startswith("static/"):
                    package_path = get_package_resource(clean_path)
                    if package_path:
                        return package_path

        return file_path

    def _is_hidden_file(self, path: str) -> bool:
        """Проверка, является ли файл скрытым."""
        filename = Path(path).name
        return filename in HIDDEN_FILES

    def _not_found(self, path: str) -> HTTPResponse:
        """Ответ 404."""
        response = HTTPResponse(404)
        response.set_body(f"File not found: {path}", "text/plain")
        return response

    def _method_not_allowed(self, method: str) -> HTTPResponse:
        """Ответ для неподдерживаемого метода."""
        response = HTTPResponse(405)
        allowed = ", ".join(self.method_handlers.keys())
        response.set_header("Allow", allowed)
        response.set_body(
            f"Method '{method}' not allowed. Allowed methods: {allowed}",
            "text/plain"
        )
        return response

    def _bad_request(self, message: str) -> HTTPResponse:
        """Ответ 400."""
        response = HTTPResponse(400)
        response.set_body(message, "text/plain")
        return response

    def _internal_error(self, message: str) -> HTTPResponse:
        """Ответ 500."""
        response = HTTPResponse(500)
        response.set_body(f"Internal Server Error: {message}", "text/plain")
        return response
