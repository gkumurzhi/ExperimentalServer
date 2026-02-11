"""
Обработчик OPSEC загрузки файлов.
"""

import json
import base64
import hashlib
import secrets

from ..http import HTTPRequest, HTTPResponse
from ..security.crypto import xor_decrypt, verify_hmac
from .base import BaseHandler


class OpsecHandlersMixin(BaseHandler):
    """Миксин с OPSEC обработчиками."""

    def handle_opsec_upload(self, request: HTTPRequest) -> HTTPResponse:
        """OPSEC загрузка файлов - скрытый режим."""
        if not request.body:
            response = HTTPResponse(400)
            response.set_body("", "text/plain")
            return response

        filename = None
        file_data = None
        encryption = None
        decrypt_key = None
        hmac_value = None

        try:
            payload = json.loads(request.body.decode("utf-8"))
            if isinstance(payload, dict):
                filename = payload.get("n") or payload.get("name")
                data_b64 = payload.get("d") or payload.get("data")
                encryption = payload.get("e")
                decrypt_key = payload.get("k")
                key_is_base64 = payload.get("kb64", False)  # Флаг что ключ в base64
                hmac_value = payload.get("h") or payload.get("hmac")  # HMAC для проверки

                # Декодируем ключ из base64 если указан флаг
                if decrypt_key and key_is_base64:
                    decrypt_key = base64.b64decode(decrypt_key).decode("utf-8")
                if data_b64:
                    file_data = base64.b64decode(data_b64)
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass

        if file_data is None:
            file_data = request.body

        # Проверка HMAC если указан
        if hmac_value and decrypt_key:
            if not verify_hmac(file_data, decrypt_key, hmac_value):
                response = HTTPResponse(400)
                response.set_body(
                    json.dumps({"ok": False, "err": "hmac"}),
                    "application/json"
                )
                return response

        # Расшифровываем если указан ключ
        if encryption == "xor" and decrypt_key:
            file_data = xor_decrypt(file_data, decrypt_key)

        if not filename:
            data_hash = hashlib.sha256(file_data).hexdigest()[:12]
            filename = f"{data_hash}.bin"

        safe_filename = "".join(c for c in filename if c.isalnum() or c in "._-")
        if not safe_filename:
            safe_filename = f"upload_{secrets.token_hex(6)}"

        file_path = self.upload_dir / safe_filename
        if file_path.exists():
            name_parts = safe_filename.rsplit(".", 1)
            if len(name_parts) == 2:
                safe_filename = f"{name_parts[0]}_{secrets.token_hex(4)}.{name_parts[1]}"
            else:
                safe_filename = f"{safe_filename}_{secrets.token_hex(4)}"
            file_path = self.upload_dir / safe_filename

        try:
            with open(file_path, "wb") as f:
                f.write(file_data)

            response = HTTPResponse(200)
            result = {
                "ok": True,
                "id": hashlib.sha256(safe_filename.encode()).hexdigest()[:16],
                "sz": len(file_data)
            }
            response.set_body(json.dumps(result), "application/json")
            return response

        except Exception:
            response = HTTPResponse(500)
            response.set_body(json.dumps({"ok": False}), "application/json")
            return response
