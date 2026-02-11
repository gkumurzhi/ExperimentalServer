"""
HTTP Basic Authentication.
"""

import base64
import hashlib
import secrets
from typing import Callable


def parse_basic_auth(auth_header: str) -> tuple[str, str] | None:
    """
    Парсинг заголовка Authorization для Basic Auth.

    Args:
        auth_header: Значение заголовка Authorization

    Returns:
        Кортеж (username, password) или None если невалидный формат
    """
    if not auth_header:
        return None

    parts = auth_header.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "basic":
        return None

    try:
        decoded = base64.b64decode(parts[1]).decode("utf-8")
        if ":" not in decoded:
            return None
        username, password = decoded.split(":", 1)
        return username, password
    except Exception:
        return None


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    """
    Хеширование пароля с солью (SHA256).

    Args:
        password: Пароль для хеширования
        salt: Соль (если None, генерируется новая)

    Returns:
        Кортеж (хеш, соль)
    """
    if salt is None:
        salt = secrets.token_hex(16)

    salted = f"{salt}{password}".encode("utf-8")
    hashed = hashlib.sha256(salted).hexdigest()
    return hashed, salt


def verify_password(password: str, hashed: str, salt: str) -> bool:
    """
    Проверка пароля.

    Args:
        password: Введённый пароль
        hashed: Сохранённый хеш
        salt: Соль

    Returns:
        True если пароль верный
    """
    computed, _ = hash_password(password, salt)
    return secrets.compare_digest(computed, hashed)


class BasicAuthenticator:
    """
    Класс для HTTP Basic Authentication.

    Поддерживает:
    - Простую проверку username:password
    - Хранение хешированных паролей
    - Callback для кастомной аутентификации
    """

    def __init__(
        self,
        credentials: dict[str, str] | None = None,
        auth_callback: Callable[[str, str], bool] | None = None,
        realm: str = "Restricted Area"
    ):
        """
        Args:
            credentials: Словарь {username: password} (plaintext)
            auth_callback: Функция проверки (username, password) -> bool
            realm: Realm для WWW-Authenticate заголовка
        """
        self.realm = realm
        self.auth_callback = auth_callback

        # Хешируем пароли
        self._credentials: dict[str, tuple[str, str]] = {}  # {user: (hash, salt)}
        if credentials:
            for username, password in credentials.items():
                hashed, salt = hash_password(password)
                self._credentials[username] = (hashed, salt)

    def add_user(self, username: str, password: str) -> None:
        """Добавление пользователя."""
        hashed, salt = hash_password(password)
        self._credentials[username] = (hashed, salt)

    def remove_user(self, username: str) -> None:
        """Удаление пользователя."""
        self._credentials.pop(username, None)

    def authenticate(self, auth_header: str | None) -> bool:
        """
        Проверка аутентификации.

        Args:
            auth_header: Значение заголовка Authorization

        Returns:
            True если аутентификация успешна
        """
        if not auth_header:
            return False

        parsed = parse_basic_auth(auth_header)
        if not parsed:
            return False

        username, password = parsed

        # Кастомный callback
        if self.auth_callback:
            return self.auth_callback(username, password)

        # Проверка по сохранённым credentials
        if username not in self._credentials:
            return False

        hashed, salt = self._credentials[username]
        return verify_password(password, hashed, salt)

    def get_www_authenticate_header(self) -> str:
        """Получение значения заголовка WWW-Authenticate."""
        return f'Basic realm="{self.realm}"'


def generate_random_credentials() -> tuple[str, str]:
    """
    Генерация случайных credentials.

    Returns:
        Кортеж (username, password)
    """
    username = f"user_{secrets.token_hex(4)}"
    password = secrets.token_urlsafe(16)
    return username, password
