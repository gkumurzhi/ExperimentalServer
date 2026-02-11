"""
Обработчик HTML Smuggling.
"""

import json
import logging
import secrets

from ..http import HTTPRequest, HTTPResponse, parse_query_string
from ..utils.smuggling import generate_smuggling_html
from ..utils.captcha import generate_password_captcha
from .base import BaseHandler

logger = logging.getLogger("httpserver")


class SmuggleHandlersMixin(BaseHandler):
    """Миксин с HTML Smuggling обработчиком."""

    # Атрибут для временных SMUGGLE файлов (определён в сервере)
    _temp_smuggle_files: set[str]

    def handle_smuggle(self, request: HTTPRequest) -> HTTPResponse:
        """Кастомный метод SMUGGLE - генерация HTML Smuggling страницы.

        Параметры (query string):
            encrypt=1 - включить XOR шифрование (пароль генерируется на сервере)
        """
        # Парсим query string
        clean_path, params = parse_query_string(request.path)
        encrypt = params.get("encrypt") == "1"

        # В sandbox режиме работаем только с uploads
        file_path = self._get_file_path(clean_path, for_sandbox=True)

        if file_path is None or not file_path.exists() or file_path.is_dir():
            response = HTTPResponse(404)
            response.set_body(json.dumps({
                "error": "File not found",
                "path": clean_path
            }), "application/json")
            return response

        # Генерируем случайный пароль на сервере если запрошено шифрование
        password = None
        password_captcha = None
        if encrypt:
            # 7 символов: только заглавные буквы и цифры
            alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
            password = ''.join(secrets.choice(alphabet) for _ in range(7))
            # Генерируем капчу с паролем
            password_captcha = generate_password_captcha(password)

        logger.debug(f"SMUGGLE {file_path.name}, encrypt={encrypt}")

        # Читаем файл
        with open(file_path, "rb") as f:
            file_data = f.read()

        # Генерируем HTML
        html = generate_smuggling_html(
            file_data=file_data,
            filename=file_path.name,
            password=password,
            password_captcha=password_captcha
        )

        # Сохраняем HTML во временный файл в uploads
        temp_name = f"smuggle_{secrets.token_hex(8)}.html"
        temp_path = self.upload_dir / temp_name
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(html)

        # Регистрируем как временный файл (будет удалён после отдачи)
        self._temp_smuggle_files.add(str(temp_path))

        # Возвращаем URL на временный файл
        response = HTTPResponse(200)
        response.set_body(json.dumps({
            "url": f"/uploads/{temp_name}",
            "file": file_path.name,
            "encrypted": password is not None
        }), "application/json")
        response.set_header("X-Smuggle-URL", f"/uploads/{temp_name}")

        return response
