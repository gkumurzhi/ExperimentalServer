"""Tests for WebSocket message handlers (_handle_ws_message, _ws_handle_save, etc.)."""

import base64
import json
import threading
from pathlib import Path

import pytest

from src.handlers import HandlerMixin
from src.http import HTTPRequest
from src.security.keys import HAS_ECDH
from src.websocket import build_ws_frame, parse_ws_frame


class _MockSocket:
    """Captures sendall() calls for WebSocket frame inspection."""

    def __init__(self):
        self.sent: list[bytes] = []

    def sendall(self, data: bytes) -> None:
        self.sent.append(data)

    def get_json_messages(self) -> list[dict]:
        """Parse all sent WS frames as JSON messages."""
        messages = []
        for raw in self.sent:
            frame = parse_ws_frame(raw)
            if frame is None:
                continue
            _opcode, payload, _consumed = frame
            try:
                messages.append(json.loads(payload.decode("utf-8")))
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
        return messages

    @property
    def last_json(self) -> dict:
        msgs = self.get_json_messages()
        assert msgs, "No JSON messages were sent"
        return msgs[-1]


class WSServerStub(HandlerMixin):
    """Minimal server with notepad + WS message handling."""

    def __init__(self, root_dir: Path, upload_dir: Path):
        self.root_dir = root_dir
        self.upload_dir = upload_dir
        self.sandbox_mode = False
        self.opsec_mode = False
        self._temp_smuggle_files: set[str] = set()
        self._smuggle_lock = threading.Lock()
        self._notes_lock = threading.Lock()
        self.method_handlers = {
            "GET": self.handle_get,
            "NOTE": self.handle_note,
        }

        self._ecdh_manager = None
        if HAS_ECDH:
            from src.security.keys import ECDHKeyManager
            self._ecdh_manager = ECDHKeyManager()

    def get_metrics(self):
        return {"uptime_seconds": 0, "total_requests": 0, "total_errors": 0,
                "bytes_sent": 0, "status_counts": {}}

    # Mirror of server._handle_ws_message
    def _handle_ws_message(self, sock, payload: bytes) -> None:
        import re as _re
        _NOTE_ID_RE_WS = _re.compile(r"^[a-f0-9]{1,32}$")

        try:
            msg = json.loads(payload.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._ws_send_json(sock, {"type": "error", "error": "Invalid JSON"})
            return

        msg_type = msg.get("type", "")

        if msg_type == "save":
            self._ws_handle_save(sock, msg)
        elif msg_type == "load":
            self._ws_handle_load(sock, msg)
        elif msg_type == "list":
            resp = self._note_list()
            result = json.loads(resp.body)
            result["type"] = "list"
            self._ws_send_json(sock, result)
        elif msg_type == "delete":
            note_id = msg.get("id", "")
            if note_id and _NOTE_ID_RE_WS.match(note_id):
                resp = self._note_delete(note_id)
                result = json.loads(resp.body)
                result["type"] = "deleted"
                self._ws_send_json(sock, result)
            else:
                self._ws_send_json(sock, {"type": "error", "error": "Invalid note ID"})
        else:
            self._ws_send_json(sock, {"type": "error", "error": f"Unknown type: {msg_type}"})

    def _ws_handle_save(self, sock, msg: dict) -> None:
        title = msg.get("title", "")
        data = msg.get("data", "")
        note_id = msg.get("noteId", "")
        session_id = msg.get("sessionId", "")

        payload = {"title": title, "data": data}
        if note_id:
            payload["id"] = note_id

        body = json.dumps(payload).encode("utf-8")
        headers = f"NOTE /notes HTTP/1.1\r\nContent-Length: {len(body)}\r\n"
        if session_id:
            headers += f"X-Session-Id: {session_id}\r\n"
        raw = headers.encode() + b"\r\n" + body
        req = HTTPRequest(raw)
        resp = self.handle_note(req)
        result = json.loads(resp.body)
        result["type"] = "saved"
        self._ws_send_json(sock, result)

    def _ws_handle_load(self, sock, msg: dict) -> None:
        import re as _re
        _NOTE_ID_RE_WS = _re.compile(r"^[a-f0-9]{1,32}$")
        note_id = msg.get("id", "")
        if not note_id or not _NOTE_ID_RE_WS.match(note_id):
            self._ws_send_json(sock, {"type": "error", "error": "Invalid note ID"})
            return
        resp = self._note_load(note_id)
        result = json.loads(resp.body)
        result["type"] = "loaded"
        self._ws_send_json(sock, result)

    @staticmethod
    def _ws_send_json(sock, data: dict) -> None:
        frame = build_ws_frame(json.dumps(data).encode("utf-8"))
        try:
            sock.sendall(frame)
        except Exception:
            pass


@pytest.fixture
def ws_server(temp_dir, upload_dir):
    (temp_dir / "index.html").write_text("<html>ok</html>")
    return WSServerStub(temp_dir, upload_dir)


@pytest.fixture
def mock_socket():
    return _MockSocket()


# ── Invalid input tests ───────────────────────────────────────────

class TestWSInvalidInput:
    def test_invalid_json_returns_error(self, ws_server, mock_socket):
        ws_server._handle_ws_message(mock_socket, b"not json{{{")
        assert mock_socket.last_json["type"] == "error"
        assert "Invalid JSON" in mock_socket.last_json["error"]

    def test_unknown_type_returns_error(self, ws_server, mock_socket):
        payload = json.dumps({"type": "bogus"}).encode()
        ws_server._handle_ws_message(mock_socket, payload)
        assert mock_socket.last_json["type"] == "error"
        assert "Unknown type" in mock_socket.last_json["error"]

    def test_empty_payload_returns_error(self, ws_server, mock_socket):
        ws_server._handle_ws_message(mock_socket, b"")
        assert mock_socket.last_json["type"] == "error"


# ── List tests ────────────────────────────────────────────────────

class TestWSList:
    def test_list_empty(self, ws_server, mock_socket):
        payload = json.dumps({"type": "list"}).encode()
        ws_server._handle_ws_message(mock_socket, payload)
        msg = mock_socket.last_json
        assert msg["type"] == "list"
        assert msg["count"] == 0
        assert msg["notes"] == []


# ── Save tests ────────────────────────────────────────────────────

class TestWSSave:
    def test_save_creates_note(self, ws_server, mock_socket):
        data_b64 = base64.b64encode(b"encrypted blob").decode()
        payload = json.dumps({
            "type": "save",
            "title": "WS Note",
            "data": data_b64,
        }).encode()
        ws_server._handle_ws_message(mock_socket, payload)
        msg = mock_socket.last_json
        assert msg["type"] == "saved"
        assert msg["success"] is True
        assert len(msg["id"]) == 32

    def test_save_then_list_shows_note(self, ws_server, mock_socket):
        data_b64 = base64.b64encode(b"data").decode()
        save_payload = json.dumps({
            "type": "save", "title": "Listed", "data": data_b64,
        }).encode()
        ws_server._handle_ws_message(mock_socket, save_payload)

        list_payload = json.dumps({"type": "list"}).encode()
        ws_server._handle_ws_message(mock_socket, list_payload)
        msg = mock_socket.last_json
        assert msg["type"] == "list"
        assert msg["count"] == 1
        assert msg["notes"][0]["title"] == "Listed"


# ── Load tests ────────────────────────────────────────────────────

class TestWSLoad:
    def test_load_existing_note(self, ws_server, mock_socket):
        # Save first
        data_b64 = base64.b64encode(b"load me").decode()
        save_payload = json.dumps({
            "type": "save", "title": "Load Test", "data": data_b64,
        }).encode()
        ws_server._handle_ws_message(mock_socket, save_payload)
        note_id = mock_socket.last_json["id"]

        # Load
        load_payload = json.dumps({"type": "load", "id": note_id}).encode()
        ws_server._handle_ws_message(mock_socket, load_payload)
        msg = mock_socket.last_json
        assert msg["type"] == "loaded"
        assert msg["id"] == note_id
        assert base64.b64decode(msg["data"]) == b"load me"

    def test_load_invalid_id_returns_error(self, ws_server, mock_socket):
        payload = json.dumps({"type": "load", "id": "ZZZZ!!!"}).encode()
        ws_server._handle_ws_message(mock_socket, payload)
        msg = mock_socket.last_json
        assert msg["type"] == "error"
        assert "Invalid note ID" in msg["error"]

    def test_load_missing_id_returns_error(self, ws_server, mock_socket):
        payload = json.dumps({"type": "load"}).encode()
        ws_server._handle_ws_message(mock_socket, payload)
        msg = mock_socket.last_json
        assert msg["type"] == "error"

    def test_load_nonexistent_returns_404(self, ws_server, mock_socket):
        payload = json.dumps({"type": "load", "id": "a" * 32}).encode()
        ws_server._handle_ws_message(mock_socket, payload)
        msg = mock_socket.last_json
        assert msg["type"] == "loaded"
        assert msg.get("error") or msg.get("status") == 404


# ── Delete tests ──────────────────────────────────────────────────

class TestWSDelete:
    def test_delete_existing_note(self, ws_server, mock_socket, upload_dir):
        # Save
        data_b64 = base64.b64encode(b"delete me").decode()
        save_payload = json.dumps({
            "type": "save", "title": "Del Test", "data": data_b64,
        }).encode()
        ws_server._handle_ws_message(mock_socket, save_payload)
        note_id = mock_socket.last_json["id"]

        # Delete
        del_payload = json.dumps({"type": "delete", "id": note_id}).encode()
        ws_server._handle_ws_message(mock_socket, del_payload)
        msg = mock_socket.last_json
        assert msg["type"] == "deleted"
        assert msg["success"] is True

        # Verify list is empty
        list_payload = json.dumps({"type": "list"}).encode()
        ws_server._handle_ws_message(mock_socket, list_payload)
        assert mock_socket.last_json["count"] == 0

    def test_delete_invalid_id_returns_error(self, ws_server, mock_socket):
        payload = json.dumps({"type": "delete", "id": "!@#$"}).encode()
        ws_server._handle_ws_message(mock_socket, payload)
        assert mock_socket.last_json["type"] == "error"

    def test_delete_empty_id_returns_error(self, ws_server, mock_socket):
        payload = json.dumps({"type": "delete", "id": ""}).encode()
        ws_server._handle_ws_message(mock_socket, payload)
        assert mock_socket.last_json["type"] == "error"
