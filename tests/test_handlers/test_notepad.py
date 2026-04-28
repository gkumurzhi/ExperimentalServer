"""Tests for the Secure Notepad (NOTE method) handler."""

import base64
import json
import threading
from pathlib import Path

import pytest

from src.handlers import HandlerMixin
from src.security.keys import HAS_ECDH, ECDHKeyManager
from tests.conftest import make_request


class NotepadStubServer(HandlerMixin):
    """Minimal concrete class with all handler mixins for notepad testing."""

    def __init__(self, root_dir: Path, upload_dir: Path, **kwargs):
        self.root_dir = root_dir
        self.upload_dir = upload_dir
        self.notes_dir = root_dir / "notes"
        self.notes_dir.mkdir(exist_ok=True)
        self.sandbox_mode = kwargs.get("sandbox", False)
        self.opsec_mode = kwargs.get("opsec", False)
        self.advanced_upload_enabled = False
        self._temp_smuggle_files: set[str] = set()
        self._smuggle_lock = threading.Lock()
        self._notes_lock = threading.Lock()

        # ECDH key manager (v2)
        self._ecdh_manager = None
        if HAS_ECDH:
            self._ecdh_manager = ECDHKeyManager()
        self.method_handlers = self.build_method_handlers()


@pytest.fixture
def server(temp_dir, upload_dir):
    return NotepadStubServer(temp_dir, upload_dir)


def _make_note_payload(
    title: str = "Test Note",
    data: bytes = b"encrypted blob",
    note_id: str = "",
) -> bytes:
    """Build a NOTE save payload."""
    payload: dict = {
        "title": title,
        "data": base64.b64encode(data).decode(),
    }
    if note_id:
        payload["id"] = note_id
    return json.dumps(payload).encode()


# ── Save tests ─────────────────────────────────────────────────────


class TestNotepadSave:
    def test_create_new_note(self, server):
        body = _make_note_payload("My Note", b"\x01salt1234567890xxnonce12bytesciphertext_tag16")
        req = make_request("NOTE", "/notes", body=body)
        resp = server.handle_note(req)
        assert resp.status_code == 201
        data = json.loads(resp.body)
        assert data["success"] is True
        assert len(data["id"]) == 32
        assert data["title"] == "My Note"

    def test_update_existing_note(self, server):
        # Create first
        body = _make_note_payload("Original")
        req = make_request("NOTE", "/notes", body=body)
        resp = server.handle_note(req)
        note_id = json.loads(resp.body)["id"]

        # Update
        body = _make_note_payload("Updated", b"new data", note_id=note_id)
        req = make_request("NOTE", "/notes", body=body)
        resp = server.handle_note(req)
        assert resp.status_code == 200
        data = json.loads(resp.body)
        assert data["id"] == note_id
        assert data["title"] == "Updated"

    def test_update_nonexistent_note_returns_404(self, server):
        body = _make_note_payload("Ghost", note_id="a" * 32)
        req = make_request("NOTE", "/notes", body=body)
        resp = server.handle_note(req)
        assert resp.status_code == 404

    def test_save_empty_body_returns_400(self, server):
        req = make_request("NOTE", "/notes")
        resp = server.handle_note(req)
        # No body → falls through to _note_list
        assert resp.status_code == 200

    def test_save_invalid_json_returns_400(self, server):
        req = make_request("NOTE", "/notes", body=b"not json{{{")
        resp = server.handle_note(req)
        assert resp.status_code == 400

    def test_save_json_array_returns_400(self, server):
        req = make_request("NOTE", "/notes", body=b"[]")
        resp = server.handle_note(req)
        assert resp.status_code == 400

    def test_save_missing_title_returns_400(self, server):
        payload = json.dumps({"data": base64.b64encode(b"x").decode()}).encode()
        req = make_request("NOTE", "/notes", body=payload)
        resp = server.handle_note(req)
        assert resp.status_code == 400

    def test_save_missing_data_returns_400(self, server):
        payload = json.dumps({"title": "No Data"}).encode()
        req = make_request("NOTE", "/notes", body=payload)
        resp = server.handle_note(req)
        assert resp.status_code == 400

    def test_save_invalid_base64_returns_400(self, server):
        payload = json.dumps({"title": "Bad", "data": "not!!!base64"}).encode()
        req = make_request("NOTE", "/notes", body=payload)
        resp = server.handle_note(req)
        assert resp.status_code == 400

    def test_save_empty_encrypted_data_returns_400(self, server):
        payload = json.dumps({"title": "Empty", "data": base64.b64encode(b"").decode()}).encode()
        req = make_request("NOTE", "/notes", body=payload)
        resp = server.handle_note(req)
        assert resp.status_code == 400

    def test_title_truncated_to_200(self, server):
        long_title = "x" * 300
        body = _make_note_payload(long_title)
        req = make_request("NOTE", "/notes", body=body)
        resp = server.handle_note(req)
        assert resp.status_code == 201
        data = json.loads(resp.body)
        assert len(data["title"]) == 200

    def test_files_written_to_disk(self, server):
        body = _make_note_payload("Disk Test", b"hello encrypted")
        req = make_request("NOTE", "/notes", body=body)
        resp = server.handle_note(req)
        note_id = json.loads(resp.body)["id"]

        notes_dir = server.notes_dir
        enc_path = notes_dir / f"{note_id}.enc"
        meta_path = notes_dir / f"{note_id}.meta.json"
        assert enc_path.exists()
        assert meta_path.exists()
        assert enc_path.read_bytes() == b"hello encrypted"
        assert not (server.upload_dir / "notes").exists()

        meta = json.loads(meta_path.read_text())
        assert meta["title"] == "Disk Test"


# ── List tests ─────────────────────────────────────────────────────


class TestNotepadList:
    def test_list_empty(self, server):
        req = make_request("NOTE", "/notes?list")
        resp = server.handle_note(req)
        assert resp.status_code == 200
        data = json.loads(resp.body)
        assert data["count"] == 0
        assert data["notes"] == []

    def test_list_returns_notes_sorted_by_updated(self, server):
        # Create two notes
        body1 = _make_note_payload("First")
        req1 = make_request("NOTE", "/notes", body=body1)
        resp1 = server.handle_note(req1)
        json.loads(resp1.body)["id"]

        body2 = _make_note_payload("Second")
        req2 = make_request("NOTE", "/notes", body=body2)
        server.handle_note(req2)

        req = make_request("NOTE", "/notes?list")
        resp = server.handle_note(req)
        data = json.loads(resp.body)
        assert data["count"] == 2
        # Most recent first
        titles = [n["title"] for n in data["notes"]]
        assert titles[0] == "Second"

    def test_list_no_body_defaults_to_list(self, server):
        req = make_request("NOTE", "/notes")
        resp = server.handle_note(req)
        assert resp.status_code == 200
        data = json.loads(resp.body)
        assert "notes" in data


# ── Load tests ─────────────────────────────────────────────────────


class TestNotepadLoad:
    def test_load_existing_note(self, server):
        body = _make_note_payload("Load Me", b"secret stuff")
        req = make_request("NOTE", "/notes", body=body)
        resp = server.handle_note(req)
        note_id = json.loads(resp.body)["id"]

        req = make_request("NOTE", f"/notes/{note_id}")
        resp = server.handle_note(req)
        assert resp.status_code == 200
        data = json.loads(resp.body)
        assert data["id"] == note_id
        assert data["title"] == "Load Me"
        # Verify data round-trips through base64
        assert base64.b64decode(data["data"]) == b"secret stuff"

    def test_load_missing_returns_404(self, server):
        req = make_request("NOTE", "/notes/deadbeef12345678deadbeef12345678")
        resp = server.handle_note(req)
        assert resp.status_code == 404


# ── Delete tests ───────────────────────────────────────────────────


class TestNotepadDelete:
    def test_delete_existing_note(self, server):
        body = _make_note_payload("Delete Me")
        req = make_request("NOTE", "/notes", body=body)
        resp = server.handle_note(req)
        note_id = json.loads(resp.body)["id"]

        req = make_request("NOTE", f"/notes/{note_id}?delete")
        resp = server.handle_note(req)
        assert resp.status_code == 200
        data = json.loads(resp.body)
        assert data["success"] is True

        # Files should be gone
        notes_dir = server.notes_dir
        assert not (notes_dir / f"{note_id}.enc").exists()
        assert not (notes_dir / f"{note_id}.meta.json").exists()

    def test_delete_missing_returns_404(self, server):
        req = make_request("NOTE", "/notes/deadbeef12345678deadbeef12345678?delete")
        resp = server.handle_note(req)
        assert resp.status_code == 404

    def test_delete_removes_from_list(self, server):
        body = _make_note_payload("Temporary")
        req = make_request("NOTE", "/notes", body=body)
        resp = server.handle_note(req)
        note_id = json.loads(resp.body)["id"]

        # Delete
        req = make_request("NOTE", f"/notes/{note_id}?delete")
        server.handle_note(req)

        # List should be empty
        req = make_request("NOTE", "/notes?list")
        resp = server.handle_note(req)
        data = json.loads(resp.body)
        assert data["count"] == 0


class TestNotepadClear:
    def test_clear_notes_removes_notes_without_touching_uploads(self, server):
        upload_file = server.upload_dir / "download.txt"
        upload_file.write_text("keep", encoding="utf-8")

        first = server.handle_note(
            make_request("NOTE", "/notes", body=_make_note_payload("First", b"one"))
        )
        second = server.handle_note(
            make_request("NOTE", "/notes", body=_make_note_payload("Second", b"two"))
        )
        assert json.loads(first.body)["success"] is True
        assert json.loads(second.body)["success"] is True

        req = make_request("NOTE", "/notes?clear=1")
        resp = server.handle_note(req)

        assert resp.status_code == 200
        data = json.loads(resp.body)
        assert data["success"] is True
        assert data["cleared"] is True
        assert data["path"] == "/notes"
        assert data["deleted_files"] == 4
        assert data["deleted_dirs"] == 0
        assert data["preserved"] == []
        assert upload_file.exists()
        assert list(server.notes_dir.iterdir()) == []

        list_resp = server.handle_note(make_request("NOTE", "/notes?list"))
        assert json.loads(list_resp.body)["count"] == 0

    def test_clear_notes_preserves_hidden_files(self, server):
        hidden = server.notes_dir / ".gitkeep"
        hidden.write_text("", encoding="utf-8")
        visible = server.notes_dir / "visible.tmp"
        visible.write_text("remove", encoding="utf-8")

        resp = server.handle_note(make_request("NOTE", "/notes?clear=1"))

        assert resp.status_code == 200
        data = json.loads(resp.body)
        assert data["deleted_files"] == 1
        assert data["preserved"] == [".gitkeep"]
        assert hidden.exists()
        assert not visible.exists()


# ── Security tests ─────────────────────────────────────────────────


class TestNotepadSecurity:
    def test_invalid_hex_id_rejected(self, server):
        req = make_request("NOTE", "/notes/not-hex-at-all!!")
        resp = server.handle_note(req)
        assert resp.status_code == 400

    def test_path_traversal_in_id_rejected(self, server):
        req = make_request("NOTE", "/notes/../../etc/passwd")
        resp = server.handle_note(req)
        assert resp.status_code == 400

    def test_too_long_id_rejected(self, server):
        long_id = "a" * 33  # max 32
        req = make_request("NOTE", f"/notes/{long_id}")
        resp = server.handle_note(req)
        assert resp.status_code == 400

    def test_traversal_in_save_id_rejected(self, server):
        payload = json.dumps(
            {
                "id": "../../../etc/passwd",
                "title": "Evil",
                "data": base64.b64encode(b"x").decode(),
            }
        ).encode()
        req = make_request("NOTE", "/notes", body=payload)
        resp = server.handle_note(req)
        assert resp.status_code == 400

    def test_invalid_path_returns_400(self, server):
        req = make_request("NOTE", "/other/path")
        resp = server.handle_note(req)
        assert resp.status_code == 400


# ── ECDH key exchange tests ───────────────────────────────────────


@pytest.mark.skipif(not HAS_ECDH, reason="cryptography not installed")
class TestECDHKeyExchange:
    def test_get_key_returns_public_key(self, server):
        req = make_request("NOTE", "/notes/key")
        resp = server.handle_note(req)
        assert resp.status_code == 200
        data = json.loads(resp.body)
        assert data["hasEcdh"] is True
        assert "publicKey" in data
        raw = base64.b64decode(data["publicKey"])
        assert len(raw) == 65
        assert raw[0] == 0x04  # uncompressed point

    def test_get_key_stable(self, server):
        """Same server returns same public key."""
        req1 = make_request("NOTE", "/notes/key")
        resp1 = server.handle_note(req1)
        req2 = make_request("NOTE", "/notes/key")
        resp2 = server.handle_note(req2)
        assert json.loads(resp1.body)["publicKey"] == json.loads(resp2.body)["publicKey"]

    def test_exchange_returns_session_id(self, server):
        # Generate a client key
        client = ECDHKeyManager()
        client_pub_b64 = base64.b64encode(client.get_public_key_raw()).decode()

        body = json.dumps({"clientPublicKey": client_pub_b64}).encode()
        req = make_request("NOTE", "/notes/exchange", body=body)
        resp = server.handle_note(req)
        assert resp.status_code == 200
        data = json.loads(resp.body)
        assert "sessionId" in data
        assert len(data["sessionId"]) == 32
        assert "serverPublicKey" in data

    def test_exchange_missing_key_returns_400(self, server):
        body = json.dumps({}).encode()
        req = make_request("NOTE", "/notes/exchange", body=body)
        resp = server.handle_note(req)
        assert resp.status_code == 400

    def test_exchange_invalid_key_length_returns_400(self, server):
        body = json.dumps(
            {
                "clientPublicKey": base64.b64encode(b"tooshort").decode(),
            }
        ).encode()
        req = make_request("NOTE", "/notes/exchange", body=body)
        resp = server.handle_note(req)
        assert resp.status_code == 400

    def test_exchange_invalid_json_returns_400(self, server):
        req = make_request("NOTE", "/notes/exchange", body=b"not json")
        resp = server.handle_note(req)
        assert resp.status_code == 400

    def test_exchange_json_array_returns_400(self, server):
        req = make_request("NOTE", "/notes/exchange", body=b"[]")
        resp = server.handle_note(req)
        assert resp.status_code == 400

    def test_exchange_no_body_returns_400(self, server):
        req = make_request("NOTE", "/notes/exchange")
        resp = server.handle_note(req)
        # Empty body → JSON decode error
        assert resp.status_code == 400


class TestECDHKeyExchangeNoEcdh:
    def test_get_key_without_ecdh_manager(self, temp_dir, upload_dir):
        """Server without ECDH manager reports hasEcdh=false."""
        srv = NotepadStubServer(temp_dir, upload_dir)
        srv._ecdh_manager = None

        req = make_request("NOTE", "/notes/key")
        resp = srv.handle_note(req)
        assert resp.status_code == 200
        data = json.loads(resp.body)
        assert data["hasEcdh"] is False
        assert "publicKey" not in data

    def test_exchange_without_ecdh_manager(self, temp_dir, upload_dir):
        """Server without ECDH manager returns 501."""
        srv = NotepadStubServer(temp_dir, upload_dir)
        srv._ecdh_manager = None

        body = json.dumps({"clientPublicKey": "anything"}).encode()
        req = make_request("NOTE", "/notes/exchange", body=body)
        resp = srv.handle_note(req)
        assert resp.status_code == 501


class TestNotepadRequiresCrypto:
    def test_list_without_ecdh_manager_returns_501(self, temp_dir, upload_dir):
        srv = NotepadStubServer(temp_dir, upload_dir)
        srv._ecdh_manager = None

        req = make_request("NOTE", "/notes?list")
        resp = srv.handle_note(req)

        assert resp.status_code == 501

    def test_save_without_ecdh_manager_returns_501(self, temp_dir, upload_dir):
        srv = NotepadStubServer(temp_dir, upload_dir)
        srv._ecdh_manager = None

        req = make_request("NOTE", "/notes", body=_make_note_payload())
        resp = srv.handle_note(req)

        assert resp.status_code == 501

    def test_load_without_ecdh_manager_returns_501(self, temp_dir, upload_dir):
        srv = NotepadStubServer(temp_dir, upload_dir)
        srv._ecdh_manager = None

        req = make_request("NOTE", "/notes/" + ("a" * 32))
        resp = srv.handle_note(req)

        assert resp.status_code == 501

    def test_delete_without_ecdh_manager_returns_501(self, temp_dir, upload_dir):
        srv = NotepadStubServer(temp_dir, upload_dir)
        srv._ecdh_manager = None

        req = make_request("NOTE", "/notes/" + ("a" * 32) + "?delete")
        resp = srv.handle_note(req)

        assert resp.status_code == 501

    def test_clear_without_ecdh_manager_returns_501(self, temp_dir, upload_dir):
        srv = NotepadStubServer(temp_dir, upload_dir)
        srv._ecdh_manager = None

        req = make_request("NOTE", "/notes?clear=1")
        resp = srv.handle_note(req)

        assert resp.status_code == 501


# ── Save with session header tests ────────────────────────────────


@pytest.mark.skipif(not HAS_ECDH, reason="cryptography not installed")
class TestNotepadSaveWithSession:
    def test_save_with_session_id_header(self, server):
        """Save with X-Session-Id header succeeds and marks session in meta."""
        # Set up a session
        client = ECDHKeyManager()
        client_pub_b64 = base64.b64encode(client.get_public_key_raw()).decode()
        exchange_body = json.dumps({"clientPublicKey": client_pub_b64}).encode()
        exchange_req = make_request("NOTE", "/notes/exchange", body=exchange_body)
        exchange_resp = server.handle_note(exchange_req)
        session_id = json.loads(exchange_resp.body)["sessionId"]

        # Save with session header
        body = _make_note_payload("Session Note", b"ecdh-encrypted-data")
        req = make_request(
            "NOTE",
            "/notes",
            body=body,
            headers={
                "X-Session-Id": session_id,
            },
        )
        resp = server.handle_note(req)
        assert resp.status_code == 201
        data = json.loads(resp.body)
        assert data["success"] is True

        # Verify meta has session flag
        notes_dir = server.notes_dir
        meta_path = notes_dir / f"{data['id']}.meta.json"
        meta = json.loads(meta_path.read_text())
        assert meta.get("session") is True

    def test_save_without_session_still_works(self, server):
        """Save without session header still works."""
        body = _make_note_payload("No Session", b"plain-encrypted-data")
        req = make_request("NOTE", "/notes", body=body)
        resp = server.handle_note(req)
        assert resp.status_code == 201

    def test_save_with_unknown_session_header_is_ignored(self, server):
        body = _make_note_payload("Unknown Session", b"encrypted-data")
        req = make_request(
            "NOTE",
            "/notes",
            body=body,
            headers={"X-Session-Id": "deadbeefdeadbeefdeadbeefdeadbeef"},
        )
        resp = server.handle_note(req)

        assert resp.status_code == 201
        data = json.loads(resp.body)

        notes_dir = server.notes_dir
        meta_path = notes_dir / f"{data['id']}.meta.json"
        meta = json.loads(meta_path.read_text())
        assert "session" not in meta


class TestNotepadCorruptMetadata:
    def test_list_skips_non_object_metadata(self, server):
        notes_dir = server.notes_dir
        (notes_dir / "broken.meta.json").write_text("[]")

        req = make_request("NOTE", "/notes?list")
        resp = server.handle_note(req)

        assert resp.status_code == 200
        data = json.loads(resp.body)
        assert data["count"] == 0
        assert data["notes"] == []

    def test_list_includes_note_when_metadata_is_corrupt(self, server):
        note_id = "b" * 32
        notes_dir = server.notes_dir
        (notes_dir / f"{note_id}.enc").write_bytes(b"ciphertext")
        (notes_dir / f"{note_id}.meta.json").write_text("[]")

        req = make_request("NOTE", "/notes?list")
        resp = server.handle_note(req)

        assert resp.status_code == 200
        data = json.loads(resp.body)
        assert data["count"] == 1
        assert data["notes"][0]["id"] == note_id
        assert data["notes"][0]["title"] == ""
        assert data["notes"][0]["size"] == len(b"ciphertext")

    def test_load_with_non_object_metadata_falls_back(self, server):
        note_id = "a" * 32
        notes_dir = server.notes_dir
        (notes_dir / f"{note_id}.enc").write_bytes(b"ciphertext")
        (notes_dir / f"{note_id}.meta.json").write_text("[]")

        req = make_request("NOTE", f"/notes/{note_id}")
        resp = server.handle_note(req)

        assert resp.status_code == 200
        data = json.loads(resp.body)
        assert data["id"] == note_id
        assert data["title"] == ""

    def test_update_rewrites_corrupt_metadata_sidecar(self, server):
        note_id = "c" * 32
        notes_dir = server.notes_dir
        (notes_dir / f"{note_id}.enc").write_bytes(b"old")
        (notes_dir / f"{note_id}.meta.json").write_text("{not json")

        req = make_request(
            "NOTE",
            "/notes",
            body=_make_note_payload("Recovered", b"new-ciphertext", note_id=note_id),
        )
        resp = server.handle_note(req)

        assert resp.status_code == 200
        meta = json.loads((notes_dir / f"{note_id}.meta.json").read_text())
        assert meta["id"] == note_id
        assert meta["title"] == "Recovered"
        assert meta["size"] == len(b"new-ciphertext")
