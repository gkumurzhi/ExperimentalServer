"""Minimal Secure Notepad client demonstrating the ECDH + AES-GCM flow.

Usage:
    python examples/notepad_client.py --url http://127.0.0.1:8080 \\
                                      --note-id myid \\
                                      --text "Hello secret world"

Requires `cryptography` — install with: pip install "exphttp[crypto]"
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
import urllib.request

try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
except ImportError:
    print("This example requires 'cryptography'. Install with: pip install 'exphttp[crypto]'")
    sys.exit(1)


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _b64d(text: str) -> bytes:
    return base64.b64decode(text)


def fetch_server_pubkey(url: str) -> bytes:
    """GET /notes/pubkey returns the server's ECDH P-256 public key (raw)."""
    with urllib.request.urlopen(f"{url}/notes/pubkey") as resp:
        payload = json.loads(resp.read())
    return _b64d(payload["pubkey"])


def derive_shared_key(server_pub_raw: bytes, client_priv: ec.EllipticCurvePrivateKey) -> bytes:
    server_pub = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), server_pub_raw)
    shared = client_priv.exchange(ec.ECDH(), server_pub)
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"exphttp-notepad",
    ).derive(shared)


def encrypt_note(text: str, key: bytes) -> tuple[bytes, bytes]:
    nonce = __import__("os").urandom(12)
    ct = AESGCM(key).encrypt(nonce, text.encode("utf-8"), associated_data=None)
    return nonce, ct


def save_note(url: str, note_id: str, client_pub_raw: bytes, nonce: bytes, ct: bytes) -> None:
    body = json.dumps({
        "pubkey": _b64(client_pub_raw),
        "nonce": _b64(nonce),
        "ciphertext": _b64(ct),
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{url}/notes/{note_id}",
        data=body,
        headers={"Content-Type": "application/json"},
        method="NOTE",
    )
    with urllib.request.urlopen(req) as resp:
        print("Server:", resp.read().decode("utf-8", errors="replace"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--note-id", required=True)
    parser.add_argument("--text", required=True)
    args = parser.parse_args()

    server_pub_raw = fetch_server_pubkey(args.url)
    client_priv = ec.generate_private_key(ec.SECP256R1())
    client_pub_raw = client_priv.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )

    key = derive_shared_key(server_pub_raw, client_priv)
    nonce, ct = encrypt_note(args.text, key)
    save_note(args.url, args.note_id, client_pub_raw, nonce, ct)


if __name__ == "__main__":
    main()
