"""
File operation handlers: GET, HEAD, POST, PUT, PATCH, DELETE, FETCH, NONE.
"""

import json
import logging
import mimetypes
import re
from datetime import datetime
from email.utils import formatdate
from pathlib import Path
from urllib.parse import unquote

from ..http import HTTPRequest, HTTPResponse, make_unique_filename, sanitize_filename
from .base import BaseHandler

logger = logging.getLogger("httpserver")

# Pattern to remove Telegram link in OPSEC mode
TELEGRAM_LINK_PATTERN = re.compile(
    r'<a\s+href="https://t\.me/kgmnotes"[^>]*>.*?</a>', re.DOTALL | re.IGNORECASE
)


class FileHandlersMixin(BaseHandler):
    """Mixin with file operation handlers."""

    # Attribute for temporary SMUGGLE files (defined in the server)
    _temp_smuggle_files: set[str]

    @staticmethod
    def _compute_etag(file_path: Path) -> str:
        """Compute a stat-based ETag for a file (no full read needed)."""
        st = file_path.stat()
        return f'"{st.st_size:x}-{st.st_mtime_ns:x}"'

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

    def _resolve_get_path(self, request: HTTPRequest) -> Path | None:
        """Resolve the filesystem path for a GET request.

        Handles sandbox mode restrictions, directory→index.html fallback,
        and hidden file protection.  Returns None when the path should 404.
        """
        url_path = request.path.lstrip("/")

        if self._is_hidden_file(request.path):
            return None

        if self.sandbox_mode:
            if url_path.startswith(("uploads/", "static/")) or url_path in ("uploads", "static"):
                file_path = self._get_file_path(request.path, for_sandbox=True)
            else:
                file_path = self._get_file_path(request.path, for_sandbox=False)
                if file_path and "/" in url_path and not url_path.startswith(("uploads", "static")):
                    return None
        else:
            file_path = self._get_file_path(request.path)

        if file_path is None or not file_path.exists():
            return None

        # Directory → index.html fallback
        if file_path.is_dir():
            index_path = file_path / "index.html"
            return index_path if index_path.exists() else None

        return file_path

    def _serve_file(self, file_path: Path, request: HTTPRequest) -> HTTPResponse:
        """Build a 200 response for *file_path* with ETag, cache, and CSP headers."""
        url_path = request.path.lstrip("/")

        # ETag / conditional request support
        etag = self._compute_etag(file_path)
        st = file_path.stat()
        last_modified = formatdate(st.st_mtime, usegmt=True)

        if_none_match = request.headers.get("if-none-match", "")
        if if_none_match and if_none_match == etag:
            response = HTTPResponse(304)
            response.set_header("ETag", etag)
            response.set_header("Last-Modified", last_modified)
            response.set_header("Cache-Control", "public, max-age=0, must-revalidate")
            return response

        response = HTTPResponse(200)
        content_type, _ = mimetypes.guess_type(str(file_path))
        content_type = content_type or "application/octet-stream"

        # Cache headers
        response.set_header("ETag", etag)
        response.set_header("Last-Modified", last_modified)
        if url_path.startswith("uploads/") or url_path == "uploads":
            response.set_header("Cache-Control", "no-cache")
        else:
            response.set_header("Cache-Control", "public, max-age=0, must-revalidate")

        # Smuggle files and OPSEC HTML need a full read
        file_path_str = str(file_path)
        with self._smuggle_lock:
            is_smuggle = file_path_str in self._temp_smuggle_files

        needs_full_read = is_smuggle or (content_type.startswith("text/html") and self.opsec_mode)

        if needs_full_read:
            content = file_path.read_bytes()
            if content_type.startswith("text/html"):
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
            response.set_file(file_path, content_type)

        # CSP header for HTML responses
        if content_type.startswith("text/html"):
            response.set_header(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
                "connect-src 'self' ws: wss:",
            )

        return response

    def handle_get(self, request: HTTPRequest) -> HTTPResponse:
        """Handle GET request — return file contents."""
        logger.debug(f"GET {request.path}")

        if request.path == "/metrics":
            return self._serve_metrics()

        file_path = self._resolve_get_path(request)
        if file_path is None:
            return self._not_found(request.path)

        return self._serve_file(file_path, request)

    def handle_head(self, request: HTTPRequest) -> HTTPResponse:
        """Handle HEAD request — same as GET but with empty body."""
        response = self.handle_get(request)
        response.body = b""
        response.stream_path = None
        return response

    def handle_delete(self, request: HTTPRequest) -> HTTPResponse:
        """Handle DELETE request — delete file from uploads/."""
        # Always sandbox-restricted
        file_path = self._get_file_path(request.path, for_sandbox=True)

        if file_path is None or not file_path.exists():
            return self._not_found(request.path)

        # Reject directories
        if file_path.is_dir():
            return self._bad_request("Cannot delete directories")

        # Defense in depth: verify path is inside upload_dir
        try:
            file_path.resolve().relative_to(self.upload_dir.resolve())
        except ValueError:
            response = HTTPResponse(403)
            response.set_body(
                json.dumps(
                    {
                        "error": "Cannot delete files outside uploads/",
                        "status": 403,
                    }
                ),
                "application/json",
            )
            return response

        try:
            deleted_name = file_path.name
            file_path.unlink()
            logger.debug(f"DELETE {deleted_name}")
            response = HTTPResponse(200)
            response.set_body(
                json.dumps(
                    {
                        "success": True,
                        "deleted": deleted_name,
                        "path": request.path,
                    }
                ),
                "application/json",
            )
            return response
        except OSError as e:
            return self._internal_error(f"Delete failed: {e}")

    def handle_post(self, request: HTTPRequest) -> HTTPResponse:
        """Handle POST request — delegates to handle_none (file upload).

        POST, PUT, PATCH, and NONE all use the same file upload logic.
        This allows standard HTTP clients to upload without custom methods.
        """
        return self.handle_none(request)

    def handle_patch(self, request: HTTPRequest) -> HTTPResponse:
        """Handle PATCH request — delegates to handle_none (file upload)."""
        return self.handle_none(request)

    def handle_options(self, request: HTTPRequest) -> HTTPResponse:
        """Handle OPTIONS request for CORS preflight."""
        response = HTTPResponse(204)

        requested_method = request.headers.get("access-control-request-method", "")
        logger.debug(f"OPTIONS preflight: {requested_method}")
        if requested_method:
            if self.opsec_mode:
                # In OPSEC mode, do not expose custom methods
                allowed = "GET, POST, PUT, PATCH, OPTIONS"
                if requested_method not in allowed:
                    allowed = f"{allowed}, {requested_method}"
            else:
                allowed = (
                    "GET, HEAD, POST, PUT, PATCH, DELETE, FETCH, INFO, PING, NONE, NOTE, OPTIONS"
                )
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
        response.set_header("X-File-Modified", datetime.fromtimestamp(stat.st_mtime).isoformat())

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
            response.set_body(
                json.dumps(
                    {
                        "success": False,
                        "error": "No file data provided",
                        "hint": "Send file content in request body with X-File-Name header",
                    },
                    indent=2,
                ),
                "application/json",
            )
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
            response.set_body(
                json.dumps({"success": False, "error": str(e)}, indent=2), "application/json"
            )
            return response
