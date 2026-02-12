"""
Pure-Python RFC 6455 WebSocket helpers (zero external deps).

Provides the minimum functionality needed for the Secure Notepad
real-time transport: upgrade handshake, frame parsing/building,
and close frames.
"""

import base64
import hashlib
import struct

from .http import HTTPRequest

# RFC 6455 magic GUID
_WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

# Opcodes
WS_TEXT = 0x01
WS_BINARY = 0x02
WS_CLOSE = 0x08
WS_PING = 0x09
WS_PONG = 0x0A


def check_websocket_upgrade(request: HTTPRequest) -> bool:
    """Return True if the request is a valid WebSocket upgrade."""
    upgrade = request.headers.get("upgrade", "").lower()
    connection = request.headers.get("connection", "").lower()
    ws_key = request.headers.get("sec-websocket-key", "")
    return upgrade == "websocket" and "upgrade" in connection and len(ws_key) > 0


def build_ws_accept_key(ws_key: str) -> str:
    """Compute ``Sec-WebSocket-Accept`` per RFC 6455 Section 4.2.2."""
    combined = ws_key.strip() + _WS_GUID
    sha1 = hashlib.sha1(combined.encode("ascii")).digest()
    return base64.b64encode(sha1).decode("ascii")


def build_ws_handshake_response(ws_key: str) -> bytes:
    """Build the HTTP 101 Switching Protocols response."""
    accept = build_ws_accept_key(ws_key)
    lines = [
        "HTTP/1.1 101 Switching Protocols",
        "Upgrade: websocket",
        "Connection: Upgrade",
        f"Sec-WebSocket-Accept: {accept}",
        "",
        "",
    ]
    return "\r\n".join(lines).encode("ascii")


def parse_ws_frame(data: bytes) -> tuple[int, bytes, int] | None:
    """
    Parse a single WebSocket frame from *data*.

    Returns ``(opcode, payload, total_bytes_consumed)`` or ``None``
    if *data* does not yet contain a complete frame.

    Handles client-to-server masking (required by RFC 6455).
    """
    dlen = len(data)
    if dlen < 2:
        return None

    # Byte 0: FIN + opcode
    opcode = data[0] & 0x0F

    # Byte 1: MASK flag + payload length
    masked = bool(data[1] & 0x80)
    payload_len = data[1] & 0x7F
    offset = 2

    if payload_len == 126:
        if dlen < 4:
            return None
        payload_len = struct.unpack("!H", data[2:4])[0]
        offset = 4
    elif payload_len == 127:
        if dlen < 10:
            return None
        payload_len = struct.unpack("!Q", data[2:10])[0]
        offset = 10

    mask_key = b""
    if masked:
        if dlen < offset + 4:
            return None
        mask_key = data[offset:offset + 4]
        offset += 4

    if dlen < offset + payload_len:
        return None

    raw_payload = data[offset:offset + payload_len]

    if masked:
        payload = bytearray(payload_len)
        for i in range(payload_len):
            payload[i] = raw_payload[i] ^ mask_key[i % 4]
        payload = bytes(payload)
    else:
        payload = raw_payload

    return opcode, payload, offset + payload_len


def build_ws_frame(payload: bytes, opcode: int = WS_TEXT, fin: bool = True) -> bytes:
    """
    Build a server-to-client WebSocket frame (unmasked).
    """
    header = bytearray()
    first_byte = (0x80 if fin else 0x00) | (opcode & 0x0F)
    header.append(first_byte)

    length = len(payload)
    if length < 126:
        header.append(length)
    elif length < 65536:
        header.append(126)
        header.extend(struct.pack("!H", length))
    else:
        header.append(127)
        header.extend(struct.pack("!Q", length))

    return bytes(header) + payload


def build_ws_close_frame(code: int = 1000, reason: str = "") -> bytes:
    """Build a WebSocket close frame with status code and optional reason."""
    payload = struct.pack("!H", code)
    if reason:
        payload += reason.encode("utf-8")
    return build_ws_frame(payload, opcode=WS_CLOSE)
