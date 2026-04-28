"""
HTML Smuggling handler.
"""

import json
import logging
import secrets

from ..http import HTTPRequest, HTTPResponse
from ..utils.captcha import generate_password_captcha
from ..utils.smuggling import generate_smuggling_html
from .base import BaseHandler

logger = logging.getLogger("httpserver")

SMUGGLE_SOURCE_SIZE_LIMIT = 10 * 1024 * 1024


class SmuggleHandlersMixin(BaseHandler):
    """Mixin with HTML Smuggling handler."""

    smuggle_source_size_limit = SMUGGLE_SOURCE_SIZE_LIMIT

    # Temporary SMUGGLE files attribute (defined in server)
    _temp_smuggle_files: set[str]

    def handle_smuggle(self, request: HTTPRequest) -> HTTPResponse:
        """Custom SMUGGLE method — generate HTML smuggling page.

        Query params:
            encrypt=1 — enable XOR obfuscation (password generated server-side)
        """
        encrypt = request.query_params.get("encrypt") == "1"

        file_path = self._get_file_path(request.path, for_sandbox=True)

        if file_path is None or not file_path.exists() or file_path.is_dir():
            response = HTTPResponse(404)
            response.set_body(
                json.dumps({"error": "File not found", "path": request.path}), "application/json"
            )
            return response

        source_size_limit = self._smuggle_source_size_limit()
        source_size = file_path.stat().st_size
        if source_size > source_size_limit:
            return self._smuggle_too_large_response(source_size, source_size_limit)

        # Generate random password server-side if encryption requested
        password = None
        password_captcha = None
        if encrypt:
            # 7 chars: uppercase letters and digits only
            alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
            password = "".join(secrets.choice(alphabet) for _ in range(7))
            # Generate captcha with the password
            password_captcha = generate_password_captcha(password)

        logger.debug(f"SMUGGLE {file_path.name}, encrypt={encrypt}")

        # Read at most one byte past the cap to avoid a race with file growth after stat().
        with file_path.open("rb") as f:
            file_data = f.read(source_size_limit + 1)
        if len(file_data) > source_size_limit:
            return self._smuggle_too_large_response(len(file_data), source_size_limit)

        # Generate HTML
        html = generate_smuggling_html(
            file_data=file_data,
            filename=file_path.name,
            password=password,
            password_captcha=password_captcha,
        )

        # Save HTML to a temp file in uploads
        temp_name = f"smuggle_{secrets.token_hex(8)}.html"
        temp_path = self.upload_dir / temp_name
        with temp_path.open("w", encoding="utf-8") as f:
            f.write(html)

        # Register as temp file (will be deleted after serving)
        with self._smuggle_lock:
            self._temp_smuggle_files.add(str(temp_path))

        # Return URL to the temp file
        response = HTTPResponse(200)
        response.set_body(
            json.dumps(
                {
                    "url": f"/uploads/{temp_name}",
                    "file": file_path.name,
                    "encrypted": password is not None,
                }
            ),
            "application/json",
        )
        response.set_header("X-Smuggle-URL", f"/uploads/{temp_name}")

        return response

    def _smuggle_source_size_limit(self) -> int:
        """Return the effective SMUGGLE source cap in bytes."""
        configured_limit = int(
            getattr(self, "smuggle_source_size_limit", SMUGGLE_SOURCE_SIZE_LIMIT)
        )
        upload_limit = int(getattr(self, "max_upload_size", configured_limit))
        return min(configured_limit, upload_limit)

    def _smuggle_too_large_response(self, source_size: int, source_size_limit: int) -> HTTPResponse:
        """Build a stable JSON 413 response for over-limit SMUGGLE sources."""
        response = HTTPResponse(413)
        response.set_body(
            json.dumps(
                {
                    "error": (
                        "SMUGGLE source too large. "
                        f"Max size: {self.format_size(source_size_limit)}"
                    ),
                    "status": 413,
                    "file_size": source_size,
                    "file_size_human": self.format_size(source_size),
                    "max_size": source_size_limit,
                    "max_size_human": self.format_size(source_size_limit),
                }
            ),
            "application/json",
        )
        return response
