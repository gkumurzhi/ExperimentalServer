"""Tests for WebSocket message handlers (_handle_ws_message, _ws_handle_save, etc.)."""

import base64
import json
import struct
import threading
from pathlib import Path

import pytest

from src.handlers import HandlerMixin, NotepadHandlersMixin
from src.security.keys import HAS_ECDH
from src.server import ExperimentalHTTPServer
from src.websocket import _MAX_FRAME_SIZE, WS_CLOSE, WS_TEXT, build_ws_frame, parse_ws_frame
from tests.conftest import make_request


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


class _FailingSocket:
    def sendall(self, _data: bytes) -> None:
        raise OSError("send failed")


class _WebSocketLoopSocket(_MockSocket):
    def __init__(self, recv_items: list[bytes | BaseException]):
        super().__init__()
        self._recv_items = list(recv_items)
        self.timeouts: list[float] = []

    def settimeout(self, value: float) -> None:
        self.timeouts.append(value)

    def recv(self, _size: int) -> bytes:
        if not self._recv_items:
            return b""
        item = self._recv_items.pop(0)
        if isinstance(item, BaseException):
            raise item
        return item


class _InvalidResult:
    def to_dict(self) -> list[object]:
        return []


class WSServerStub(HandlerMixin):
    """Minimal server with notepad + WS message handling."""

    _handle_ws_message = NotepadHandlersMixin._handle_ws_message
    _ws_handle_save = NotepadHandlersMixin._ws_handle_save
    _ws_handle_load = NotepadHandlersMixin._ws_handle_load
    _ws_run_note_operation = NotepadHandlersMixin._ws_run_note_operation
    _ws_send_json = staticmethod(NotepadHandlersMixin._ws_send_json)

    def __init__(self, root_dir: Path, upload_dir: Path):
        self.root_dir = root_dir
        self.upload_dir = upload_dir
        self.notes_dir = root_dir / "notes"
        self.notes_dir.mkdir(exist_ok=True)
        self.sandbox_mode = False
        self.opsec_mode = False
        self.advanced_upload_enabled = False
        self._temp_smuggle_files: set[str] = set()
        self._smuggle_lock = threading.Lock()
        self._notes_lock = threading.Lock()

        self._ecdh_manager = None
        if HAS_ECDH:
            from src.security.keys import ECDHKeyManager

            self._ecdh_manager = ECDHKeyManager()
        self.method_handlers = self.build_method_handlers()

    def get_metrics(self):
        return {
            "uptime_seconds": 0,
            "total_requests": 0,
            "total_errors": 0,
            "client_errors": 0,
            "server_errors": 0,
            "bytes_sent": 0,
            "status_counts": {},
        }


@pytest.fixture
def ws_server(temp_dir, upload_dir):
    (temp_dir / "index.html").write_text("<html>ok</html>")
    return WSServerStub(temp_dir, upload_dir)


@pytest.fixture
def mock_socket():
    return _MockSocket()


# ── Invalid input tests ───────────────────────────────────────────


class TestWSClientMasking:
    def test_unmasked_frame_closes_protocol_error_without_dispatch(
        self,
        temp_dir,
        monkeypatch,
    ):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True)
        handled_payloads: list[bytes] = []
        monkeypatch.setattr(
            server,
            "_handle_ws_message",
            lambda _sock, payload: handled_payloads.append(payload),
        )
        server.running = True
        sock = _WebSocketLoopSocket(
            [build_ws_frame(json.dumps({"type": "list"}).encode(), opcode=WS_TEXT)]
        )
        request = make_request(
            "GET",
            "/notes/ws",
            headers={"Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ=="},
        )

        server._handle_notepad_ws(sock, request)

        assert handled_payloads == []
        assert b"HTTP/1.1 101 Switching Protocols" in sock.sent[0]
        assert len(sock.sent) == 2
        protocol_close = parse_ws_frame(sock.sent[1])
        assert protocol_close is not None
        assert protocol_close[0] == WS_CLOSE
        assert struct.unpack("!H", protocol_close[1][:2])[0] == 1002
        assert protocol_close[1][2:] == b"Protocol error"

    def test_incomplete_frame_idle_timeout_closes_without_dispatch(
        self,
        temp_dir,
        monkeypatch,
    ):
        (temp_dir / "index.html").write_text("<html>ok</html>")
        server = ExperimentalHTTPServer(
            root_dir=str(temp_dir),
            quiet=True,
            websocket_frame_idle_timeout=0.01,
        )
        handled_payloads: list[bytes] = []
        monkeypatch.setattr(
            server,
            "_handle_ws_message",
            lambda _sock, payload: handled_payloads.append(payload),
        )
        monotonic_values = iter([0.0, 0.02])
        monkeypatch.setattr("src.server.time.monotonic", lambda: next(monotonic_values))
        server.running = True

        partial_frame = (
            b"\x81\xff" + struct.pack("!Q", _MAX_FRAME_SIZE) + b"\x37\x38\x39\x30" + b"partial"
        )
        sock = _WebSocketLoopSocket([partial_frame, TimeoutError()])
        request = make_request(
            "GET",
            "/notes/ws",
            headers={"Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ=="},
        )

        server._handle_notepad_ws(sock, request)

        assert handled_payloads == []
        assert b"HTTP/1.1 101 Switching Protocols" in sock.sent[0]
        assert sock.timeouts == [60.0, 0.01]
        close_frame = parse_ws_frame(sock.sent[-1])
        assert close_frame is not None
        assert close_frame[0] == WS_CLOSE
        assert struct.unpack("!H", close_frame[1][:2])[0] == 1002
        assert close_frame[1][2:] == b"Incomplete frame timeout"


class TestWSInvalidInput:
    def test_invalid_json_returns_error(self, ws_server, mock_socket):
        ws_server._handle_ws_message(mock_socket, b"not json{{{")
        assert mock_socket.last_json["type"] == "error"
        assert "Invalid JSON" in mock_socket.last_json["error"]

    def test_json_array_returns_object_error(self, ws_server, mock_socket):
        ws_server._handle_ws_message(mock_socket, b"[]")
        assert mock_socket.last_json["type"] == "error"
        assert "Expected JSON object" in mock_socket.last_json["error"]

    def test_unknown_type_returns_error(self, ws_server, mock_socket):
        payload = json.dumps({"type": "bogus"}).encode()
        ws_server._handle_ws_message(mock_socket, payload)
        assert mock_socket.last_json["type"] == "error"
        assert "Unknown type" in mock_socket.last_json["error"]

    def test_non_string_type_returns_unknown_type_error(self, ws_server, mock_socket):
        payload = json.dumps({"type": 123}).encode()
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
        payload = json.dumps(
            {
                "type": "save",
                "title": "WS Note",
                "data": data_b64,
            }
        ).encode()
        ws_server._handle_ws_message(mock_socket, payload)
        msg = mock_socket.last_json
        assert msg["type"] == "saved"
        assert msg["success"] is True
        assert len(msg["id"]) == 32

    def test_save_then_list_shows_note(self, ws_server, mock_socket):
        data_b64 = base64.b64encode(b"data").decode()
        save_payload = json.dumps(
            {
                "type": "save",
                "title": "Listed",
                "data": data_b64,
            }
        ).encode()
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
        save_payload = json.dumps(
            {
                "type": "save",
                "title": "Load Test",
                "data": data_b64,
            }
        ).encode()
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
        save_payload = json.dumps(
            {
                "type": "save",
                "title": "Del Test",
                "data": data_b64,
            }
        ).encode()
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


class TestNoteTransportParity:
    def test_http_and_ws_save_have_same_contract(self, ws_server, mock_socket):
        http_body = json.dumps(
            {
                "title": "HTTP Save",
                "data": base64.b64encode(b"same-shape").decode(),
            }
        ).encode()
        http_resp = ws_server.handle_note(make_request("NOTE", "/notes", body=http_body))
        http_data = json.loads(http_resp.body)

        ws_payload = json.dumps(
            {
                "type": "save",
                "title": "WS Save",
                "data": base64.b64encode(b"same-shape").decode(),
            }
        ).encode()
        ws_server._handle_ws_message(mock_socket, ws_payload)
        ws_data = mock_socket.last_json

        assert http_data["success"] is True
        assert ws_data["type"] == "saved"
        assert ws_data["success"] is True
        assert http_data["size"] == ws_data["size"] == len(b"same-shape")
        assert len(http_data["id"]) == len(ws_data["id"]) == 32

    def test_http_and_ws_list_match(self, ws_server, mock_socket):
        save_body = json.dumps(
            {
                "title": "Parity Note",
                "data": base64.b64encode(b"ciphertext").decode(),
            }
        ).encode()
        save_resp = ws_server.handle_note(make_request("NOTE", "/notes", body=save_body))
        note_id = json.loads(save_resp.body)["id"]

        http_resp = ws_server.handle_note(make_request("NOTE", "/notes?list"))
        http_data = json.loads(http_resp.body)

        ws_server._handle_ws_message(mock_socket, json.dumps({"type": "list"}).encode())
        ws_data = mock_socket.last_json

        assert ws_data["type"] == "list"
        assert ws_data["count"] == http_data["count"]
        assert ws_data["notes"] == http_data["notes"]
        assert ws_data["notes"][0]["id"] == note_id

    def test_http_and_ws_load_match(self, ws_server, mock_socket):
        save_body = json.dumps(
            {
                "title": "Load Parity",
                "data": base64.b64encode(b"load-parity").decode(),
            }
        ).encode()
        save_resp = ws_server.handle_note(make_request("NOTE", "/notes", body=save_body))
        note_id = json.loads(save_resp.body)["id"]

        http_resp = ws_server.handle_note(make_request("NOTE", f"/notes/{note_id}"))
        http_data = json.loads(http_resp.body)

        ws_server._handle_ws_message(
            mock_socket,
            json.dumps({"type": "load", "id": note_id}).encode(),
        )
        ws_data = mock_socket.last_json

        expected_ws = {"type": "loaded", **http_data}
        assert ws_data == expected_ws

    def test_http_and_ws_clear_match(self, ws_server, mock_socket):
        save_body = json.dumps(
            {
                "title": "Clear Parity",
                "data": base64.b64encode(b"clear-parity").decode(),
            }
        ).encode()
        ws_server.handle_note(make_request("NOTE", "/notes", body=save_body))

        http_resp = ws_server.handle_note(make_request("NOTE", "/notes?clear=1"))
        http_data = json.loads(http_resp.body)
        assert http_data["success"] is True

        ws_server.handle_note(make_request("NOTE", "/notes", body=save_body))
        ws_server._handle_ws_message(mock_socket, json.dumps({"type": "clear"}).encode())
        ws_data = mock_socket.last_json

        assert ws_data == {"type": "cleared", **http_data}


class TestWSHelpers:
    def test_ws_run_note_operation_falls_back_for_non_object_payload(self, ws_server):
        result = ws_server._ws_run_note_operation("saved", _InvalidResult)
        assert result == {"error": "Invalid JSON response", "status": 500, "type": "saved"}

    def test_ws_send_json_ignores_socket_send_failures(self) -> None:
        NotepadHandlersMixin._ws_send_json(_FailingSocket(), {"type": "noop"})
