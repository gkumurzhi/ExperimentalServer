"""
Secure Notepad handler — E2E encrypted notes stored server-side.

v2: Uses ECDH key exchange (P-256) for automatic key negotiation.
The server never sees plaintext — it stores opaque encrypted blobs
alongside a small JSON sidecar with metadata (title, timestamps).

Routes:
    NOTE /notes/key        → server ECDH public key
    NOTE /notes/exchange   → ECDH key exchange → session
    NOTE /notes  + body    → save note
    NOTE /notes?list       → list notes
    NOTE /notes?clear=1    → clear all notes
    NOTE /notes/{id}       → load note
    NOTE /notes/{id}?delete→ delete note
"""

import base64
import binascii
import json
import logging
import socket
import threading
from collections.abc import Callable

from ..http import HTTPRequest, HTTPResponse
from ..notepad_service import (
    NotepadService,
    NotepadServiceError,
    SaveNoteRequest,
    is_valid_note_id,
)
from ..websocket import build_ws_frame
from .base import BaseHandler

logger = logging.getLogger("httpserver")

_NOTE_CRYPTO_REQUIRED_ERROR = (
    "Secure Notepad requires the cryptography package; install exphttp[crypto]"
)


class NotepadHandlersMixin(BaseHandler):
    """Mixin for the NOTE HTTP method — encrypted note CRUD + ECDH.

    NOTE session IDs are short-lived, audit-only state. They confirm that a
    client recently completed an ECDH exchange, but they are not authorization
    tokens and they are not required to load or decrypt stored note blobs.
    """

    # Set by ExperimentalHTTPServer.__init__
    _notes_lock: threading.Lock
    _notepad_service: NotepadService | None

    # ── public entry point ────────────────────────────────────────

    def handle_note(self, request: HTTPRequest) -> HTTPResponse:
        """
        Route NOTE requests by path and query parameters.

        | Request                        | Action             |
        |--------------------------------|--------------------|
        | NOTE /notes/key                | Server public key  |
        | NOTE /notes/exchange + body    | ECDH key exchange  |
        | NOTE /notes  + body            | Save (create/upd)  |
        | NOTE /notes?list               | List all notes     |
        | NOTE /notes?clear=1            | Clear all notes    |
        | NOTE /notes/{id}               | Load note          |
        | NOTE /notes/{id}?delete        | Delete note        |
        """
        path = request.path
        query = request.query_string

        # Strip leading slash, normalise
        clean = path.lstrip("/")

        # ECDH routes — must be checked BEFORE the notes/{id} catch-all
        if clean == "notes/key":
            return self._note_get_key()
        if clean == "notes/exchange":
            return self._note_exchange(request)
        if self._ecdh_manager is None:
            return self._note_crypto_required()

        # Route: /notes  (root)
        if clean == "notes" or clean == "notes/":
            if self._is_note_clear_request(request):
                return self._note_clear()
            if "list" in query:
                return self._note_list()
            if request.body:
                return self._note_save(request)
            return self._note_list()

        # Route: /notes/{id}
        if clean.startswith("notes/"):
            note_id = clean[len("notes/") :]
            if not is_valid_note_id(note_id):
                return self._bad_request("Invalid note ID")
            if "delete" in query:
                return self._note_delete(note_id)
            return self._note_load(note_id)

        return self._bad_request("Invalid notepad path")

    def _note_crypto_required(self) -> HTTPResponse:
        """Return the NOTE feature-unavailable response."""
        return self._error_response(501, _NOTE_CRYPTO_REQUIRED_ERROR)

    # ── ECDH key exchange ─────────────────────────────────────────

    def _note_get_key(self) -> HTTPResponse:
        """Return the server's ECDH public key (base64 of raw 65 bytes)."""
        mgr = self._ecdh_manager
        result: dict[str, object] = {"hasEcdh": mgr is not None}
        if mgr is not None:
            raw = mgr.get_public_key_raw()
            result["publicKey"] = base64.b64encode(raw).decode("ascii")

        response = HTTPResponse(200)
        response.set_body(json.dumps(result), "application/json")
        return response

    def _note_exchange(self, request: HTTPRequest) -> HTTPResponse:
        """Perform ECDH key exchange: receive client pubkey, return session."""
        mgr = self._ecdh_manager
        if mgr is None:
            return self._note_crypto_required()

        payload, error = self._load_json_object(request.body)
        if error:
            return error
        assert payload is not None

        client_key_b64 = payload.get("clientPublicKey")
        if not isinstance(client_key_b64, str) or not client_key_b64:
            return self._bad_request("Missing 'clientPublicKey'")

        try:
            client_pub_raw = base64.b64decode(client_key_b64, validate=True)
        except (ValueError, binascii.Error):
            return self._bad_request("Invalid base64 in 'clientPublicKey'")

        if len(client_pub_raw) != 65:
            return self._bad_request(
                "Invalid public key length (expected 65 bytes uncompressed)",
            )

        try:
            session_id, _key = mgr.derive_session(client_pub_raw)
        except Exception as e:
            logger.error("ECDH exchange failed: %s", e)
            return self._bad_request("ECDH exchange failed")

        server_pub_b64 = base64.b64encode(
            mgr.get_public_key_raw(),
        ).decode("ascii")

        response = HTTPResponse(200)
        response.set_body(
            json.dumps(
                {
                    "sessionId": session_id,
                    "serverPublicKey": server_pub_b64,
                    "sessionTtlSeconds": int(mgr.session_ttl_seconds),
                }
            ),
            "application/json",
        )
        return response

    # ── internal helpers ──────────────────────────────────────────

    def _get_notepad_service(self) -> NotepadService:
        """Return the lazily created note-domain service."""
        service = getattr(self, "_notepad_service", None)
        if service is None:
            session_exists = (
                self._note_session_is_active if self._ecdh_manager is not None else None
            )
            service = NotepadService(
                self.notes_dir,
                self._notes_lock,
                session_exists=session_exists,
            )
            self._notepad_service = service
        return service

    @staticmethod
    def _is_note_clear_request(request: HTTPRequest) -> bool:
        """Return True when NOTE explicitly asks to clear notes/."""
        return request.query_params.get("clear", "").lower() in {"1", "true", "yes"}

    def _note_session_is_active(self, session_id: str) -> bool:
        """Return ``True`` when *session_id* is still active in the ECDH manager."""
        mgr = self._ecdh_manager
        return mgr is not None and mgr.get_session_key(session_id) is not None

    @staticmethod
    def _note_json_response(payload: dict[str, object], status_code: int = 200) -> HTTPResponse:
        """Build a JSON HTTP response for note operations."""
        response = HTTPResponse(status_code)
        response.set_body(json.dumps(payload), "application/json")
        return response

    def _note_error_response(self, error: NotepadServiceError) -> HTTPResponse:
        """Map a note-domain error to the existing HTTP error contract."""
        return self._error_response(error.status_code, error.message)

    def _note_save(self, request: HTTPRequest) -> HTTPResponse:
        """Save (create or update) a note."""
        payload, error = self._load_json_object(request.body)
        if error:
            return error
        assert payload is not None

        title_value = payload.get("title")
        data_b64 = payload.get("data")
        note_id_value = payload.get("id", "")
        if not isinstance(note_id_value, str):
            return self._bad_request("Invalid note ID format")
        save_request = SaveNoteRequest(
            title=title_value if isinstance(title_value, str) else "",
            data_b64=data_b64 if isinstance(data_b64, str) else "",
            note_id=note_id_value,
            session_id=request.get_header("x-session-id") or None,
        )
        try:
            result = self._get_notepad_service().save_note(save_request)
        except NotepadServiceError as exc:
            return self._note_error_response(exc)
        return self._note_json_response(result.to_dict(), 201 if result.created else 200)

    def _note_list(self) -> HTTPResponse:
        """List all notes sorted by updated_at descending.

        The encrypted blob is the source of truth; malformed sidecars fall back
        to filename- and filesystem-derived metadata instead of hiding the note.
        """
        result = self._get_notepad_service().list_notes()
        return self._note_json_response(result.to_dict())

    def _note_load(self, note_id: str) -> HTTPResponse:
        """Load a single note (encrypted blob + metadata)."""
        try:
            result = self._get_notepad_service().load_note(note_id)
        except NotepadServiceError as exc:
            return self._note_error_response(exc)
        return self._note_json_response(result.to_dict())

    def _note_delete(self, note_id: str) -> HTTPResponse:
        """Delete a note (both .enc and .meta.json)."""
        try:
            result = self._get_notepad_service().delete_note(note_id)
        except NotepadServiceError as exc:
            return self._note_error_response(exc)
        return self._note_json_response(result.to_dict())

    def _note_clear(self) -> HTTPResponse:
        """Clear all notes from the separate notes/ directory."""
        try:
            result = self._get_notepad_service().clear_notes()
        except NotepadServiceError as exc:
            return self._note_error_response(exc)
        return self._note_json_response(result.to_dict())

    def _handle_ws_message(self, sock: socket.socket, payload: bytes) -> None:
        """Process a single WebSocket JSON message for notepad ops."""
        try:
            msg = json.loads(payload.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._ws_send_json(sock, {"type": "error", "error": "Invalid JSON"})
            return

        msg_obj = self._coerce_json_object(msg)
        if msg_obj is None:
            self._ws_send_json(sock, {"type": "error", "error": "Expected JSON object"})
            return

        msg_type = msg_obj.get("type")
        if not isinstance(msg_type, str):
            msg_type = ""

        if msg_type == "save":
            self._ws_handle_save(sock, msg_obj)
        elif msg_type == "load":
            self._ws_handle_load(sock, msg_obj)
        elif msg_type == "list":
            result = self._get_notepad_service().list_notes().to_dict()
            result["type"] = "list"
            self._ws_send_json(sock, result)
        elif msg_type == "delete":
            note_id = msg_obj.get("id")
            if isinstance(note_id, str) and note_id and is_valid_note_id(note_id):
                result = self._ws_run_note_operation(
                    "deleted",
                    lambda: self._get_notepad_service().delete_note(note_id),
                )
                result["type"] = "deleted"
                self._ws_send_json(sock, result)
            else:
                self._ws_send_json(sock, {"type": "error", "error": "Invalid note ID"})
        elif msg_type == "clear":
            result = self._ws_run_note_operation(
                "cleared",
                lambda: self._get_notepad_service().clear_notes(),
            )
            self._ws_send_json(sock, result)
        else:
            self._ws_send_json(sock, {"type": "error", "error": f"Unknown type: {msg_type}"})

    def _ws_run_note_operation(
        self,
        result_type: str,
        operation: Callable[[], object],
    ) -> dict[str, object]:
        """Run a note-domain operation and map errors into the existing WS payload shape."""
        try:
            result = operation()
        except NotepadServiceError as exc:
            payload = exc.to_dict()
        else:
            to_dict = getattr(result, "to_dict", None)
            payload = to_dict() if callable(to_dict) else {}

        payload_obj = self._coerce_json_object(payload)
        if payload_obj is None:
            payload_obj = {"error": "Invalid JSON response", "status": 500}
        payload_obj["type"] = result_type
        return payload_obj

    def _ws_handle_save(self, sock: socket.socket, msg: dict[str, object]) -> None:
        """Handle a WS save message through the shared note-domain service."""
        title = msg.get("title")
        data = msg.get("data")
        note_id = msg.get("noteId")
        session_id = msg.get("sessionId")
        save_request = SaveNoteRequest(
            title=title if isinstance(title, str) else "",
            data_b64=data if isinstance(data, str) else "",
            note_id=note_id if isinstance(note_id, str) else "",
            session_id=session_id if isinstance(session_id, str) and session_id else None,
        )
        result = self._ws_run_note_operation(
            "saved",
            lambda: self._get_notepad_service().save_note(save_request),
        )
        self._ws_send_json(sock, result)

    def _ws_handle_load(self, sock: socket.socket, msg: dict[str, object]) -> None:
        """Handle a WS load message."""
        note_id = msg.get("id")
        if not isinstance(note_id, str) or not note_id or not is_valid_note_id(note_id):
            self._ws_send_json(sock, {"type": "error", "error": "Invalid note ID"})
            return
        result = self._ws_run_note_operation(
            "loaded",
            lambda: self._get_notepad_service().load_note(note_id),
        )
        self._ws_send_json(sock, result)

    @staticmethod
    def _ws_send_json(sock: socket.socket, data: dict[str, object]) -> None:
        """Send a JSON message over WebSocket."""
        frame = build_ws_frame(json.dumps(data).encode("utf-8"))
        try:
            sock.sendall(frame)
        except Exception:
            pass
