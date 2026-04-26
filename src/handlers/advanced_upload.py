"""
Advanced file upload handler.
"""

import base64
import binascii
import hashlib
import json
import logging
import secrets
from typing import Literal, TypedDict

from ..http import HTTPRequest, HTTPResponse
from ..security.crypto import decrypt, verify_hmac
from .base import BaseHandler

logger = logging.getLogger("httpserver")

Transport = Literal["body", "headers", "url"]


class AdvancedUploadPayload(TypedDict, total=False):
    d: str
    data: str
    e: str
    k: str
    kb64: bool
    n: str
    name: str
    h: str
    hmac: str
    _transport: Transport
    _raw_body: bytes


class AdvancedUploadHandlersMixin(BaseHandler):
    """Mixin with advanced upload handlers."""

    @staticmethod
    def _urlsafe_b64decode(data: str) -> bytes:
        """Decode URL-safe or standard base64."""
        data = data.replace("-", "+").replace("_", "/")
        padding = 4 - len(data) % 4
        if padding != 4:
            data += "=" * padding
        try:
            return base64.b64decode(data)
        except (binascii.Error, ValueError):
            return b""

    def _extract_advanced_upload_payload(
        self,
        request: HTTPRequest,
    ) -> tuple[AdvancedUploadPayload | None, HTTPResponse | None]:
        """Extract advanced upload payload from body, headers, or URL params."""

        # 1. Try JSON body.
        if request.body:
            try:
                payload = json.loads(request.body.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return {"_transport": "body", "_raw_body": request.body}, None

            payload_obj = self._coerce_json_object(payload)
            if payload_obj is None:
                return None, self._bad_request("Expected JSON object")

            data_field = payload_obj.get("d")
            if not isinstance(data_field, str) or not data_field:
                data_field = payload_obj.get("data")
                if not isinstance(data_field, str) or not data_field:
                    return None, self._bad_request("Missing 'd' or 'data' in JSON body")

            result: AdvancedUploadPayload = {
                "_transport": "body",
                "d": data_field,
            }
            encryption = payload_obj.get("e")
            if isinstance(encryption, str):
                result["e"] = encryption
            decrypt_key = payload_obj.get("k")
            if isinstance(decrypt_key, str):
                result["k"] = decrypt_key
            filename = payload_obj.get("n")
            if isinstance(filename, str):
                result["n"] = filename
            else:
                alt_filename = payload_obj.get("name")
                if isinstance(alt_filename, str):
                    result["name"] = alt_filename
            hmac_value = payload_obj.get("h")
            if isinstance(hmac_value, str):
                result["h"] = hmac_value
            else:
                alt_hmac = payload_obj.get("hmac")
                if isinstance(alt_hmac, str):
                    result["hmac"] = alt_hmac
            key_is_base64 = payload_obj.get("kb64")
            if isinstance(key_is_base64, bool):
                result["kb64"] = key_is_base64
            return result, None

        # 2. Try HTTP headers (x-d, x-e, x-k, x-n, x-h, x-kb64)
        if request.headers.get("x-d"):
            header_payload: AdvancedUploadPayload = {
                "d": request.headers["x-d"],
                "kb64": request.headers.get("x-kb64", "").lower() in ("1", "true"),
                "_transport": "headers",
            }
            encryption = request.headers.get("x-e")
            if encryption is not None:
                header_payload["e"] = encryption
            decrypt_key = request.headers.get("x-k")
            if decrypt_key is not None:
                header_payload["k"] = decrypt_key
            filename = request.headers.get("x-n")
            if filename is not None:
                header_payload["n"] = filename
            hmac_value = request.headers.get("x-h")
            if hmac_value is not None:
                header_payload["h"] = hmac_value
            return header_payload, None

        # 2b. Try chunked headers (x-d-0, x-d-1, ..., x-d-N)
        if request.headers.get("x-d-0"):
            chunks = []
            i = 0
            while request.headers.get(f"x-d-{i}") is not None:
                chunks.append(request.headers[f"x-d-{i}"])
                i += 1
            chunked_payload = AdvancedUploadPayload(
                d="".join(chunks),
                kb64=request.headers.get("x-kb64", "").lower() in ("1", "true"),
                _transport="headers",
            )
            encryption = request.headers.get("x-e")
            if encryption is not None:
                chunked_payload["e"] = encryption
            decrypt_key = request.headers.get("x-k")
            if decrypt_key is not None:
                chunked_payload["k"] = decrypt_key
            filename = request.headers.get("x-n")
            if filename is not None:
                chunked_payload["n"] = filename
            hmac_value = request.headers.get("x-h")
            if hmac_value is not None:
                chunked_payload["h"] = hmac_value
            return chunked_payload, None

        # 3. Try URL query params (?d=...&e=...&k=...)
        if request.query_params.get("d"):
            query_payload = AdvancedUploadPayload(
                d=request.query_params["d"],
                kb64=request.query_params.get("kb64", "").lower() in ("1", "true"),
                _transport="url",
            )
            encryption = request.query_params.get("e")
            if encryption is not None:
                query_payload["e"] = encryption
            decrypt_key = request.query_params.get("k")
            if decrypt_key is not None:
                query_payload["k"] = decrypt_key
            filename = request.query_params.get("n")
            if filename is not None:
                query_payload["n"] = filename
            hmac_value = request.query_params.get("h")
            if hmac_value is not None:
                query_payload["h"] = hmac_value
            return query_payload, None

        return None, None

    def handle_advanced_upload(self, request: HTTPRequest) -> HTTPResponse:
        """Advanced upload endpoint."""
        payload, error = self._extract_advanced_upload_payload(request)
        if error:
            return error

        if not payload:
            response = HTTPResponse(400)
            response.set_body("", "text/plain")
            return response

        transport = payload.get("_transport", "body")
        filename = payload.get("n") or payload.get("name")
        file_data = payload.get("_raw_body")
        encryption = payload.get("e")
        decrypt_key = payload.get("k")
        hmac_value = payload.get("h") or payload.get("hmac")

        data_field = payload.get("d") or payload.get("data")
        if data_field:
            key_is_base64 = payload.get("kb64", False)

            if decrypt_key and key_is_base64:
                try:
                    decrypt_key = base64.b64decode(decrypt_key, validate=True).decode("utf-8")
                except (ValueError, binascii.Error, UnicodeDecodeError):
                    return self._bad_request("Invalid base64 in 'k'")

            if transport == "url":
                file_data = self._urlsafe_b64decode(data_field)
            else:
                try:
                    file_data = base64.b64decode(data_field, validate=True)
                except (ValueError, binascii.Error):
                    return self._bad_request("Invalid base64 in 'd'")

            if not file_data:
                return self._bad_request("Empty or invalid advanced upload payload")

        if file_data is None:
            response = HTTPResponse(400)
            response.set_body("", "text/plain")
            return response

        if hmac_value and decrypt_key:
            if not verify_hmac(file_data, decrypt_key, hmac_value):
                logger.warning("Advanced upload HMAC verification failed")
                response = HTTPResponse(400)
                response.set_body(json.dumps({"ok": False, "err": "hmac"}), "application/json")
                return response

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
            "Advanced upload: %s, encrypted=%s, hmac=%s, transport=%s",
            safe_filename,
            bool(encryption),
            bool(hmac_value),
            transport,
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
            logger.error(f"Advanced upload write failed: {e}")
            response = HTTPResponse(500)
            response.set_body(json.dumps({"ok": False}), "application/json")
            return response
