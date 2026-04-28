"""Transport-independent note storage service for Secure Notepad."""

from __future__ import annotations

import base64
import binascii
import json
import logging
import secrets
import shutil
import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("httpserver")


NOTE_ID_LENGTH = 32


def is_valid_note_id(note_id: str) -> bool:
    """Return ``True`` when *note_id* matches the stored-note identifier format."""
    return 1 <= len(note_id) <= NOTE_ID_LENGTH and all(
        char in "0123456789abcdef" for char in note_id
    )


@dataclass(frozen=True, slots=True)
class SaveNoteRequest:
    """Normalized save-note input shared by HTTP and WebSocket transports."""

    title: str
    data_b64: str
    note_id: str = ""
    session_id: str | None = None


@dataclass(frozen=True, slots=True)
class NoteSummary:
    """Recoverable note metadata returned to transports."""

    note_id: str
    title: str
    created_at: str
    updated_at: str
    size: int

    def to_dict(self) -> dict[str, object]:
        """Serialize the note summary for JSON responses."""
        return {
            "id": self.note_id,
            "title": self.title,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "size": self.size,
        }


@dataclass(frozen=True, slots=True)
class SaveNoteResult:
    """Successful save-note result."""

    note: NoteSummary
    created: bool

    def to_dict(self) -> dict[str, object]:
        """Serialize the save result for JSON responses."""
        return {"success": True, **self.note.to_dict()}


@dataclass(frozen=True, slots=True)
class ListNotesResult:
    """Successful list-notes result."""

    notes: list[NoteSummary]

    def to_dict(self) -> dict[str, object]:
        """Serialize the list result for JSON responses."""
        return {
            "notes": [note.to_dict() for note in self.notes],
            "count": len(self.notes),
        }


@dataclass(frozen=True, slots=True)
class LoadNoteResult:
    """Successful load-note result."""

    note: NoteSummary
    data_b64: str

    def to_dict(self) -> dict[str, object]:
        """Serialize the load result for JSON responses."""
        return {**self.note.to_dict(), "data": self.data_b64}


@dataclass(frozen=True, slots=True)
class DeleteNoteResult:
    """Successful delete-note result."""

    note_id: str

    def to_dict(self) -> dict[str, object]:
        """Serialize the delete result for JSON responses."""
        return {"success": True, "id": self.note_id}


@dataclass(frozen=True, slots=True)
class ClearNotesResult:
    """Successful clear-notes result."""

    deleted_files: int
    deleted_dirs: int
    preserved: list[str]

    def to_dict(self) -> dict[str, object]:
        """Serialize the clear result for JSON responses."""
        return {
            "success": True,
            "cleared": True,
            "path": "/notes",
            "deleted_files": self.deleted_files,
            "deleted_dirs": self.deleted_dirs,
            "preserved": self.preserved,
        }


class NotepadServiceError(Exception):
    """Typed note-domain error that transports can map into responses."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message

    def to_dict(self) -> dict[str, object]:
        """Serialize the error for JSON responses."""
        return {"error": self.message, "status": self.status_code}


class NotepadService:
    """Shared storage and metadata logic for Secure Notepad."""

    def __init__(
        self,
        notes_dir: Path,
        notes_lock: threading.Lock,
        *,
        session_exists: Callable[[str], bool] | None = None,
    ) -> None:
        self._notes_dir = notes_dir
        self._notes_lock = notes_lock
        self._session_exists = session_exists

    def save_note(self, request: SaveNoteRequest) -> SaveNoteResult:
        """Create or update a note from normalized transport input."""
        title = request.title.strip()
        if not title:
            raise NotepadServiceError(400, "Missing or empty 'title'")
        if not request.data_b64:
            raise NotepadServiceError(400, "Missing 'data' (base64-encoded encrypted blob)")

        try:
            raw_data = base64.b64decode(request.data_b64, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise NotepadServiceError(400, "Invalid base64 in 'data'") from exc

        if len(raw_data) == 0:
            raise NotepadServiceError(400, "Empty encrypted data")

        note_id = request.note_id
        is_new = False
        if note_id:
            _notes_dir, enc_path, meta_path = self._resolve_note_paths(note_id)
            if not enc_path.exists():
                raise NotepadServiceError(404, "Note not found for update")
        else:
            note_id = secrets.token_hex(16)
            is_new = True
            _notes_dir, enc_path, meta_path = self._resolve_note_paths(note_id)

        now = datetime.now(timezone.utc).isoformat()
        meta: dict[str, object] = {
            "id": note_id,
            "title": title[:200],
            "created_at": now,
            "updated_at": now,
            "size": len(raw_data),
        }

        if not is_new and meta_path.exists():
            existing = self._note_record(note_id, enc_path)
            if existing.created_at:
                meta["created_at"] = existing.created_at

        if request.session_id and self._session_exists is not None:
            if self._session_exists(request.session_id):
                meta["session"] = True
            else:
                logger.debug("Ignoring unknown or expired note session: %s", request.session_id)

        with self._notes_lock:
            try:
                enc_path.write_bytes(raw_data)
                meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
            except Exception as exc:
                logger.error("Note save failed: %s", exc)
                raise NotepadServiceError(500, "Failed to save note") from exc

        logger.debug("Note saved: %s (%d bytes)", note_id, len(raw_data))
        saved_note = NoteSummary(
            note_id=note_id,
            title=str(meta["title"]),
            created_at=str(meta["created_at"]),
            updated_at=str(meta["updated_at"]),
            size=len(raw_data),
        )
        return SaveNoteResult(note=saved_note, created=is_new)

    def list_notes(self) -> ListNotesResult:
        """Return all notes sorted by ``updated_at`` descending."""
        notes_dir = self._get_notes_dir()
        notes: list[NoteSummary] = []

        for enc_path in notes_dir.glob("*.enc"):
            note_id = enc_path.stem
            if is_valid_note_id(note_id):
                notes.append(self._note_record(note_id, enc_path))

        notes.sort(key=lambda note: note.updated_at, reverse=True)
        return ListNotesResult(notes=notes)

    def load_note(self, note_id: str) -> LoadNoteResult:
        """Load a note's ciphertext and metadata."""
        _notes_dir, enc_path, _meta_path = self._resolve_note_paths(note_id)
        if not enc_path.exists():
            raise NotepadServiceError(404, "Note not found")

        try:
            raw_data = enc_path.read_bytes()
        except OSError as exc:
            logger.error("Note load failed: %s", exc)
            raise NotepadServiceError(500, "Failed to read note") from exc

        note = self._note_record(note_id, enc_path)
        return LoadNoteResult(
            note=note,
            data_b64=base64.b64encode(raw_data).decode("ascii"),
        )

    def delete_note(self, note_id: str) -> DeleteNoteResult:
        """Delete a note's ciphertext and metadata sidecar."""
        _notes_dir, enc_path, meta_path = self._resolve_note_paths(note_id)
        if not enc_path.exists():
            raise NotepadServiceError(404, "Note not found")

        with self._notes_lock:
            try:
                enc_path.unlink(missing_ok=True)
                meta_path.unlink(missing_ok=True)
            except OSError as exc:
                logger.error("Note delete failed: %s", exc)
                raise NotepadServiceError(500, "Failed to delete note") from exc

        logger.debug("Note deleted: %s", note_id)
        return DeleteNoteResult(note_id=note_id)

    def clear_notes(self) -> ClearNotesResult:
        """Delete all user-visible entries from the notes directory."""
        notes_dir = self._get_notes_dir()
        deleted_files = 0
        deleted_dirs = 0
        preserved: list[str] = []
        errors: list[str] = []

        with self._notes_lock:
            for entry in sorted(notes_dir.iterdir(), key=lambda path: path.name):
                if entry.name.startswith("."):
                    preserved.append(entry.name)
                    continue

                try:
                    if entry.is_dir() and not entry.is_symlink():
                        shutil.rmtree(entry)
                        deleted_dirs += 1
                    else:
                        entry.unlink()
                        deleted_files += 1
                except OSError as exc:
                    errors.append(f"{entry.name}: {exc}")

        if errors:
            logger.error("Note clear failed: %s", "; ".join(errors))
            raise NotepadServiceError(500, "Failed to clear notes")

        logger.debug(
            "Cleared notes/: %s files, %s directories, %s preserved",
            deleted_files,
            deleted_dirs,
            len(preserved),
        )
        return ClearNotesResult(
            deleted_files=deleted_files,
            deleted_dirs=deleted_dirs,
            preserved=preserved,
        )

    def _get_notes_dir(self) -> Path:
        """Return the notes directory, creating it lazily."""
        notes_dir = self._notes_dir
        notes_dir.mkdir(parents=True, exist_ok=True)
        return notes_dir

    @staticmethod
    def _note_meta_path(notes_dir: Path, note_id: str) -> Path:
        """Return the metadata sidecar path for *note_id*."""
        return (notes_dir / f"{note_id}.meta.json").resolve()

    @staticmethod
    def _note_timestamp_from_path(path: Path) -> str:
        """Return the file mtime as an ISO-8601 UTC timestamp."""
        try:
            return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
        except OSError:
            return ""

    def _read_note_meta(self, meta_path: Path) -> dict[str, object] | None:
        """Read a metadata sidecar, returning ``None`` for malformed data."""
        try:
            payload = json.loads(meta_path.read_text("utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

        if not isinstance(payload, dict):
            return None
        if not all(isinstance(key, str) for key in payload):
            return None
        return payload

    def _note_record(self, note_id: str, enc_path: Path) -> NoteSummary:
        """Build a recoverable note summary from ciphertext plus sidecar."""
        fallback_timestamp = self._note_timestamp_from_path(enc_path)
        try:
            size = enc_path.stat().st_size
        except OSError:
            size = 0

        title = ""
        created_at = fallback_timestamp
        updated_at = fallback_timestamp
        meta_path = self._note_meta_path(enc_path.parent, note_id)

        if meta_path.exists():
            existing = self._read_note_meta(meta_path)
            if existing is not None:
                maybe_title = existing.get("title")
                maybe_created_at = existing.get("created_at")
                maybe_updated_at = existing.get("updated_at")
                if isinstance(maybe_title, str):
                    title = maybe_title
                if isinstance(maybe_created_at, str) and maybe_created_at:
                    created_at = maybe_created_at
                if isinstance(maybe_updated_at, str) and maybe_updated_at:
                    updated_at = maybe_updated_at

        return NoteSummary(
            note_id=note_id,
            title=title,
            created_at=created_at,
            updated_at=updated_at,
            size=size,
        )

    def _resolve_note_paths(self, note_id: str) -> tuple[Path, Path, Path]:
        """Resolve and validate the ciphertext + metadata paths for *note_id*."""
        if not is_valid_note_id(note_id):
            raise NotepadServiceError(400, "Invalid note ID")

        notes_dir = self._get_notes_dir().resolve()
        enc_path = (notes_dir / f"{note_id}.enc").resolve()
        meta_path = self._note_meta_path(notes_dir, note_id)

        try:
            enc_path.relative_to(notes_dir)
            meta_path.relative_to(notes_dir)
        except ValueError as exc:
            raise NotepadServiceError(400, "Invalid note ID") from exc

        return notes_dir, enc_path, meta_path


__all__ = [
    "ClearNotesResult",
    "DeleteNoteResult",
    "ListNotesResult",
    "LoadNoteResult",
    "NotepadService",
    "NotepadServiceError",
    "NoteSummary",
    "SaveNoteRequest",
    "SaveNoteResult",
    "is_valid_note_id",
]
