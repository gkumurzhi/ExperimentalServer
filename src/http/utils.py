"""
HTTP utilities.
"""

import secrets
from datetime import datetime
from pathlib import Path


def parse_query_string(path: str) -> tuple[str, dict[str, str]]:
    """
    Parse query string from URL path.

    Args:
        path: URL path with possible query string

    Returns:
        Tuple of (clean path, params dict)
    """
    if "?" not in path:
        return path, {}

    clean_path, query = path.split("?", 1)
    params: dict[str, str] = {}

    for param in query.split("&"):
        if "=" in param:
            key, value = param.split("=", 1)
            params[key] = value
        else:
            params[param] = ""

    return clean_path, params


def sanitize_filename(filename: str, allow_cyrillic: bool = True) -> str:
    """
    Sanitize filename by removing unsafe characters.

    Args:
        filename: Original filename
        allow_cyrillic: Allow Cyrillic characters

    Returns:
        Safe filename
    """
    safe_chars = "._- "

    def is_safe_char(c: str) -> bool:
        if c.isalnum():
            return True
        if c in safe_chars:
            return True
        # Cyrillic (U+0400 - U+04FF)
        if allow_cyrillic and '\u0400' <= c <= '\u04FF':
            return True
        return False

    safe_filename = "".join(c for c in filename if is_safe_char(c))

    # Collapse consecutive dots (protection against ".." in paths)
    while ".." in safe_filename:
        safe_filename = safe_filename.replace("..", ".")

    safe_filename = safe_filename.strip()

    if not safe_filename:
        safe_filename = f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    return safe_filename


def format_file_size(size: int) -> str:
    """
    Format file size to human-readable string.

    Args:
        size: Size in bytes

    Returns:
        Formatted string (e.g. "1.5 MB")
    """
    fsize = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if fsize < 1024:
            return f"{fsize:.1f} {unit}"
        fsize /= 1024
    return f"{fsize:.1f} TB"


def get_safe_path(
    url_path: str,
    base_dir: Path,
    sandbox_dir: Path | None = None
) -> Path | None:
    """
    Safely convert URL path to filesystem path.

    Args:
        url_path: URL request path
        base_dir: Base directory
        sandbox_dir: Sandbox directory (if None, base_dir is used)

    Returns:
        File path or None if path is invalid (path traversal)
    """
    # Strip leading slash and normalize path
    clean_path = url_path.lstrip("/")

    if sandbox_dir:
        # In sandbox mode, restrict to sandbox_dir
        if clean_path.startswith("uploads/"):
            clean_path = clean_path[8:]  # len("uploads/") = 8
        file_path = (sandbox_dir / clean_path).resolve()

        # Verify path is inside sandbox_dir
        if not str(file_path).startswith(str(sandbox_dir)):
            return None
    else:
        file_path = (base_dir / clean_path).resolve()

        # Verify path is inside base_dir (path traversal protection)
        if not str(file_path).startswith(str(base_dir)):
            return None

    return file_path


def make_unique_filename(file_path: Path) -> Path:
    """
    Generate unique filename if file already exists.

    Args:
        file_path: Original file path

    Returns:
        Path with unique name
    """
    if not file_path.exists():
        return file_path

    unique_suffix = secrets.token_hex(4)
    name_parts = file_path.name.rsplit(".", 1)

    if len(name_parts) == 2:
        new_name = f"{name_parts[0]}_{unique_suffix}.{name_parts[1]}"
    else:
        new_name = f"{file_path.name}_{unique_suffix}"

    return file_path.parent / new_name
