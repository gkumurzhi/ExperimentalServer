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
    NOTE /notes/{id}       → load note
    NOTE /notes/{id}?delete→ delete note
"""

import base64
import json
import logging
import re
import secrets
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from ..http import HTTPRequest, HTTPResponse
from .base import BaseHandler

if TYPE_CHECKING:
    pass

logger = logging.getLogger("httpserver")

_NOTE_ID_RE = re.compile(r"^[a-f0-9]{1,32}$")


class NotepadHandlersMixin(BaseHandler):
    """Mixin for the NOTE HTTP method — encrypted note CRUD + ECDH."""

    # Set by ExperimentalHTTPServer.__init__
    _notes_lock: threading.Lock

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

        # Route: /notes  (root)
        if clean == "notes" or clean == "notes/":
            if "list" in query:
                return self._note_list()
            if request.body:
                return self._note_save(request)
            return self._note_list()

        # Route: /notes/{id}
        if clean.startswith("notes/"):
            note_id = clean[len("notes/"):]
            if not _NOTE_ID_RE.match(note_id):
                return self._bad_request("Invalid note ID")
            if "delete" in query:
                return self._note_delete(note_id)
            return self._note_load(note_id)

        return self._bad_request("Invalid notepad path")

    # ── ECDH key exchange ─────────────────────────────────────────

    def _note_get_key(self) -> HTTPResponse:
        """Return the server's ECDH public key (base64 of raw 65 bytes)."""
        mgr = getattr(self, "_ecdh_manager", None)
        has_ecdh = mgr is not None

        result: dict = {"hasEcdh": has_ecdh}
        if has_ecdh:
            raw = mgr.get_public_key_raw()
            result["publicKey"] = base64.b64encode(raw).decode("ascii")

        response = HTTPResponse(200)
        response.set_body(json.dumps(result), "application/json")
        return response

    def _note_exchange(self, request: HTTPRequest) -> HTTPResponse:
        """Perform ECDH key exchange: receive client pubkey, return session."""
        mgr = getattr(self, "_ecdh_manager", None)
        if mgr is None:
            return self._error_response(
                501, "ECDH not available (cryptography package not installed)",
            )

        try:
            payload = json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return self._bad_request("Invalid JSON body")

        client_key_b64 = payload.get("clientPublicKey", "")
        if not client_key_b64:
            return self._bad_request("Missing 'clientPublicKey'")

        try:
            client_pub_raw = base64.b64decode(client_key_b64)
        except Exception:
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
            json.dumps({
                "sessionId": session_id,
                "serverPublicKey": server_pub_b64,
            }),
            "application/json",
        )
        return response

    # ── internal helpers ──────────────────────────────────────────

    def _get_notes_dir(self) -> Path:
        """Return (and lazily create) the ``uploads/notes/`` directory."""
        notes_dir = self.upload_dir / "notes"
        notes_dir.mkdir(parents=True, exist_ok=True)
        return notes_dir

    def _note_save(self, request: HTTPRequest) -> HTTPResponse:
        """Save (create or update) a note."""
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return self._bad_request("Invalid JSON body")

        if not isinstance(payload, dict):
            return self._bad_request("Expected JSON object")

        title = payload.get("title", "").strip()
        data_b64 = payload.get("data")

        if not title:
            return self._bad_request("Missing or empty 'title'")
        if not data_b64:
            return self._bad_request("Missing 'data' (base64-encoded encrypted blob)")

        # Validate that data is valid base64
        try:
            raw_data = base64.b64decode(data_b64)
        except Exception:
            return self._bad_request("Invalid base64 in 'data'")

        if len(raw_data) == 0:
            return self._bad_request("Empty encrypted data")

        note_id = payload.get("id", "")
        notes_dir = self._get_notes_dir()
        is_new = False

        if note_id:
            if not _NOTE_ID_RE.match(note_id):
                return self._bad_request("Invalid note ID format")
            # Verify the note actually exists for updates
            enc_path = notes_dir / f"{note_id}.enc"
            if not enc_path.exists():
                return self._error_response(404, "Note not found for update")
        else:
            note_id = secrets.token_hex(16)
            is_new = True

        # Path-traversal check (belt + suspenders)
        enc_path = (notes_dir / f"{note_id}.enc").resolve()
        meta_path = (notes_dir / f"{note_id}.meta.json").resolve()
        try:
            enc_path.relative_to(notes_dir.resolve())
            meta_path.relative_to(notes_dir.resolve())
        except ValueError:
            return self._bad_request("Invalid note ID")

        now = datetime.now(timezone.utc).isoformat()
        meta = {
            "id": note_id,
            "title": title[:200],
            "created_at": now,
            "updated_at": now,
            "size": len(raw_data),
        }

        # Load existing meta for created_at preservation on update
        if not is_new and meta_path.exists():
            try:
                existing = json.loads(meta_path.read_text("utf-8"))
                meta["created_at"] = existing.get("created_at", now)
            except (json.JSONDecodeError, OSError):
                pass

        # Store session ID in meta if present (for audit trail)
        session_id = request.get_header("x-session-id")
        if session_id:
            meta["session"] = True

        with self._notes_lock:
            try:
                enc_path.write_bytes(raw_data)
                meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
            except Exception as e:
                logger.error("Note save failed: %s", e)
                return self._internal_error("Failed to save note")

        logger.debug("Note saved: %s (%d bytes)", note_id, len(raw_data))

        response = HTTPResponse(201 if is_new else 200)
        response.set_body(
            json.dumps({
                "success": True,
                "id": note_id,
                "title": meta["title"],
                "created_at": meta["created_at"],
                "updated_at": meta["updated_at"],
                "size": len(raw_data),
            }),
            "application/json",
        )
        return response

    def _note_list(self) -> HTTPResponse:
        """List all notes sorted by updated_at descending."""
        notes_dir = self._get_notes_dir()
        notes: list[dict] = []

        for meta_file in notes_dir.glob("*.meta.json"):
            try:
                meta = json.loads(meta_file.read_text("utf-8"))
                notes.append({
                    "id": meta["id"],
                    "title": meta.get("title", ""),
                    "created_at": meta.get("created_at", ""),
                    "updated_at": meta.get("updated_at", ""),
                    "size": meta.get("size", 0),
                })
            except (json.JSONDecodeError, OSError, KeyError):
                continue

        notes.sort(key=lambda n: n.get("updated_at", ""), reverse=True)

        response = HTTPResponse(200)
        response.set_body(
            json.dumps({"notes": notes, "count": len(notes)}),
            "application/json",
        )
        return response

    def _note_load(self, note_id: str) -> HTTPResponse:
        """Load a single note (encrypted blob + metadata)."""
        notes_dir = self._get_notes_dir()
        enc_path = (notes_dir / f"{note_id}.enc").resolve()
        meta_path = (notes_dir / f"{note_id}.meta.json").resolve()

        # Path-traversal guard
        try:
            enc_path.relative_to(notes_dir.resolve())
        except ValueError:
            return self._bad_request("Invalid note ID")

        if not enc_path.exists():
            return self._error_response(404, "Note not found")

        try:
            raw_data = enc_path.read_bytes()
            data_b64 = base64.b64encode(raw_data).decode("ascii")
        except OSError as e:
            logger.error("Note load failed: %s", e)
            return self._internal_error("Failed to read note")

        meta: dict = {"id": note_id}
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text("utf-8"))
            except (json.JSONDecodeError, OSError):
                pass

        response = HTTPResponse(200)
        response.set_body(
            json.dumps({
                "id": note_id,
                "title": meta.get("title", ""),
                "data": data_b64,
                "created_at": meta.get("created_at", ""),
                "updated_at": meta.get("updated_at", ""),
                "size": len(raw_data),
            }),
            "application/json",
        )
        return response

    def _note_delete(self, note_id: str) -> HTTPResponse:
        """Delete a note (both .enc and .meta.json)."""
        notes_dir = self._get_notes_dir()
        enc_path = (notes_dir / f"{note_id}.enc").resolve()
        meta_path = (notes_dir / f"{note_id}.meta.json").resolve()

        # Path-traversal guard
        try:
            enc_path.relative_to(notes_dir.resolve())
        except ValueError:
            return self._bad_request("Invalid note ID")

        if not enc_path.exists():
            return self._error_response(404, "Note not found")

        with self._notes_lock:
            try:
                enc_path.unlink(missing_ok=True)
                meta_path.unlink(missing_ok=True)
            except OSError as e:
                logger.error("Note delete failed: %s", e)
                return self._internal_error("Failed to delete note")

        logger.debug("Note deleted: %s", note_id)

        response = HTTPResponse(200)
        response.set_body(
            json.dumps({"success": True, "id": note_id}),
            "application/json",
        )
        return response
