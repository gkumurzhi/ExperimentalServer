"""
HTTP утилиты.
"""

import secrets
from datetime import datetime
from pathlib import Path


def parse_query_string(path: str) -> tuple[str, dict[str, str]]:
    """
    Парсинг query string из пути.

    Args:
        path: URL путь с возможным query string

    Returns:
        Кортеж (чистый путь, словарь параметров)
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
    Очистка имени файла от небезопасных символов.

    Args:
        filename: Исходное имя файла
        allow_cyrillic: Разрешить кириллицу

    Returns:
        Безопасное имя файла
    """
    safe_chars = "._- "

    def is_safe_char(c: str) -> bool:
        if c.isalnum():
            return True
        if c in safe_chars:
            return True
        # Кириллица (U+0400 - U+04FF)
        if allow_cyrillic and '\u0400' <= c <= '\u04FF':
            return True
        return False

    safe_filename = "".join(c for c in filename if is_safe_char(c))

    # Схлопываем последовательные точки (защита от ".." в путях)
    while ".." in safe_filename:
        safe_filename = safe_filename.replace("..", ".")

    safe_filename = safe_filename.strip()

    if not safe_filename:
        safe_filename = f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    return safe_filename


def format_file_size(size: int) -> str:
    """
    Форматирование размера файла в человекочитаемый вид.

    Args:
        size: Размер в байтах

    Returns:
        Форматированная строка (например, "1.5 MB")
    """
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def get_safe_path(
    url_path: str,
    base_dir: Path,
    sandbox_dir: Path | None = None
) -> Path | None:
    """
    Безопасное преобразование URL пути в путь файловой системы.

    Args:
        url_path: URL путь запроса
        base_dir: Базовая директория
        sandbox_dir: Директория для sandbox режима (если None - используется base_dir)

    Returns:
        Путь к файлу или None если путь невалидный (path traversal)
    """
    # Убираем начальный слеш и нормализуем путь
    clean_path = url_path.lstrip("/")

    if sandbox_dir:
        # В sandbox режиме работаем только с sandbox_dir
        if clean_path.startswith("uploads/"):
            clean_path = clean_path[8:]  # len("uploads/") = 8
        file_path = (sandbox_dir / clean_path).resolve()

        # Проверяем, что путь находится внутри sandbox_dir
        if not str(file_path).startswith(str(sandbox_dir)):
            return None
    else:
        file_path = (base_dir / clean_path).resolve()

        # Проверяем, что путь находится внутри base_dir (защита от path traversal)
        if not str(file_path).startswith(str(base_dir)):
            return None

    return file_path


def make_unique_filename(file_path: Path) -> Path:
    """
    Создание уникального имени файла если файл уже существует.

    Args:
        file_path: Исходный путь к файлу

    Returns:
        Путь с уникальным именем
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
