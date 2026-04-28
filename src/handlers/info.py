"""
Info method handlers: INFO, PING.
"""

import json
import logging
import mimetypes
from datetime import datetime, timezone
from typing import Any

from ..config import __version__
from ..http import HTTPRequest, HTTPResponse
from .base import BaseHandler

logger = logging.getLogger("httpserver")


class InfoHandlersMixin(BaseHandler):
    """Mixin with info method handlers."""

    def handle_info(self, request: HTTPRequest) -> HTTPResponse:
        """Custom INFO method — file/directory information."""
        if self._is_hidden_file(request.path):
            return self._not_found(request.path)

        # For INFO, don't substitute / with index.html
        url_path = request.path
        clean_path = url_path.lstrip("/")

        if clean_path.startswith("uploads/"):
            clean_path = clean_path[8:]
        elif clean_path == "uploads":
            clean_path = ""
        file_path = self._resolve_safe_path(clean_path, self.upload_dir)

        if file_path is None:
            response = HTTPResponse(400)
            response.set_body("Invalid path", "text/plain")
            return response

        is_dir = file_path.is_dir() if file_path.exists() else False
        logger.debug(f"INFO {request.path} -> {'directory' if is_dir else 'file'}")

        if not file_path.exists():
            response = HTTPResponse(404)
            response.set_body(
                json.dumps({"exists": False, "path": request.path}), "application/json"
            )
            return response

        stat = file_path.stat()
        content_type, _ = mimetypes.guess_type(str(file_path))

        info: dict[str, Any] = {
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
            "access_scope": "uploads",
        }

        if file_path.is_dir():
            all_items = [
                {"name": f.name, "is_dir": f.is_dir()}
                for f in sorted(file_path.iterdir())
                if not f.name.startswith(".")
            ]

            # Pagination: ?offset=N&limit=M (defaults: offset=0, limit=100)
            try:
                offset = max(0, int(request.query_params.get("offset", "0")))
            except ValueError:
                offset = 0
            try:
                limit = min(1000, max(1, int(request.query_params.get("limit", "100"))))
            except ValueError:
                limit = 100

            info["total_items"] = len(all_items)
            info["offset"] = offset
            info["limit"] = limit
            info["contents"] = all_items[offset : offset + limit]

        response = HTTPResponse(200)
        response.set_body(json.dumps(info, indent=2, ensure_ascii=False), "application/json")
        return response

    def handle_ping(self, request: HTTPRequest) -> HTTPResponse:
        """Custom PING method — server health check."""
        logger.debug("PING")
        response = HTTPResponse(200)

        ping_info: dict[str, Any] = {
            "status": "pong",
            "server": f"ExperimentalHTTPServer/{__version__}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "supported_methods": list(self.method_handlers.keys()),
            "access_scope": "uploads",
            "advanced_upload": bool(getattr(self, "advanced_upload_enabled", False)),
        }
        get_metrics = getattr(self, "get_metrics", None)
        if callable(get_metrics):
            ping_info["metrics"] = get_metrics()

        response.set_body(json.dumps(ping_info, indent=2), "application/json")
        response.set_header("X-Ping-Response", "pong")
        return response
