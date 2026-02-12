"""
ECDH key exchange manager for Secure Notepad v2.

Uses Elliptic Curve Diffie-Hellman (P-256) to negotiate a shared
AES-256-GCM encryption key between client and server without any
user-entered password.

Wire format for encrypted messages:
    nonce(12) + ciphertext + tag(16)

Requires the ``cryptography`` package.
"""

import logging
import os
import secrets

logger = logging.getLogger("httpserver")

HAS_ECDH = False

try:
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.hashes import SHA256
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    from cryptography.hazmat.primitives.serialization import (
        Encoding,
        PublicFormat,
    )

    HAS_ECDH = True
except ImportError:
    pass

_HKDF_SALT = b"\x00" * 32
_HKDF_INFO = b"notepad-e2e-key"
_NONCE_LEN = 12


class ECDHKeyManager:
    """Manages ECDH key pairs and per-session derived AES-256-GCM keys."""

    def __init__(self) -> None:
        if not HAS_ECDH:
            raise RuntimeError("cryptography package required for ECDH")
        self._private_key = ec.generate_private_key(ec.SECP256R1())
        self._sessions: dict[str, bytes] = {}

    def get_public_key_raw(self) -> bytes:
        """Return the server's public key as 65-byte uncompressed point."""
        return self._private_key.public_key().public_bytes(
            encoding=Encoding.X962,
            format=PublicFormat.UncompressedPoint,
        )

    def derive_session(self, client_pub_raw: bytes) -> tuple[str, bytes]:
        """
        Perform ECDH key exchange with a client's raw public key.

        Args:
            client_pub_raw: 65-byte uncompressed EC P-256 public key.

        Returns:
            (session_id, derived_aes_key) — 32-byte AES key.
        """
        client_pub = ec.EllipticCurvePublicKey.from_encoded_point(
            ec.SECP256R1(), client_pub_raw,
        )
        shared_secret = self._private_key.exchange(ec.ECDH(), client_pub)

        derived_key = HKDF(
            algorithm=SHA256(),
            length=32,
            salt=_HKDF_SALT,
            info=_HKDF_INFO,
        ).derive(shared_secret)

        session_id = secrets.token_hex(16)
        self._sessions[session_id] = derived_key
        logger.debug("ECDH session created: %s", session_id)
        return session_id, derived_key

    def get_session_key(self, session_id: str) -> bytes | None:
        """Return the AES key for a session, or None if unknown."""
        return self._sessions.get(session_id)

    def remove_session(self, session_id: str) -> None:
        """Remove a session (e.g. on disconnect)."""
        self._sessions.pop(session_id, None)

    def encrypt(self, session_id: str, plaintext: bytes) -> bytes:
        """
        Encrypt data with the session's AES-256-GCM key.

        Returns:
            nonce(12) + ciphertext + tag(16).
        """
        key = self._sessions.get(session_id)
        if key is None:
            raise ValueError(f"Unknown session: {session_id}")
        nonce = os.urandom(_NONCE_LEN)
        aesgcm = AESGCM(key)
        ct = aesgcm.encrypt(nonce, plaintext, None)
        return nonce + ct

    def decrypt(self, session_id: str, data: bytes) -> bytes:
        """
        Decrypt data with the session's AES-256-GCM key.

        Args:
            data: nonce(12) + ciphertext + tag(16).
        """
        key = self._sessions.get(session_id)
        if key is None:
            raise ValueError(f"Unknown session: {session_id}")
        if len(data) < _NONCE_LEN + 16:
            raise ValueError("Data too short")
        nonce = data[:_NONCE_LEN]
        ct = data[_NONCE_LEN:]
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ct, None)
