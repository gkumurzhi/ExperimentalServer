"""
File operation handlers: GET, POST, PUT, FETCH, NONE.
"""

import json
import logging
import mimetypes
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

from ..http import HTTPRequest, HTTPResponse, make_unique_filename, sanitize_filename
from .base import BaseHandler

logger = logging.getLogger("httpserver")

# Pattern to remove Telegram link in OPSEC mode
TELEGRAM_LINK_PATTERN = re.compile(
    r'<a\s+href="https://t\.me/kgmnotes"[^>]*>.*?</a>',
    re.DOTALL | re.IGNORECASE
)


class FileHandlersMixin(BaseHandler):
    """Mixin with file operation handlers."""

    # Attribute for temporary SMUGGLE files (defined in the server)
    _temp_smuggle_files: set[str]

    def _process_html_for_opsec(self, content: bytes) -> bytes:
        """
        Process HTML for OPSEC mode.
        Removes the author's Telegram channel link.
        """
        if not self.opsec_mode:
            return content

        try:
            html = content.decode("utf-8")
            # Remove Telegram link
            html = TELEGRAM_LINK_PATTERN.sub("", html)
            return html.encode("utf-8")
        except UnicodeDecodeError:
            return content

    def handle_get(self, request: HTTPRequest) -> HTTPResponse:
        """Handle GET request — return file contents."""
        url_path = request.path.lstrip("/")
        logger.debug(f"GET {request.path}")

        # Hidden file protection
        if self._is_hidden_file(request.path):
            return self._not_found(request.path)

        # In sandbox mode, allow access to:
        # 1. Root files (index.html, style.css, etc.)
        # 2. uploads/ directory
        # 3. static/ directory (static resources)
        if self.sandbox_mode:
            # Check whether the request targets uploads, static, or a root file
            if url_path.startswith("uploads/") or url_path == "uploads":
                # Request to uploads — use sandbox logic
                file_path = self._get_file_path(request.path, for_sandbox=True)
            elif url_path.startswith("static/") or url_path == "static":
                # Request to static — allow reading static files
                file_path = self._get_file_path(request.path, for_sandbox=True)
            else:
                # Root file — verify no path traversal attempt
                file_path = self._get_file_path(request.path, for_sandbox=False)
                # In sandbox mode, deny access to subdirectories other than uploads and static
                if file_path and "/" in url_path and not url_path.startswith(("uploads", "static")):
                    return self._not_found(request.path)
        else:
            file_path = self._get_file_path(request.path)

        if file_path is None or not file_path.exists():
            return self._not_found(request.path)

        if file_path.is_dir():
            # Try to find index.html in the directory
            index_path = file_path / "index.html"
            if index_path.exists():
                file_path = index_path
            else:
                return self._not_found(request.path)

        response = HTTPResponse(200)
        content_type, _ = mimetypes.guess_type(str(file_path))
        content_type = content_type or "application/octet-stream"

        # Check if this is a temp smuggle file (must read fully for cleanup)
        file_path_str = str(file_path)
        with self._smuggle_lock:
            is_smuggle = file_path_str in self._temp_smuggle_files

        # HTML files need OPSEC processing; smuggle files need post-send cleanup
        needs_full_read = (
            is_smuggle
            or (content_type and content_type.startswith("text/html") and self.opsec_mode)
        )

        if needs_full_read:
            with file_path.open("rb") as f:
                content = f.read()

            if content_type and content_type.startswith("text/html"):
                content = self._process_html_for_opsec(content)

            response.set_body(content, content_type)

            if is_smuggle:
                try:
                    file_path.unlink()
                    with self._smuggle_lock:
                        self._temp_smuggle_files.discard(file_path_str)
                    logger.debug(f"Smuggle file cleaned up: {file_path.name}")
                except OSError:
                    pass
        else:
            # Stream file directly from disk (no full memory copy)
            response.set_file(file_path, content_type)

        # CSP header for HTML responses
        if content_type and content_type.startswith("text/html"):
            response.set_header(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
                "connect-src 'self'",
            )

        return response

    def handle_post(self, request: HTTPRequest) -> HTTPResponse:
        """Handle POST request — delegates to handle_none (file upload).

        POST, PUT, and NONE all use the same file upload logic.
        This allows standard HTTP clients to upload without custom methods.
        """
        return self.handle_none(request)

    def handle_options(self, request: HTTPRequest) -> HTTPResponse:
        """Handle OPTIONS request for CORS preflight."""
        response = HTTPResponse(204)

        requested_method = request.headers.get("access-control-request-method", "")
        logger.debug(f"OPTIONS preflight: {requested_method}")
        if requested_method:
            if self.opsec_mode:
                # In OPSEC mode, do not expose custom methods
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
        """Custom FETCH method — file download."""
        # In sandbox mode, download only from uploads
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

        content_type, _ = mimetypes.guess_type(str(file_path))
        content_type = content_type or "application/octet-stream"

        stat = file_path.stat()
        logger.debug(f"FETCH {file_path.name} ({stat.st_size} bytes)")

        # Stream file directly from disk
        response.set_file(file_path, content_type)
        response.set_header("Content-Disposition", f'attachment; filename="{file_path.name}"')
        response.set_header("X-Fetch-Status", "success")
        response.set_header("X-File-Name", file_path.name)
        response.set_header("X-File-Size", str(stat.st_size))
        response.set_header(
            "X-File-Modified",
            datetime.fromtimestamp(stat.st_mtime).isoformat()
        )

        return response

    def handle_none(self, request: HTTPRequest) -> HTTPResponse:
        """Custom NONE method — file upload."""
        filename = request.headers.get("x-file-name", "")
        if filename:
            filename = unquote(filename)
        if not filename:
            path_name = request.path.strip("/")
            if path_name:
                filename = Path(path_name).name
            else:
                filename = f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Sanitize filename
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
            with file_path.open("wb") as f:
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
            file_path.unlink(missing_ok=True)
            logger.error(f"Upload failed: {e}")
            response = HTTPResponse(500)
            response.set_header("X-Upload-Status", "error")
            response.set_body(json.dumps({
                "success": False,
                "error": str(e)
            }, indent=2), "application/json")
            return response
