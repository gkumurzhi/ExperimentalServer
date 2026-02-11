"""
Обработчики файловых операций: GET, POST, PUT, FETCH, NONE.
"""

import json
import logging
import mimetypes
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

from ..http import HTTPRequest, HTTPResponse, sanitize_filename, make_unique_filename
from .base import BaseHandler

logger = logging.getLogger("httpserver")

# Паттерн для удаления ссылки на телеграм в OPSEC режиме
TELEGRAM_LINK_PATTERN = re.compile(
    r'<a\s+href="https://t\.me/kgmnotes"[^>]*>.*?</a>',
    re.DOTALL | re.IGNORECASE
)


class FileHandlersMixin(BaseHandler):
    """Миксин с обработчиками файловых операций."""

    # Атрибут для временных SMUGGLE файлов (определён в сервере)
    _temp_smuggle_files: set[str]

    def _process_html_for_opsec(self, content: bytes) -> bytes:
        """
        Обработка HTML для OPSEC режима.
        Удаляет ссылку на телеграм канал автора.
        """
        if not self.opsec_mode:
            return content

        try:
            html = content.decode("utf-8")
            # Удаляем ссылку на телеграм
            html = TELEGRAM_LINK_PATTERN.sub("", html)
            return html.encode("utf-8")
        except UnicodeDecodeError:
            return content

    def handle_get(self, request: HTTPRequest) -> HTTPResponse:
        """Обработка GET-запроса - возвращает содержимое файла."""
        url_path = request.path.lstrip("/")
        logger.debug(f"GET {request.path}")

        # Защита скрытых файлов
        if self._is_hidden_file(request.path):
            return self._not_found(request.path)

        # В sandbox режиме разрешаем доступ к:
        # 1. Корневым файлам (index.html, style.css и т.д.)
        # 2. Папке uploads/
        # 3. Папке static/ (статические ресурсы)
        if self.sandbox_mode:
            # Проверяем, это запрос к uploads, static или к корневому файлу
            if url_path.startswith("uploads/") or url_path == "uploads":
                # Запрос к uploads - используем sandbox логику
                file_path = self._get_file_path(request.path, for_sandbox=True)
            elif url_path.startswith("static/") or url_path == "static":
                # Запрос к static - разрешаем чтение статических файлов
                file_path = self._get_file_path(request.path, for_sandbox=True)
            else:
                # Корневой файл - проверяем что это не попытка выйти за пределы
                file_path = self._get_file_path(request.path, for_sandbox=False)
                # В sandbox режиме запрещаем доступ к поддиректориям кроме uploads и static
                if file_path and "/" in url_path and not url_path.startswith(("uploads", "static")):
                    return self._not_found(request.path)
        else:
            file_path = self._get_file_path(request.path)

        if file_path is None or not file_path.exists():
            return self._not_found(request.path)

        if file_path.is_dir():
            # Пробуем найти index.html в директории
            index_path = file_path / "index.html"
            if index_path.exists():
                file_path = index_path
            else:
                return self._not_found(request.path)

        response = HTTPResponse(200)
        content_type, _ = mimetypes.guess_type(str(file_path))
        content_type = content_type or "application/octet-stream"

        with open(file_path, "rb") as f:
            content = f.read()

        # В OPSEC режиме обрабатываем HTML (удаляем ссылку на телеграм)
        if content_type and content_type.startswith("text/html"):
            content = self._process_html_for_opsec(content)

        response.set_body(content, content_type)

        # Удаляем временные SMUGGLE файлы после отдачи
        file_path_str = str(file_path)
        if file_path_str in self._temp_smuggle_files:
            try:
                file_path.unlink()
                self._temp_smuggle_files.discard(file_path_str)
                logger.debug(f"Smuggle file cleaned up: {file_path.name}")
            except OSError:
                pass  # Файл уже удалён или недоступен

        return response

    def handle_post(self, request: HTTPRequest) -> HTTPResponse:
        """Обработка POST-запроса - загрузка файлов (как NONE/PUT)."""
        return self.handle_none(request)

    def handle_options(self, request: HTTPRequest) -> HTTPResponse:
        """Обработка OPTIONS-запроса для CORS preflight."""
        response = HTTPResponse(204)

        requested_method = request.headers.get("access-control-request-method", "")
        logger.debug(f"OPTIONS preflight: {requested_method}")
        if requested_method:
            if self.opsec_mode:
                # В OPSEC режиме не раскрываем кастомные методы
                allowed = "GET, POST, PUT, OPTIONS"
                if requested_method not in allowed:
                    allowed = f"{allowed}, {requested_method}"
            else:
                allowed = "GET, POST, PUT, FETCH, INFO, PING, NONE, OPTIONS"
                if requested_method not in allowed:
                    allowed = f"{allowed}, {requested_method}"
            response.set_header("Access-Control-Allow-Methods", allowed)

        return response

    def handle_fetch(self, request: HTTPRequest) -> HTTPResponse:
        """Кастомный метод FETCH - скачивание файлов."""
        # В sandbox режиме скачиваем только из uploads
        file_path = self._get_file_path(request.path, for_sandbox=True)

        if file_path is None or not file_path.exists() or file_path.is_dir():
            response = HTTPResponse(404)
            response.set_header("X-Fetch-Status", "file-not-found")
            error_msg = f"Cannot fetch: {request.path}"
            if self.sandbox_mode:
                error_msg += " (sandbox mode: only uploads/ accessible)"
            response.set_body(error_msg, "text/plain")
            return response

        response = HTTPResponse(200)

        with open(file_path, "rb") as f:
            content = f.read()

        content_type, _ = mimetypes.guess_type(str(file_path))
        content_type = content_type or "application/octet-stream"

        logger.debug(f"FETCH {file_path.name} ({len(content)} bytes)")
        response.set_body(content, content_type)
        response.set_header("Content-Disposition", f'attachment; filename="{file_path.name}"')
        response.set_header("X-Fetch-Status", "success")
        response.set_header("X-File-Name", file_path.name)
        response.set_header("X-File-Size", str(len(content)))
        response.set_header(
            "X-File-Modified",
            datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
        )

        return response

    def handle_none(self, request: HTTPRequest) -> HTTPResponse:
        """Кастомный метод NONE - загрузка файлов."""
        filename = request.headers.get("x-file-name", "")
        if filename:
            filename = unquote(filename)
        if not filename:
            path_name = request.path.strip("/")
            if path_name:
                filename = Path(path_name).name
            else:
                filename = f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Безопасное имя файла
        safe_filename = sanitize_filename(filename)

        if not request.body:
            response = HTTPResponse(400)
            response.set_header("X-Upload-Status", "no-data")
            response.set_body(json.dumps({
                "success": False,
                "error": "No file data provided",
                "hint": "Send file content in request body with X-File-Name header"
            }, indent=2), "application/json")
            return response

        file_path = self.upload_dir / safe_filename
        file_path = make_unique_filename(file_path)
        safe_filename = file_path.name

        try:
            with open(file_path, "wb") as f:
                f.write(request.body)

            logger.debug(f"Upload: {safe_filename} ({len(request.body)} bytes)")
            response = HTTPResponse(201)
            response.set_header("X-Upload-Status", "success")
            response.set_header("X-File-Name", safe_filename)
            response.set_header("X-File-Size", str(len(request.body)))
            response.set_header("X-File-Path", f"/uploads/{safe_filename}")

            result = {
                "success": True,
                "filename": safe_filename,
                "size": len(request.body),
                "size_human": self.format_size(len(request.body)),
                "path": f"/uploads/{safe_filename}",
                "uploaded_at": datetime.now().isoformat(),
                "content_type": request.headers.get("content-type", "application/octet-stream"),
            }

            response.set_body(json.dumps(result, indent=2, ensure_ascii=False), "application/json")
            return response

        except Exception as e:
            logger.error(f"Upload failed: {e}")
            response = HTTPResponse(500)
            response.set_header("X-Upload-Status", "error")
            response.set_body(json.dumps({
                "success": False,
                "error": str(e)
            }, indent=2), "application/json")
            return response
