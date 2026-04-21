"""Minimal Secure Notepad client for the current NOTE API.

Usage:
    python examples/notepad_client.py --url http://127.0.0.1:8080 \
                                      --title "Example Note" \
                                      --text "Hello secret world"

Optional:
    --note-id <hex>    Update an existing note instead of creating a new one.

Requires `cryptography`:
    pip install "exphttp[crypto]"
"""

from __future__ import annotations

import argparse
import base64
import http.client
import json
import os
import re
import sys
from urllib.parse import urlsplit

try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
except ImportError:
    print("This example requires 'cryptography'. Install with: pip install 'exphttp[crypto]'")
    sys.exit(1)


_NOTE_ID_RE = re.compile(r"^[a-f0-9]{1,32}$")


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _b64d(text: str) -> bytes:
    return base64.b64decode(text)


def _note_request(
    base_url: str,
    path: str,
    *,
    payload: dict[str, object] | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, object]:
    parsed = urlsplit(base_url.rstrip("/"))
    if parsed.scheme not in ("http", "https"):
        raise RuntimeError("URL must use http:// or https://")
    if not parsed.hostname:
        raise RuntimeError("URL must include a hostname")

    data = None
    request_headers: dict[str, str] = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        request_headers["Content-Type"] = "application/json"
    if headers:
        request_headers.update(headers)

    conn_cls = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
    conn = conn_cls(parsed.hostname, parsed.port, timeout=10)
    request_path = f"{parsed.path.rstrip('/')}{path}" if parsed.path else path

    try:
        conn.request("NOTE", request_path, body=data, headers=request_headers)
        resp = conn.getresponse()
        raw = resp.read()
    finally:
        conn.close()

    if resp.status >= 400:
        detail = raw.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"NOTE {request_path} failed: HTTP {resp.status} {detail}")

    return json.loads(raw.decode("utf-8")) if raw else {}


def fetch_server_public_key(url: str) -> bytes:
    payload = _note_request(url, "/notes/key")
    if not payload.get("hasEcdh"):
        raise RuntimeError("Server reports that ECDH is unavailable")
    public_key = payload.get("publicKey")
    if not isinstance(public_key, str) or not public_key:
        raise RuntimeError("Server did not return a usable public key")
    return _b64d(public_key)


def exchange_session(
    url: str,
    client_pub_raw: bytes,
) -> tuple[str, bytes]:
    payload = _note_request(
        url,
        "/notes/exchange",
        payload={"clientPublicKey": _b64(client_pub_raw)},
    )
    session_id = payload.get("sessionId")
    server_public_key = payload.get("serverPublicKey")
    if not isinstance(session_id, str) or not session_id:
        raise RuntimeError("Server did not return a session ID")
    if not isinstance(server_public_key, str) or not server_public_key:
        raise RuntimeError("Server did not return an exchange public key")
    return session_id, _b64d(server_public_key)


def derive_shared_key(server_pub_raw: bytes, client_priv: ec.EllipticCurvePrivateKey) -> bytes:
    server_pub = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), server_pub_raw)
    shared = client_priv.exchange(ec.ECDH(), server_pub)
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"exphttp-notepad",
    ).derive(shared)


def encrypt_note(text: str, key: bytes) -> bytes:
    nonce = os.urandom(12)
    ciphertext = AESGCM(key).encrypt(nonce, text.encode("utf-8"), associated_data=None)
    return nonce + ciphertext


def decrypt_note(blob: bytes, key: bytes) -> str:
    if len(blob) < 12 + 16:
        raise RuntimeError("Encrypted note is too short to contain nonce + tag")
    nonce = blob[:12]
    ciphertext = blob[12:]
    plaintext = AESGCM(key).decrypt(nonce, ciphertext, associated_data=None)
    return plaintext.decode("utf-8")


def save_note(
    url: str,
    *,
    title: str,
    text: str,
    key: bytes,
    session_id: str,
    note_id: str | None,
) -> dict[str, object]:
    encrypted_blob = encrypt_note(text, key)
    body: dict[str, object] = {
        "title": title,
        "data": _b64(encrypted_blob),
    }
    if note_id:
        body["id"] = note_id
    return _note_request(url, "/notes", payload=body, headers={"X-Session-Id": session_id})


def load_note(url: str, note_id: str) -> dict[str, object]:
    return _note_request(url, f"/notes/{note_id}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True, help="Base server URL, for example http://127.0.0.1:8080")
    parser.add_argument("--title", default="Example Note", help="Note title to save")
    parser.add_argument("--text", required=True, help="Plaintext note content to encrypt and save")
    parser.add_argument(
        "--note-id",
        help="Optional hex note ID (1-32 lowercase hex chars) to update an existing note",
    )
    args = parser.parse_args()

    if args.note_id and not _NOTE_ID_RE.match(args.note_id):
        parser.error("--note-id must be 1-32 lowercase hex characters")

    advertised_server_key = fetch_server_public_key(args.url)
    client_priv = ec.generate_private_key(ec.SECP256R1())
    client_pub_raw = client_priv.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )

    session_id, exchanged_server_key = exchange_session(args.url, client_pub_raw)
    if exchanged_server_key != advertised_server_key:
        raise RuntimeError("Server public key changed between /notes/key and /notes/exchange")

    shared_key = derive_shared_key(exchanged_server_key, client_priv)
    saved = save_note(
        args.url,
        title=args.title,
        text=args.text,
        key=shared_key,
        session_id=session_id,
        note_id=args.note_id,
    )

    saved_note_id = saved.get("id")
    if not isinstance(saved_note_id, str) or not saved_note_id:
        raise RuntimeError(f"Unexpected save response: {saved!r}")

    loaded = load_note(args.url, saved_note_id)
    encrypted_data = loaded.get("data")
    if not isinstance(encrypted_data, str) or not encrypted_data:
        raise RuntimeError(f"Unexpected load response: {loaded!r}")

    decrypted_text = decrypt_note(_b64d(encrypted_data), shared_key)

    print(f"Saved note: {saved_note_id}")
    print(f"Title: {loaded.get('title', args.title)}")
    print(f"Decrypted text: {decrypted_text}")


if __name__ == "__main__":
    main()
