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
MAX_NOTE_ENCRYPTED_BLOB_BYTES = 1024 * 1024
DEFAULT_MAX_NOTES = 1000
DEFAULT_MAX_NOTE_STORAGE_BYTES = 256 * 1024 * 1024


def max_note_data_b64_chars() -> int:
    """Return the longest valid base64 payload for one encrypted note blob."""
    return ((MAX_NOTE_ENCRYPTED_BLOB_BYTES + 2) // 3) * 4


def _note_blob_limit_label() -> str:
    """Return a human-readable label for the current note blob limit."""
    mebibyte = 1024 * 1024
    if MAX_NOTE_ENCRYPTED_BLOB_BYTES % mebibyte == 0:
        return f"{MAX_NOTE_ENCRYPTED_BLOB_BYTES // mebibyte} MiB"
    return f"{MAX_NOTE_ENCRYPTED_BLOB_BYTES} bytes"


def _format_note_bytes(size: int) -> str:
    """Return a compact human-readable byte count for note quota messages."""
    fsize = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if fsize < 1024:
            return f"{fsize:.1f} {unit}"
        fsize /= 1024
    return f"{fsize:.1f} TB"


def is_valid_note_id(note_id: str) -> bool:
    """Return ``True`` when *note_id* matches the stored-note identifier format."""
    return 1 <= len(note_id) <= NOTE_ID_LENGTH and all(
        char in "0123456789abcdef" for char in note_id
    )


@dataclass(frozen=True, slots=True)
class NoteStoragePolicy:
    """Aggregate encrypted-note storage and listing limits."""

    max_total_bytes: int | None = DEFAULT_MAX_NOTE_STORAGE_BYTES
    max_note_count: int | None = DEFAULT_MAX_NOTES
    max_listed_notes: int = DEFAULT_MAX_NOTES

    def __post_init__(self) -> None:
        if self.max_total_bytes is not None and self.max_total_bytes < 0:
            raise ValueError("note_storage_limit must be at least 0")
        if self.max_note_count is not None and self.max_note_count < 0:
            raise ValueError("note_count_limit must be at least 0")
        if self.max_listed_notes <= 0:
            raise ValueError("note_list_limit must be greater than 0")

    def describe_limit(self) -> str:
        """Return a short human-readable description for startup output."""
        parts: list[str] = []
        if self.max_total_bytes is not None:
            parts.append(f"max {_format_note_bytes(self.max_total_bytes)}")
        if self.max_note_count is not None:
            parts.append(f"max {self.max_note_count} notes")
        parts.append(f"list {self.max_listed_notes}")
        return ", ".join(parts)


@dataclass(frozen=True, slots=True)
class NoteStorageUsage:
    """Current encrypted-note storage usage."""

    total_bytes: int
    note_count: int


@dataclass(frozen=True, slots=True)
class SaveNoteRequest:
    """Normalized save-note input shared by HTTP and WebSocket transports."""

    title: str
    data_b64: str
    note_id: str = ""
    session_id: str | None = None
    create_if_missing: bool = False


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
    limit: int
    truncated: bool

    def to_dict(self) -> dict[str, object]:
        """Serialize the list result for JSON responses."""
        return {
            "notes": [note.to_dict() for note in self.notes],
            "count": len(self.notes),
            "limit": self.limit,
            "truncated": self.truncated,
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
        storage_policy: NoteStoragePolicy | None = None,
    ) -> None:
        self._notes_dir = notes_dir
        self._notes_lock = notes_lock
        self._session_exists = session_exists
        self._storage_policy = storage_policy or NoteStoragePolicy()

    @staticmethod
    def _write_note_temp_bytes(
        notes_dir: Path,
        note_id: str,
        label: str,
        data: bytes,
        *,
        max_attempts: int = 64,
    ) -> Path:
        """Write bytes to an exclusive same-directory temporary note file."""
        attempts = max(1, max_attempts)
        for _attempt in range(attempts):
            temp_path = notes_dir / f".{note_id}.{label}.{secrets.token_hex(8)}.tmp"
            created = False
            try:
                with temp_path.open("xb") as temp_file:
                    created = True
                    temp_file.write(data)
                return temp_path
            except FileExistsError:
                continue
            except Exception:
                if created:
                    temp_path.unlink(missing_ok=True)
                raise

        raise FileExistsError(f"Could not reserve a temporary note file for {note_id!r}")

    @classmethod
    def _copy_note_backup(
        cls,
        source_path: Path,
        notes_dir: Path,
        note_id: str,
        label: str,
    ) -> Path:
        """Copy an existing note file to a same-directory backup temp file."""
        return cls._write_note_temp_bytes(
            notes_dir,
            note_id,
            f"{label}.backup",
            source_path.read_bytes(),
        )

    @staticmethod
    def _cleanup_note_temp_files(*paths: Path | None) -> None:
        """Remove temporary note files, logging but not masking original failures."""
        for path in paths:
            if path is None:
                continue
            try:
                path.unlink(missing_ok=True)
            except OSError as exc:
                logger.warning("Failed to clean temporary note file %s: %s", path.name, exc)

    @staticmethod
    def _restore_note_pair(
        enc_path: Path,
        meta_path: Path,
        enc_backup: Path | None,
        meta_backup: Path | None,
    ) -> bool:
        """Restore or remove final note files after a failed pair replacement."""
        restore_errors: list[str] = []

        try:
            if enc_backup is not None and enc_backup.exists():
                enc_backup.replace(enc_path)
            elif enc_path.exists():
                enc_path.unlink()
        except OSError as exc:
            restore_errors.append(f"{enc_path.name}: {exc}")

        try:
            if meta_backup is not None and meta_backup.exists():
                meta_backup.replace(meta_path)
            elif meta_path.exists():
                meta_path.unlink()
        except OSError as exc:
            restore_errors.append(f"{meta_path.name}: {exc}")

        if restore_errors:
            logger.error("Note save rollback incomplete: %s", "; ".join(restore_errors))
            return False

        return True

    def _write_note_pair_atomic(
        self,
        note_id: str,
        enc_path: Path,
        meta_path: Path,
        raw_data: bytes,
        meta: dict[str, object],
    ) -> None:
        """Replace ciphertext and metadata through same-directory temp files."""
        notes_dir = enc_path.parent
        meta_data = json.dumps(meta, indent=2).encode("utf-8")
        enc_tmp: Path | None = None
        meta_tmp: Path | None = None
        enc_backup: Path | None = None
        meta_backup: Path | None = None
        replacements_started = False
        rollback_complete = True

        try:
            enc_tmp = self._write_note_temp_bytes(notes_dir, note_id, "enc", raw_data)
            meta_tmp = self._write_note_temp_bytes(notes_dir, note_id, "meta", meta_data)

            if enc_path.exists():
                enc_backup = self._copy_note_backup(enc_path, notes_dir, note_id, "enc")
            if meta_path.exists():
                meta_backup = self._copy_note_backup(meta_path, notes_dir, note_id, "meta")

            replacements_started = True
            enc_tmp.replace(enc_path)
            enc_tmp = None
            meta_tmp.replace(meta_path)
            meta_tmp = None
        except Exception:
            if replacements_started:
                rollback_complete = self._restore_note_pair(
                    enc_path,
                    meta_path,
                    enc_backup,
                    meta_backup,
                )
            raise
        finally:
            self._cleanup_note_temp_files(enc_tmp, meta_tmp)
            if rollback_complete:
                self._cleanup_note_temp_files(enc_backup, meta_backup)

    def save_note(self, request: SaveNoteRequest) -> SaveNoteResult:
        """Create or update a note from normalized transport input."""
        title = request.title.strip()
        if not title:
            raise NotepadServiceError(400, "Missing or empty 'title'")
        if not request.data_b64:
            raise NotepadServiceError(400, "Missing 'data' (base64-encoded encrypted blob)")

        encoded_limit = max_note_data_b64_chars()
        if len(request.data_b64) > encoded_limit:
            raise NotepadServiceError(
                413,
                (
                    f"Encrypted note data exceeds {_note_blob_limit_label()} decoded limit "
                    f"({encoded_limit} base64 characters max)"
                ),
            )

        try:
            raw_data = base64.b64decode(request.data_b64, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise NotepadServiceError(400, "Invalid base64 in 'data'") from exc

        if len(raw_data) == 0:
            raise NotepadServiceError(400, "Empty encrypted data")
        if len(raw_data) > MAX_NOTE_ENCRYPTED_BLOB_BYTES:
            raise NotepadServiceError(
                413,
                (
                    f"Encrypted note data exceeds {_note_blob_limit_label()} decoded limit "
                    f"({MAX_NOTE_ENCRYPTED_BLOB_BYTES} bytes max)"
                ),
            )

        note_id = request.note_id or secrets.token_hex(16)
        _notes_dir, enc_path, meta_path = self._resolve_note_paths(note_id)

        now = datetime.now(timezone.utc).isoformat()
        meta: dict[str, object] = {
            "id": note_id,
            "title": title[:200],
            "created_at": now,
            "updated_at": now,
            "size": len(raw_data),
        }

        if request.session_id and self._session_exists is not None:
            if self._session_exists(request.session_id):
                meta["session"] = True
            else:
                logger.debug("Ignoring unknown or expired note session: %s", request.session_id)

        with self._notes_lock:
            is_new = False
            if request.note_id:
                if not enc_path.exists():
                    if request.create_if_missing:
                        is_new = True
                    else:
                        raise NotepadServiceError(404, "Note not found for update")
            else:
                is_new = True
                while enc_path.exists():
                    note_id = secrets.token_hex(16)
                    _notes_dir, enc_path, meta_path = self._resolve_note_paths(note_id)
                    meta["id"] = note_id

            if not is_new and meta_path.exists():
                existing = self._note_record(note_id, enc_path)
                if existing.created_at:
                    meta["created_at"] = existing.created_at

            self._check_note_storage_accepts(
                note_id,
                len(raw_data),
                replacing_existing=not is_new,
            )
            try:
                self._write_note_pair_atomic(note_id, enc_path, meta_path, raw_data, meta)
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
        """Return a bounded note list sorted by ``updated_at`` descending."""
        notes_dir = self._get_notes_dir()
        notes: list[NoteSummary] = []
        limit = self._storage_policy.max_listed_notes
        truncated = False
        examined = 0

        for enc_path in notes_dir.glob("*.enc"):
            if examined >= limit:
                truncated = True
                break
            examined += 1
            note_id = enc_path.stem
            if is_valid_note_id(note_id):
                notes.append(self._note_record(note_id, enc_path))

        notes.sort(key=lambda note: note.updated_at, reverse=True)
        return ListNotesResult(notes=notes, limit=limit, truncated=truncated)

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

    def _current_note_usage(self, *, exclude_note_id: str | None = None) -> NoteStorageUsage:
        """Return encrypted-note usage, optionally excluding one note being replaced."""
        notes_dir = self._get_notes_dir()
        total_bytes = 0
        note_count = 0

        for enc_path in notes_dir.glob("*.enc"):
            note_id = enc_path.stem
            if not is_valid_note_id(note_id) or note_id == exclude_note_id:
                continue
            try:
                if not enc_path.is_file() or enc_path.is_symlink():
                    continue
                total_bytes += enc_path.stat().st_size
                note_count += 1
            except OSError:
                continue

        return NoteStorageUsage(total_bytes=total_bytes, note_count=note_count)

    def _check_note_storage_accepts(
        self,
        note_id: str,
        new_size: int,
        *,
        replacing_existing: bool,
    ) -> None:
        """Raise when adding or replacing a note would exceed aggregate policy."""
        policy = self._storage_policy
        usage = self._current_note_usage(exclude_note_id=note_id if replacing_existing else None)
        projected_count = usage.note_count + 1
        projected_bytes = usage.total_bytes + new_size

        if policy.max_note_count is not None and projected_count > policy.max_note_count:
            raise NotepadServiceError(
                507,
                (
                    "Notepad note count quota exceeded. "
                    f"Current notes: {usage.note_count}; limit: {policy.max_note_count}."
                ),
            )

        if policy.max_total_bytes is not None and projected_bytes > policy.max_total_bytes:
            raise NotepadServiceError(
                507,
                (
                    "Notepad storage quota exceeded. "
                    f"Current usage: {_format_note_bytes(usage.total_bytes)}; "
                    f"attempted note: {_format_note_bytes(new_size)}; "
                    f"limit: {_format_note_bytes(policy.max_total_bytes)}."
                ),
            )

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
    "MAX_NOTE_ENCRYPTED_BLOB_BYTES",
    "DEFAULT_MAX_NOTES",
    "DEFAULT_MAX_NOTE_STORAGE_BYTES",
    "NotepadService",
    "NotepadServiceError",
    "NoteStoragePolicy",
    "NoteStorageUsage",
    "NoteSummary",
    "SaveNoteRequest",
    "SaveNoteResult",
    "is_valid_note_id",
    "max_note_data_b64_chars",
]
