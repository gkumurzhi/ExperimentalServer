"""
OPSEC file upload handler.
"""

import base64
import hashlib
import json
import logging
import secrets

from ..http import HTTPRequest, HTTPResponse
from ..security.crypto import decrypt, verify_hmac
from .base import BaseHandler

logger = logging.getLogger("httpserver")


class OpsecHandlersMixin(BaseHandler):
    """Mixin with OPSEC handlers."""

    @staticmethod
    def _urlsafe_b64decode(data: str) -> bytes:
        """Decode URL-safe or standard base64."""
        data = data.replace('-', '+').replace('_', '/')
        padding = 4 - len(data) % 4
        if padding != 4:
            data += '=' * padding
        return base64.b64decode(data)

    def _extract_opsec_payload(self, request: HTTPRequest) -> dict:
        """Extract OPSEC payload from body, headers, or URL params (in priority order)."""

        # 1. Try JSON body (existing behavior)
        if request.body:
            try:
                payload = json.loads(request.body.decode("utf-8"))
                if isinstance(payload, dict) and (payload.get("d") or payload.get("data")):
                    payload["_transport"] = "body"
                    return payload
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
            # Non-JSON body → return as raw body transport
            return {"_transport": "body"}

        # 2. Try HTTP headers (x-d, x-e, x-k, x-n, x-h, x-kb64)
        if request.headers.get("x-d"):
            return {
                "d": request.headers["x-d"],
                "e": request.headers.get("x-e"),
                "k": request.headers.get("x-k"),
                "kb64": request.headers.get("x-kb64", "").lower() in ("1", "true"),
                "n": request.headers.get("x-n"),
                "h": request.headers.get("x-h"),
                "_transport": "headers",
            }

        # 2b. Try chunked headers (x-d-0, x-d-1, ..., x-d-N)
        if request.headers.get("x-d-0"):
            chunks = []
            i = 0
            while request.headers.get(f"x-d-{i}") is not None:
                chunks.append(request.headers[f"x-d-{i}"])
                i += 1
            return {
                "d": "".join(chunks),
                "e": request.headers.get("x-e"),
                "k": request.headers.get("x-k"),
                "kb64": request.headers.get("x-kb64", "").lower() in ("1", "true"),
                "n": request.headers.get("x-n"),
                "h": request.headers.get("x-h"),
                "_transport": "headers",
            }

        # 3. Try URL query params (?d=...&e=...&k=...)
        if request.query_params.get("d"):
            return {
                "d": request.query_params["d"],
                "e": request.query_params.get("e"),
                "k": request.query_params.get("k"),
                "kb64": request.query_params.get("kb64", "").lower() in ("1", "true"),
                "n": request.query_params.get("n"),
                "h": request.query_params.get("h"),
                "_transport": "url",
            }

        return {}  # No data found

    def handle_opsec_upload(self, request: HTTPRequest) -> HTTPResponse:
        """OPSEC file upload — covert mode."""
        payload = self._extract_opsec_payload(request)

        if not payload:
            response = HTTPResponse(400)
            response.set_body("", "text/plain")
            return response

        transport = payload.get("_transport", "body")
        filename = None
        file_data = None
        encryption = None
        decrypt_key = None
        hmac_value = None

        data_field = payload.get("d") or payload.get("data")
        if data_field:
            filename = payload.get("n") or payload.get("name")
            encryption = payload.get("e")
            decrypt_key = payload.get("k")
            key_is_base64 = payload.get("kb64", False)
            hmac_value = payload.get("h") or payload.get("hmac")

            # Decode key from base64 if flag is set
            if decrypt_key and key_is_base64:
                decrypt_key = base64.b64decode(decrypt_key).decode("utf-8")

            # Decode data using appropriate base64 variant
            if transport == "url":
                file_data = self._urlsafe_b64decode(data_field)
            else:
                file_data = base64.b64decode(data_field)

        if file_data is None:
            if request.body:
                file_data = request.body
            else:
                response = HTTPResponse(400)
                response.set_body("", "text/plain")
                return response

        # Verify HMAC if provided
        if hmac_value and decrypt_key:
            if not verify_hmac(file_data, decrypt_key, hmac_value):
                logger.warning("OPSEC HMAC verification failed")
                response = HTTPResponse(400)
                response.set_body(
                    json.dumps({"ok": False, "err": "hmac"}),
                    "application/json"
                )
                return response

        # Decrypt if key is provided
        if encryption and decrypt_key:
            decrypted = decrypt(file_data, decrypt_key)
            if decrypted is not None:
                file_data = decrypted

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

        logger.debug(
            "OPSEC upload: %s, encrypted=%s, hmac=%s, transport=%s",
            safe_filename, bool(encryption), bool(hmac_value), transport,
        )

        try:
            with file_path.open("wb") as f:
                f.write(file_data)

            response = HTTPResponse(200)
            result = {
                "ok": True,
                "id": hashlib.sha256(safe_filename.encode()).hexdigest()[:16],
                "sz": len(file_data),
                "transport": transport,
            }
            response.set_body(json.dumps(result), "application/json")
            return response

        except Exception as e:
            file_path.unlink(missing_ok=True)
            logger.error(f"OPSEC write failed: {e}")
            response = HTTPResponse(500)
            response.set_body(json.dumps({"ok": False}), "application/json")
            return response
