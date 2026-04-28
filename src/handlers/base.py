"""
Base class for HTTP method handlers.
"""

import importlib.resources
import json
import logging
from collections.abc import Callable, Mapping
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import TYPE_CHECKING, cast
from urllib.parse import unquote

from ..config import HIDDEN_FILES
from ..http import HTTPResponse, format_file_size
from ..http.utils import resolve_descendant_path

if TYPE_CHECKING:
    import threading

    from ..security.keys import ECDHKeyManager
    from .registry import Handler

logger = logging.getLogger("httpserver")


def _safe_package_resource_parts(resource_path: str) -> tuple[str, ...] | None:
    """Return safe package resource path parts, or None when traversal is attempted."""
    decoded_path = unquote(resource_path)
    if (
        not decoded_path
        or "\\" in decoded_path
        or PurePosixPath(decoded_path).is_absolute()
        or PureWindowsPath(decoded_path).is_absolute()
    ):
        return None

    parts = tuple(decoded_path.split("/"))
    if any(
        part in {"", ".", ".."}
        or PureWindowsPath(part).drive
        or PureWindowsPath(part).root
        for part in parts
    ):
        return None

    return parts


def _contained_resource_path(path: Path, resource_root: Path) -> Path | None:
    """Resolve *path* only when it remains below *resource_root*."""
    try:
        resolved_path = path.resolve()
        resolved_path.relative_to(resource_root.resolve())
    except (OSError, RuntimeError, ValueError):
        return None
    return resolved_path


def get_package_resource(resource_path: str) -> Path | None:
    """
    Get the path to a package resource.

    Works both in installed-package and dev mode.

    Args:
        resource_path: Path to the resource (e.g. "index.html" or "static/crypto-js.min.js").

    Returns:
        Path to the resource, or None if not found.
    """
    safe_parts = _safe_package_resource_parts(resource_path)
    if safe_parts is None:
        logger.warning("Unsafe package resource path blocked: %s", resource_path)
        return None

    # Try to find in package (installed mode)
    try:
        # Python 3.9+
        files = importlib.resources.files("src.data")
        resource_ref = files.joinpath(*safe_parts)

        # Filesystem-backed packages can be contained directly. For
        # importer-backed resources, as_file() may create temporary paths that
        # expire before the response streams, so do not return those here.
        if isinstance(files, Path) and isinstance(resource_ref, Path):
            contained_path = _contained_resource_path(resource_ref, files)
            if contained_path is not None and contained_path.exists():
                return contained_path
    except (
        TypeError,
        FileNotFoundError,
        ModuleNotFoundError,
        AttributeError,
        OSError,
        ValueError,
    ):
        pass

    # Fallback: look relative to src/data (dev mode)
    dev_root = Path(__file__).parent.parent / "data"
    dev_path = _contained_resource_path(dev_root.joinpath(*safe_parts), dev_root)
    if dev_path is not None and dev_path.exists():
        return dev_path

    return None


class BaseHandler:
    """Base class with shared logic for handlers."""

    # Attributes set from the server
    root_dir: Path
    upload_dir: Path
    notes_dir: Path
    method_handlers: Mapping[str, "Handler"]
    advanced_upload_enabled: bool
    _temp_smuggle_files: set[str]
    _smuggle_lock: "threading.Lock"
    _ecdh_manager: "ECDHKeyManager | None"

    @staticmethod
    def format_size(size: int) -> str:
        """Format file size to human-readable string."""
        return format_file_size(size)

    def _get_file_path(self, url_path: str, for_sandbox: bool = False) -> Path | None:
        """
        Convert URL path to filesystem path.

        Args:
            url_path: URL request path
            for_sandbox: If True, restrict access to uploads dir
        """
        if url_path == "/":
            url_path = "/index.html"

        # Strip leading slash and normalize path
        clean_path = url_path.lstrip("/")

        if for_sandbox:
            # Strip uploads/ prefix if present
            if clean_path.startswith("uploads/"):
                clean_path = clean_path[8:]  # len("uploads/") = 8
            elif clean_path == "uploads":
                clean_path = ""
            file_path = resolve_descendant_path(clean_path, self.upload_dir)
            if file_path is None:
                logger.warning(f"Path traversal blocked: {url_path}")
                return None
        else:
            file_path = resolve_descendant_path(clean_path, self.root_dir)
            if file_path is None:
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
        self,
        clean_path: str,
        base_dir: Path,
    ) -> Path | None:
        """
        Resolve a clean (no leading slash) path against base_dir.

        Returns resolved Path if it's inside base_dir, or None on traversal
        or symlink access.
        """
        file_path = resolve_descendant_path(
            clean_path,
            base_dir,
            block_symlinks=True,
        )
        if file_path is None:
            raw_path = base_dir / clean_path if clean_path else base_dir
            if clean_path and raw_path.is_symlink():
                logger.warning("Symlink access blocked: %s", clean_path)
            else:
                logger.warning("Path traversal blocked: %s", clean_path)
            return None

        return file_path

    # Provided by the server
    get_metrics: "Callable[[], dict[str, object]]"

    def _serve_metrics(self) -> "HTTPResponse":
        """Return server metrics as JSON."""
        import json

        metrics = self.get_metrics()
        response = HTTPResponse(200)
        response.set_body(
            json.dumps(metrics, indent=2),
            "application/json",
        )
        response.set_header("Cache-Control", "no-cache")
        return response

    def _is_hidden_file(self, path: str) -> bool:
        """Return True when any URL path segment is hidden or service-owned."""
        normalized = path.replace("\\", "/")
        parts = [part for part in normalized.split("/") if part]
        return any(
            (part not in {".", ".."} and part.startswith(".")) or part in HIDDEN_FILES
            for part in parts
        )

    def _error_response(self, status: int, error: str) -> HTTPResponse:
        """Unified JSON error response."""
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
            405,
            f"Method '{method}' not allowed. Allowed: {allowed}",
        )
        response.set_header("Allow", allowed)
        return response

    def _bad_request(self, message: str) -> HTTPResponse:
        """400 response."""
        return self._error_response(400, message)

    def _internal_error(self, message: str) -> HTTPResponse:
        """500 response."""
        return self._error_response(500, message)

    @staticmethod
    def _coerce_json_object(value: object) -> dict[str, object] | None:
        """Return *value* as a JSON object mapping, else ``None``."""
        if not isinstance(value, dict):
            return None
        if not all(isinstance(key, str) for key in value):
            return None
        return cast(dict[str, object], value)

    def _load_json_object(
        self,
        body: bytes,
    ) -> tuple[dict[str, object] | None, HTTPResponse | None]:
        """Decode *body* as UTF-8 JSON and require an object at the top level."""
        try:
            payload = json.loads(body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None, self._bad_request("Invalid JSON body")

        payload_obj = self._coerce_json_object(payload)
        if payload_obj is None:
            return None, self._bad_request("Expected JSON object")

        return payload_obj, None
