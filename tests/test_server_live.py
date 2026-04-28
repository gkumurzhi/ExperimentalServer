"""Live end-to-end server coverage for auth, keep-alive, advanced upload, and WebSocket notes."""

from __future__ import annotations

import base64
import json
import socket
import struct
import threading
import time
from pathlib import Path

from src.server import ExperimentalHTTPServer
from src.websocket import WS_CLOSE, WS_TEXT, parse_ws_frame


def _make_masked_frame(opcode: int, payload: bytes) -> bytes:
    """Build a masked client-to-server WebSocket frame."""
    mask_key = b"\x37\x38\x39\x30"
    masked = bytearray(len(payload))
    for i, value in enumerate(payload):
        masked[i] = value ^ mask_key[i % 4]

    header = bytearray()
    header.append(0x80 | opcode)
    length = len(payload)
    if length < 126:
        header.append(0x80 | length)
    elif length < 65536:
        header.append(0x80 | 126)
        header.extend(struct.pack("!H", length))
    else:
        header.append(0x80 | 127)
        header.extend(struct.pack("!Q", length))

    header.extend(mask_key)
    return bytes(header) + bytes(masked)


def _recv_http_response(sock: socket.socket) -> tuple[str, dict[str, str], bytes]:
    """Read a single HTTP response from a live server socket."""
    buffer = bytearray()
    while b"\r\n\r\n" not in buffer:
        chunk = sock.recv(4096)
        if not chunk:
            raise AssertionError("Connection closed before response headers were received")
        buffer.extend(chunk)

    head, body = bytes(buffer).split(b"\r\n\r\n", 1)
    lines = head.decode("iso-8859-1").split("\r\n")
    status_line = lines[0]
    headers: dict[str, str] = {}
    for line in lines[1:]:
        key, value = line.split(":", 1)
        headers[key.lower()] = value.strip()

    content_length = int(headers.get("content-length", "0"))
    while len(body) < content_length:
        chunk = sock.recv(4096)
        if not chunk:
            raise AssertionError("Connection closed before response body was fully received")
        body += chunk

    return status_line, headers, body[:content_length]


def _recv_until(sock: socket.socket, marker: bytes) -> bytes:
    """Read from *sock* until *marker* is present."""
    data = bytearray()
    while marker not in data:
        chunk = sock.recv(4096)
        if not chunk:
            raise AssertionError(f"Connection closed before marker {marker!r} was received")
        data.extend(chunk)
    return bytes(data)


def _recv_ws_json(sock: socket.socket) -> dict[str, object]:
    """Read one complete server-to-client WebSocket JSON message."""
    buffer = bytearray()
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            raise AssertionError("WebSocket closed before a message was received")
        buffer.extend(chunk)
        frame = parse_ws_frame(bytes(buffer))
        if frame is None:
            continue
        opcode, payload, _consumed = frame
        assert opcode == WS_TEXT
        result = json.loads(payload.decode("utf-8"))
        assert isinstance(result, dict)
        return result


def _find_free_port() -> int:
    """Reserve an ephemeral local port and return it."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


class _LiveServer:
    """Small helper for starting and stopping a live server in tests."""

    def __init__(self, root_dir: Path, **kwargs: object) -> None:
        self.server = ExperimentalHTTPServer(
            host="127.0.0.1",
            port=_find_free_port(),
            root_dir=str(root_dir),
            quiet=True,
            **kwargs,
        )
        self.port = self.server.port
        self._thread = threading.Thread(target=self.server.start, daemon=True)

    def __enter__(self) -> _LiveServer:
        self._thread.start()
        for _ in range(100):
            time.sleep(0.05)
            if self.server.running:
                return self
        raise RuntimeError("Server did not start in time")

    def __exit__(self, _exc_type: object, _exc: object, _tb: object) -> None:
        self.server.stop()
        try:
            with socket.create_connection(("127.0.0.1", self.port), timeout=0.2):
                pass
        except OSError:
            pass
        self._thread.join(timeout=3.0)


class TestLiveRequestHandling:
    def test_keep_alive_handles_multiple_ping_requests_on_one_connection(
        self,
        temp_dir: Path,
    ) -> None:
        with _LiveServer(temp_dir) as live:
            with socket.create_connection(("127.0.0.1", live.port), timeout=2.0) as sock:
                sock.settimeout(2.0)

                sock.sendall(
                    (
                        f"PING / HTTP/1.1\r\n"
                        f"Host: 127.0.0.1:{live.port}\r\n"
                        f"Connection: keep-alive\r\n"
                        "\r\n"
                    ).encode("ascii")
                )
                status1, headers1, body1 = _recv_http_response(sock)
                assert status1.startswith("HTTP/1.1 200")
                assert headers1["connection"] == "keep-alive"
                ping1 = json.loads(body1)
                assert ping1["status"] == "pong"
                assert ping1["access_scope"] == "uploads"
                assert ping1["advanced_upload"] is False

                sock.sendall(
                    (
                        f"PING / HTTP/1.1\r\n"
                        f"Host: 127.0.0.1:{live.port}\r\n"
                        f"Connection: close\r\n"
                        "\r\n"
                    ).encode("ascii")
                )
                status2, headers2, body2 = _recv_http_response(sock)
                assert status2.startswith("HTTP/1.1 200")
                assert headers2["connection"] == "close"
                ping2 = json.loads(body2)
                assert ping2["status"] == "pong"
                assert ping2["access_scope"] == "uploads"
                assert ping2["advanced_upload"] is False

    def test_basic_auth_rejects_missing_header_and_accepts_valid_credentials(
        self,
        temp_dir: Path,
    ) -> None:
        with _LiveServer(temp_dir, auth="admin:secret123") as live:
            with socket.create_connection(("127.0.0.1", live.port), timeout=2.0) as sock:
                sock.settimeout(2.0)
                sock.sendall(
                    (f"PING / HTTP/1.1\r\nHost: 127.0.0.1:{live.port}\r\n\r\n").encode("ascii")
                )
                status, headers, body = _recv_http_response(sock)
                assert status.startswith("HTTP/1.1 401")
                assert headers["www-authenticate"] == 'Basic realm="Restricted Area"'
                assert json.loads(body) == {"error": "Unauthorized", "status": 401}

            credentials = base64.b64encode(b"admin:secret123").decode("ascii")
            with socket.create_connection(("127.0.0.1", live.port), timeout=2.0) as sock:
                sock.settimeout(2.0)
                sock.sendall(
                    (
                        f"PING / HTTP/1.1\r\n"
                        f"Host: 127.0.0.1:{live.port}\r\n"
                        f"Authorization: Basic {credentials}\r\n"
                        "\r\n"
                    ).encode("ascii")
                )
                status, _headers, body = _recv_http_response(sock)
                assert status.startswith("HTTP/1.1 200")
                assert json.loads(body)["status"] == "pong"

    def test_get_streamed_text_file_ignores_gzip_without_buffering(self, temp_dir: Path) -> None:
        payload = ("streamed live payload\n" * 200).encode("utf-8")
        upload_dir = temp_dir / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        upload_file = upload_dir / "payload.txt"
        upload_file.write_bytes(payload)

        with _LiveServer(temp_dir) as live:
            with socket.create_connection(("127.0.0.1", live.port), timeout=2.0) as sock:
                sock.settimeout(2.0)
                sock.sendall(
                    (
                        f"GET /payload.txt HTTP/1.1\r\n"
                        f"Host: 127.0.0.1:{live.port}\r\n"
                        "Accept-Encoding: gzip\r\n"
                        "\r\n"
                    ).encode("ascii")
                )
                status, headers, body = _recv_http_response(sock)

        assert status.startswith("HTTP/1.1 200")
        assert headers["content-type"].startswith("text/plain")
        assert headers["content-length"] == str(len(payload))
        assert "content-encoding" not in headers
        assert body == payload


class TestLiveAdvancedUploadRouting:
    def test_advanced_upload_is_disabled_without_mode_flags(
        self,
        temp_dir: Path,
    ) -> None:
        with _LiveServer(temp_dir) as live:
            assert not (temp_dir / ".opsec_config.json").exists()
            with socket.create_connection(("127.0.0.1", live.port), timeout=2.0) as sock:
                sock.settimeout(2.0)
                sock.sendall(
                    (f"PING / HTTP/1.1\r\nHost: 127.0.0.1:{live.port}\r\n\r\n").encode("ascii")
                )
                status, headers, body = _recv_http_response(sock)
                assert status.startswith("HTTP/1.1 200")
                assert headers["server"].startswith("ExperimentalHTTPServer/")
                ping = json.loads(body)
                assert ping["status"] == "pong"
                assert ping["advanced_upload"] is False

            with socket.create_connection(("127.0.0.1", live.port), timeout=2.0) as sock:
                sock.settimeout(2.0)
                sock.sendall(
                    (f"INFO / HTTP/1.1\r\nHost: 127.0.0.1:{live.port}\r\n\r\n").encode("ascii")
                )
                status, _headers, body = _recv_http_response(sock)
                info = json.loads(body)
                assert status.startswith("HTTP/1.1 200")
                assert info["is_directory"] is True
                assert info["path"] == "/"
                assert "contents" in info

            payload = base64.b64encode(b"advanced live upload").decode("ascii")
            with socket.create_connection(("127.0.0.1", live.port), timeout=2.0) as sock:
                sock.settimeout(2.0)
                request_body = f'{{"d":"{payload}","n":"advanced.txt"}}'.encode("ascii")
                sock.sendall(
                    (
                        f"SYNCDATA /advanced HTTP/1.1\r\n"
                        f"Host: 127.0.0.1:{live.port}\r\n"
                        "Content-Type: application/json\r\n"
                        f"Content-Length: {len(request_body)}\r\n"
                        "\r\n"
                    ).encode("ascii")
                    + request_body
                )
                status, _headers, body = _recv_http_response(sock)
                result = json.loads(body)
                assert status.startswith("HTTP/1.1 405")
                assert "not allowed" in result["error"]
                assert not (temp_dir / "uploads" / "advanced.txt").exists()

    def test_unknown_method_with_data_uses_advanced_upload_when_enabled(
        self,
        temp_dir: Path,
    ) -> None:
        with _LiveServer(temp_dir, advanced_upload=True) as live:
            payload = base64.b64encode(b"fallback upload").decode("ascii")

            with socket.create_connection(("127.0.0.1", live.port), timeout=2.0) as sock:
                sock.settimeout(2.0)
                sock.sendall(
                    (
                        f"STEALTH /mystery HTTP/1.1\r\n"
                        f"Host: 127.0.0.1:{live.port}\r\n"
                        f"X-D: {payload}\r\n"
                        "X-N: fallback.txt\r\n"
                        "\r\n"
                    ).encode("ascii")
                )
                status, _headers, body = _recv_http_response(sock)
                result = json.loads(body)
                assert status.startswith("HTTP/1.1 200")
                assert result["ok"] is True
                assert result["transport"] == "headers"
                assert (temp_dir / "uploads" / "fallback.txt").read_bytes() == b"fallback upload"


class TestLiveWebSocketNotes:
    def test_notes_websocket_supports_save_list_and_load_round_trip(self, temp_dir: Path) -> None:
        with _LiveServer(temp_dir) as live:
            with socket.create_connection(("127.0.0.1", live.port), timeout=2.0) as sock:
                sock.settimeout(2.0)
                sock.sendall(
                    (
                        f"GET /notes/ws HTTP/1.1\r\n"
                        f"Host: 127.0.0.1:{live.port}\r\n"
                        "Upgrade: websocket\r\n"
                        "Connection: Upgrade\r\n"
                        "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n"
                        "Sec-WebSocket-Version: 13\r\n"
                        f"Origin: http://127.0.0.1:{live.port}\r\n"
                        "\r\n"
                    ).encode("ascii")
                )
                handshake = _recv_until(sock, b"\r\n\r\n")
                assert b"HTTP/1.1 101 Switching Protocols" in handshake

                note_blob = b"live websocket note"
                note_data = base64.b64encode(note_blob).decode("ascii")
                save_payload = json.dumps(
                    {
                        "type": "save",
                        "title": "Live WS Note",
                        "data": note_data,
                    }
                ).encode("utf-8")
                sock.sendall(_make_masked_frame(WS_TEXT, save_payload))
                saved = _recv_ws_json(sock)
                assert saved["type"] == "saved"
                assert saved["success"] is True
                note_id = str(saved["id"])

                sock.sendall(_make_masked_frame(WS_TEXT, b'{"type":"list"}'))
                listed = _recv_ws_json(sock)
                assert listed["type"] == "list"
                notes = listed["notes"]
                assert isinstance(notes, list)
                assert any(isinstance(note, dict) and note.get("id") == note_id for note in notes)

                load_payload = json.dumps({"type": "load", "id": note_id}).encode("utf-8")
                sock.sendall(_make_masked_frame(WS_TEXT, load_payload))
                loaded = _recv_ws_json(sock)
                assert loaded["type"] == "loaded"
                assert loaded["id"] == note_id
                assert loaded["title"] == "Live WS Note"
                assert loaded["data"] == note_data
                assert (temp_dir / "notes" / f"{note_id}.enc").read_bytes() == note_blob
                assert not (temp_dir / "uploads" / "notes").exists()

                sock.sendall(_make_masked_frame(WS_CLOSE, struct.pack("!H", 1000)))
                close_frame = parse_ws_frame(sock.recv(4096))
                assert close_frame is not None
                assert close_frame[0] == WS_CLOSE
