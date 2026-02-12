"""
Base class for HTTP method handlers.
"""

import importlib.resources
import logging
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from ..config import HIDDEN_FILES
from ..http import HTTPResponse, format_file_size

if TYPE_CHECKING:
    import threading

logger = logging.getLogger("httpserver")


def get_package_resource(resource_path: str) -> Path | None:
    """
    Get the path to a package resource.

    Works both in installed-package and dev mode.

    Args:
        resource_path: Path to the resource (e.g. "index.html" or "static/crypto-js.min.js").

    Returns:
        Path to the resource, or None if not found.
    """
    # Try to find in package (installed mode)
    try:
        # Python 3.9+
        files = importlib.resources.files("src.data")
        resource_ref = files.joinpath(resource_path)

        # Check existence via as_file
        with importlib.resources.as_file(resource_ref) as path:
            if path.exists():
                return path
    except (TypeError, FileNotFoundError, ModuleNotFoundError, AttributeError):
        pass

    # Fallback: look relative to src/data (dev mode)
    dev_path = Path(__file__).parent.parent / "data" / resource_path
    if dev_path.exists():
        return dev_path

    return None


class BaseHandler:
    """Base class with shared logic for handlers."""

    # Attributes set from the server
    root_dir: Path
    upload_dir: Path
    method_handlers: dict[str, Callable[..., "HTTPResponse"]]
    sandbox_mode: bool
    opsec_mode: bool
    _temp_smuggle_files: set[str]
    _smuggle_lock: "threading.Lock"

    @staticmethod
    def format_size(size: int) -> str:
        """Format file size to human-readable string."""
        return format_file_size(size)

    def _get_file_path(self, url_path: str, for_sandbox: bool = False) -> Path | None:
        """
        Convert URL path to filesystem path.

        Args:
            url_path: URL request path
            for_sandbox: If True and sandbox_mode is on, restrict access to uploads dir
        """
        if url_path == "/":
            url_path = "/index.html"

        # Strip leading slash and normalize path
        clean_path = url_path.lstrip("/")

        # In sandbox mode, certain operations are restricted to uploads
        if for_sandbox and self.sandbox_mode:
            # Strip uploads/ prefix if present
            if clean_path.startswith("uploads/"):
                clean_path = clean_path[8:]  # len("uploads/") = 8
            elif clean_path.startswith("static/"):
                # static/ — first look in root_dir, then in package
                file_path = (self.root_dir / clean_path).resolve()
                try:
                    file_path.relative_to(self.root_dir / "static")
                except ValueError:
                    pass
                else:
                    if file_path.exists():
                        return file_path
                # Fallback to package resources
                return get_package_resource(clean_path)
            file_path = (self.upload_dir / clean_path).resolve()

            # Verify path is inside upload_dir
            try:
                file_path.relative_to(self.upload_dir)
            except ValueError:
                logger.warning(f"Path traversal blocked: {url_path}")
                return None
        else:
            file_path = (self.root_dir / clean_path).resolve()

            # Verify path is inside root_dir (path traversal protection)
            try:
                file_path.relative_to(self.root_dir)
            except ValueError:
                logger.warning(f"Path traversal blocked: {url_path}")
                return None

            # If file not found in root_dir, try package resources
            # (for index.html and static/)
            if not file_path.exists():
                if clean_path == "index.html" or clean_path.startswith("static/"):
                    package_path = get_package_resource(clean_path)
                    if package_path:
                        return package_path

        return file_path

    def _resolve_safe_path(
        self, clean_path: str, base_dir: Path,
    ) -> Path | None:
        """
        Resolve a clean (no leading slash) path against base_dir.

        Returns resolved Path if it's inside base_dir, or None on traversal
        or symlink access.
        """
        if clean_path:
            raw_path = base_dir / clean_path
            file_path = raw_path.resolve()
        else:
            raw_path = base_dir
            file_path = base_dir.resolve()

        try:
            file_path.relative_to(base_dir)
        except ValueError:
            logger.warning("Path traversal blocked: %s", clean_path)
            return None

        # Block symlinks (defense-in-depth: resolve already catches escapes,
        # but we also refuse to serve symlinks themselves)
        if clean_path and raw_path.is_symlink():
            logger.warning("Symlink access blocked: %s", clean_path)
            return None

        return file_path

    def _is_hidden_file(self, path: str) -> bool:
        """Check if file is hidden."""
        filename = Path(path).name
        return filename in HIDDEN_FILES

    def _error_response(self, status: int, error: str) -> HTTPResponse:
        """Unified JSON error response."""
        import json
        response = HTTPResponse(status)
        response.set_body(
            json.dumps({"error": error, "status": status}),
            "application/json",
        )
        return response

    def _not_found(self, path: str) -> HTTPResponse:
        """404 response."""
        return self._error_response(404, f"File not found: {path}")

    def _method_not_allowed(self, method: str) -> HTTPResponse:
        """405 response for unsupported method."""
        allowed = ", ".join(self.method_handlers.keys())
        response = self._error_response(
            405, f"Method '{method}' not allowed. Allowed: {allowed}",
        )
        response.set_header("Allow", allowed)
        return response

    def _bad_request(self, message: str) -> HTTPResponse:
        """400 response."""
        return self._error_response(400, message)

    def _internal_error(self, message: str) -> HTTPResponse:
        """500 response."""
        return self._error_response(500, message)
