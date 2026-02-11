"""
Обработчики информационных методов: INFO, PING.
"""

import json
import logging
import mimetypes
from datetime import datetime, timezone

from ..http import HTTPRequest, HTTPResponse
from ..config import __version__
from .base import BaseHandler

logger = logging.getLogger("httpserver")


class InfoHandlersMixin(BaseHandler):
    """Миксин с информационными обработчиками."""

    def handle_info(self, request: HTTPRequest) -> HTTPResponse:
        """Кастомный метод INFO - информация о файле."""
        # Для INFO не подменяем / на index.html
        url_path = request.path
        clean_path = url_path.lstrip("/")

        # В sandbox режиме работаем только с uploads
        if self.sandbox_mode:
            # Убираем префикс uploads/ если он есть
            if clean_path.startswith("uploads/"):
                clean_path = clean_path[8:]

            if clean_path:
                file_path = (self.upload_dir / clean_path).resolve()
            else:
                file_path = self.upload_dir.resolve()

            # Проверка path traversal - только внутри upload_dir
            if not str(file_path).startswith(str(self.upload_dir)):
                file_path = None

            base_dir = self.upload_dir
        else:
            if clean_path:
                file_path = (self.root_dir / clean_path).resolve()
            else:
                file_path = self.root_dir.resolve()

            # Проверка path traversal
            if not str(file_path).startswith(str(self.root_dir)):
                file_path = None

            base_dir = self.root_dir

        if file_path is None:
            response = HTTPResponse(400)
            response.set_body("Invalid path", "text/plain")
            return response

        is_dir = file_path.is_dir() if file_path.exists() else False
        logger.debug(f"INFO {request.path} -> {'directory' if is_dir else 'file'}")

        if not file_path.exists():
            response = HTTPResponse(404)
            response.set_body(
                json.dumps({"exists": False, "path": request.path}),
                "application/json"
            )
            return response

        stat = file_path.stat()
        content_type, _ = mimetypes.guess_type(str(file_path))

        info = {
            "exists": True,
            "path": request.path,
            "name": file_path.name,
            "is_file": file_path.is_file(),
            "is_directory": file_path.is_dir(),
            "size": stat.st_size,
            "size_human": self.format_size(stat.st_size),
            "content_type": content_type or "unknown",
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "extension": file_path.suffix,
            "sandbox_mode": self.sandbox_mode,
        }

        if file_path.is_dir() and not self.opsec_mode:
            info["contents"] = [
                {"name": f.name, "is_dir": f.is_dir()}
                for f in sorted(file_path.iterdir())
                if not f.name.startswith(".")
            ]

        response = HTTPResponse(200)
        response.set_body(
            json.dumps(info, indent=2, ensure_ascii=False),
            "application/json"
        )
        return response

    def handle_ping(self, request: HTTPRequest) -> HTTPResponse:
        """Кастомный метод PING - проверка сервера."""
        logger.debug("PING")
        response = HTTPResponse(200)

        if self.opsec_mode:
            info = {
                "status": "pong",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        else:
            info = {
                "status": "pong",
                "server": f"ExperimentalHTTPServer/{__version__}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "supported_methods": list(self.method_handlers.keys()),
                "root_directory": str(self.root_dir),
                "sandbox_mode": self.sandbox_mode,
                "opsec_mode": self.opsec_mode,
            }

        response.set_body(json.dumps(info, indent=2), "application/json")
        response.set_header("X-Ping-Response", "pong")
        return response
