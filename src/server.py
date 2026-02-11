"""
Основной HTTP-сервер с поддержкой произвольных методов.
"""

import socket
import ssl
import json
import secrets
import logging
import atexit
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .http import HTTPRequest, HTTPResponse
from .handlers import HandlerMixin
from .security.auth import BasicAuthenticator, generate_random_credentials
from .security.tls import generate_self_signed_cert, check_openssl_available
from .config import (
    ServerConfig,
    HIDDEN_FILES,
    OPSEC_METHOD_PREFIXES,
    OPSEC_METHOD_SUFFIXES,
)

# Настройка логирования
logger = logging.getLogger("httpserver")


class ExperimentalHTTPServer(HandlerMixin):
    """HTTP-сервер с поддержкой произвольных методов."""

    # Скрытые файлы, недоступные через GET
    HIDDEN_FILES = HIDDEN_FILES

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8080,
        root_dir: str = ".",
        opsec_mode: bool = False,
        sandbox_mode: bool = False,
        max_upload_size: int = 100 * 1024 * 1024,  # 100 MB
        max_workers: int = 10,
        quiet: bool = False,
        # TLS options
        tls: bool = False,
        cert_file: str | None = None,
        key_file: str | None = None,
        # Auth options
        auth: str | None = None,  # "user:password" или "random"
    ):
        self.host = host
        self.port = port
        self.root_dir = Path(root_dir).resolve()
        self.socket = None
        self.opsec_mode = opsec_mode
        self.sandbox_mode = sandbox_mode
        self.max_upload_size = max_upload_size
        self.max_workers = max_workers
        self.running = False

        # TLS настройки
        self.tls_enabled = tls
        self.cert_file = cert_file
        self.key_file = key_file
        self.ssl_context: ssl.SSLContext | None = None
        self._temp_cert_files: list[str] = []  # Для очистки временных файлов

        # Временные SMUGGLE файлы (удаляются после отдачи)
        self._temp_smuggle_files: set[str] = set()

        # Basic Auth
        self.authenticator: BasicAuthenticator | None = None
        self._setup_auth(auth)

        # Настройка логирования
        self._setup_logging(quiet)

        # Директория для загруженных файлов
        self.upload_dir = self.root_dir / "uploads"
        self.upload_dir.mkdir(exist_ok=True)

        # Очищаем старые SMUGGLE файлы от предыдущих сессий
        self._cleanup_old_smuggle_files()

        # OPSEC: генерируем случайные имена методов при каждом запуске
        self.opsec_methods: dict[str, str] = {}
        if opsec_mode:
            self._generate_opsec_methods()

        # Регистрируем обработчики методов
        self.method_handlers = {
            "GET": self.handle_get,
            "POST": self.handle_post,
            "PUT": self.handle_none,  # PUT тоже загружает файлы
            "OPTIONS": self.handle_options,
            "FETCH": self.handle_fetch,
            "INFO": self.handle_info,
            "PING": self.handle_ping,
            "NONE": self.handle_none,
            "SMUGGLE": self.handle_smuggle,
        }

    def _setup_auth(self, auth: str | None) -> None:
        """Настройка Basic Auth."""
        if not auth:
            return

        if auth == "random":
            username, password = generate_random_credentials()
            self.authenticator = BasicAuthenticator({username: password})
            print(f"\n[AUTH] Generated credentials:")
            print(f"  Username: {username}")
            print(f"  Password: {password}")
        elif ":" in auth:
            username, password = auth.split(":", 1)
            self.authenticator = BasicAuthenticator({username: password})
        else:
            # Только username, пароль = random
            password = secrets.token_urlsafe(16)
            self.authenticator = BasicAuthenticator({auth: password})
            print(f"\n[AUTH] Generated password for '{auth}': {password}")

    def _setup_logging(self, quiet: bool) -> None:
        """Настройка логирования."""
        level = logging.WARNING if quiet else logging.INFO
        if self.opsec_mode:
            # В OPSEC режиме минимум логов
            level = logging.ERROR if quiet else logging.WARNING

        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%H:%M:%S"
        ))
        logger.handlers = [handler]
        logger.setLevel(level)

    def _generate_opsec_methods(self) -> None:
        """Генерация случайных имён методов для OPSEC режима."""
        self.opsec_methods = {
            "upload": self._random_method_name(),
            "download": self._random_method_name(),
            "info": self._random_method_name(),
            "ping": self._random_method_name(),
        }
        config_path = self.root_dir / ".opsec_config.json"
        fd = os.open(str(config_path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            json.dump(self.opsec_methods, f, indent=2)

    @staticmethod
    def _random_method_name() -> str:
        """Генерация случайного имени метода."""
        prefix = secrets.choice(OPSEC_METHOD_PREFIXES)
        suffix = secrets.choice(OPSEC_METHOD_SUFFIXES)
        return f"{prefix}{suffix}" if suffix else prefix

    def _setup_tls(self) -> None:
        """Настройка TLS контекста."""
        if not self.tls_enabled:
            return

        # Если сертификат не указан, генерируем самоподписный
        if not self.cert_file or not self.key_file:
            if not check_openssl_available():
                print("[WARNING] OpenSSL not found. TLS disabled.")
                print("  Install OpenSSL or provide --cert and --key files.")
                self.tls_enabled = False
                return

            print("[TLS] Generating self-signed certificate...")
            cert_path, key_path = generate_self_signed_cert(
                common_name=self.host if self.host != "0.0.0.0" else "localhost"
            )
            self.cert_file = str(cert_path)
            self.key_file = str(key_path)
            self._temp_cert_files = [self.cert_file, self.key_file]

            # Удаляем временные файлы при выходе
            atexit.register(self._cleanup_temp_files)

        # Создаём SSL контекст
        self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.ssl_context.load_cert_chain(self.cert_file, self.key_file)

        # Современные настройки безопасности
        self.ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
        self.ssl_context.set_ciphers('ECDHE+AESGCM:DHE+AESGCM:ECDHE+CHACHA20:DHE+CHACHA20')

    def _cleanup_temp_files(self) -> None:
        """Очистка временных файлов сертификатов."""
        for path in self._temp_cert_files:
            try:
                os.unlink(path)
            except OSError:
                pass

    def _cleanup_old_smuggle_files(self) -> None:
        """Очистка старых SMUGGLE файлов от предыдущих сессий."""
        count = 0
        for file_path in self.upload_dir.glob("smuggle_*.html"):
            try:
                file_path.unlink()
                count += 1
            except OSError:
                pass
        if count > 0:
            logger.info(f"Очищено {count} старых SMUGGLE файлов")

    def start(self) -> None:
        """Запуск сервера."""
        # Настройка TLS
        self._setup_tls()

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen(5)
        self.running = True

        protocol = "https" if self.tls_enabled else "http"
        print("=" * 60)
        print("Экспериментальный HTTP-сервер запущен")
        print(f"Адрес: {protocol}://{self.host}:{self.port}")
        print(f"Корневая директория: {self.root_dir}")
        print(f"Макс. размер загрузки: {self.max_upload_size // (1024*1024)} MB")
        print(f"Поддерживаемые методы: {', '.join(self.method_handlers.keys())}")

        if self.tls_enabled:
            print("\n[TLS ENABLED]")
            print(f"  Certificate: {self.cert_file}")
            print(f"  Private key: {self.key_file}")
            if self._temp_cert_files:
                print("  (self-signed, temporary)")

        if self.authenticator:
            print("\n[BASIC AUTH ENABLED]")

        if self.sandbox_mode:
            print("\n[SANDBOX MODE ENABLED]")
            print(f"  Доступ ограничен папкой: {self.upload_dir}")
            print("  Файлы загружаются и скачиваются только из uploads/")

        if self.opsec_mode:
            print("\n[OPSEC MODE ENABLED]")
            print(f"  Upload method:   {self.opsec_methods['upload']}")
            print(f"  Download method: {self.opsec_methods['download']}")
            print(f"  Info method:     {self.opsec_methods['info']}")
            print(f"  Ping method:     {self.opsec_methods['ping']}")
            print("  Config saved to: .opsec_config.json")

        print("=" * 60)

        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                while self.running:
                    try:
                        self.socket.settimeout(1.0)  # Для graceful shutdown
                        client_socket, client_address = self.socket.accept()

                        # Оборачиваем в TLS если включено
                        if self.tls_enabled and self.ssl_context:
                            try:
                                client_socket = self.ssl_context.wrap_socket(
                                    client_socket,
                                    server_side=True
                                )
                            except ssl.SSLError as e:
                                logger.debug(f"SSL handshake failed: {e}")
                                client_socket.close()
                                continue

                        executor.submit(self._handle_client, client_socket, client_address)
                    except socket.timeout:
                        continue
        except KeyboardInterrupt:
            print("\nОстановка сервера...")
        finally:
            self.running = False
            self.socket.close()
            self._cleanup_temp_files()
            print("Сервер остановлен")

    def stop(self) -> None:
        """Остановка сервера."""
        self.running = False

    def _handle_client(self, client_socket: socket.socket, client_address: tuple) -> None:
        """Обработка клиентского подключения."""
        try:
            data = self._receive_request(client_socket)
            if not data:
                return

            request = HTTPRequest(data)

            # Basic Auth проверка
            if self.authenticator:
                auth_header = request.headers.get("authorization")
                if not self.authenticator.authenticate(auth_header):
                    response = HTTPResponse(401)
                    response.set_header(
                        "WWW-Authenticate",
                        self.authenticator.get_www_authenticate_header()
                    )
                    response.set_body("Unauthorized", "text/plain")
                    client_socket.sendall(response.build(opsec_mode=self.opsec_mode))
                    return

            # Проверка размера Content-Length до обработки
            try:
                content_length = int(request.headers.get("content-length", 0))
            except ValueError:
                content_length = 0
            if content_length > self.max_upload_size:
                response = HTTPResponse(413)
                response.set_body(
                    f"Payload too large. Max size: {self.max_upload_size // (1024*1024)} MB",
                    "text/plain"
                )
                client_socket.sendall(response.build(opsec_mode=self.opsec_mode))
                return

            # Логирование (не в OPSEC режиме)
            if not self.opsec_mode:
                logger.info(f"{client_address[0]} - {request.method} {request.path}")

            if self.opsec_mode:
                handler = self._get_opsec_handler(request)
            else:
                handler = self.method_handlers.get(request.method)

            if handler:
                response = handler(request)
            else:
                if self.opsec_mode:
                    # В OPSEC режиме не выдаём информацию о методах
                    response = HTTPResponse(404)
                    response.set_body("Not Found", "text/plain")
                else:
                    response = self._method_not_allowed(request.method)

            client_socket.sendall(response.build(opsec_mode=self.opsec_mode))
        except Exception as e:
            logger.error(f"Ошибка обработки запроса: {e}")
            error_response = HTTPResponse(500)
            if self.opsec_mode:
                error_response.set_body("Error", "text/plain")
            else:
                error_response.set_body("Internal Server Error", "text/plain")
            try:
                client_socket.sendall(error_response.build(opsec_mode=self.opsec_mode))
            except Exception:
                pass
        finally:
            client_socket.close()

    def _receive_request(self, client_socket: socket.socket) -> bytes:
        """Получение полного HTTP-запроса."""
        data = b""
        client_socket.settimeout(1.0)

        while True:
            try:
                chunk = client_socket.recv(65536)
                if not chunk:
                    break
                data += chunk

                # Защита от слишком больших запросов (DoS)
                if len(data) > self.max_upload_size + 65536:
                    return b""

                if b"\r\n\r\n" in data:
                    header_end = data.find(b"\r\n\r\n")
                    headers_part = data[:header_end].decode("utf-8", errors="replace")

                    content_length = 0
                    for line in headers_part.split("\r\n"):
                        if line.lower().startswith("content-length:"):
                            try:
                                content_length = int(line.split(":")[1].strip())
                            except ValueError:
                                content_length = 0
                            break

                    body_received = len(data) - header_end - 4
                    if body_received >= content_length:
                        break
            except socket.timeout:
                break

        return data

    def _get_opsec_handler(self, request: HTTPRequest):
        """Получение обработчика в OPSEC режиме."""
        method = request.method

        # Стандартные методы всегда работают
        if method in self.method_handlers:
            return self.method_handlers.get(method)

        if method == self.opsec_methods.get("upload"):
            return self.handle_opsec_upload
        elif method == self.opsec_methods.get("download"):
            return self.handle_fetch
        elif method == self.opsec_methods.get("info"):
            return self.handle_info
        elif method == self.opsec_methods.get("ping"):
            return self.handle_ping

        # Любой неизвестный метод в OPSEC режиме -> upload
        if request.body:
            return self.handle_opsec_upload

        return None
