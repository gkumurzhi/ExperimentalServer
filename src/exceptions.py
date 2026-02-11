"""
Кастомные исключения сервера.
"""


class ServerError(Exception):
    """Базовое исключение сервера."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class PathTraversalError(ServerError):
    """Попытка path traversal атаки."""

    def __init__(self, path: str):
        super().__init__(
            f"Path traversal attempt detected: {path}",
            status_code=403
        )
        self.path = path


class FileNotFoundServerError(ServerError):
    """Файл не найден."""

    def __init__(self, path: str):
        super().__init__(
            f"File not found: {path}",
            status_code=404
        )
        self.path = path


class FileTooLargeError(ServerError):
    """Файл превышает лимит размера."""

    def __init__(self, size: int, max_size: int):
        super().__init__(
            f"File too large: {size} bytes (max: {max_size} bytes)",
            status_code=413
        )
        self.size = size
        self.max_size = max_size


class AuthenticationError(ServerError):
    """Ошибка аутентификации."""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, status_code=401)


class MethodNotAllowedError(ServerError):
    """Метод не поддерживается."""

    def __init__(self, method: str, allowed_methods: list[str] | None = None):
        self.method = method
        self.allowed_methods = allowed_methods or []
        super().__init__(
            f"Method '{method}' not allowed",
            status_code=405
        )


class InvalidRequestError(ServerError):
    """Невалидный запрос."""

    def __init__(self, message: str = "Invalid request"):
        super().__init__(message, status_code=400)


class HMACVerificationError(ServerError):
    """Ошибка проверки HMAC."""

    def __init__(self):
        super().__init__("HMAC verification failed", status_code=400)
