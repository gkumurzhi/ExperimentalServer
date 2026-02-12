"""
Encryption functions for file transfer.

Provides AES-256-GCM authenticated encryption when the ``cryptography``
package is installed, with automatic fallback to XOR obfuscation otherwise.

Wire format for AES-256-GCM (version 0x01):
    version(1) + salt(16) + nonce(12) + ciphertext + tag(16)

HMAC-SHA256 integrity checks are cryptographically sound.
"""

import hashlib
import hmac
import logging
import os
from pathlib import Path

logger = logging.getLogger("httpserver")

# AES-256-GCM version marker
_AES_VERSION: int = 0x01
_AES_SALT_LEN: int = 16
_AES_NONCE_LEN: int = 12
_PBKDF2_ITERATIONS: int = 600_000

# Try to import cryptography for AES-256-GCM support
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.hashes import SHA256
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False


def _derive_aes_key(password: str, salt: bytes) -> bytes:
    """Derive a 256-bit AES key from password using PBKDF2-SHA256."""
    kdf = PBKDF2HMAC(
        algorithm=SHA256(),
        length=32,
        salt=salt,
        iterations=_PBKDF2_ITERATIONS,
    )
    return kdf.derive(password.encode("utf-8"))


def aes_encrypt(data: bytes, password: str) -> bytes:
    """
    Encrypt data with AES-256-GCM using PBKDF2 key derivation.

    Requires the ``cryptography`` package.

    Args:
        data: Plaintext data.
        password: Password for key derivation.

    Returns:
        Encrypted bytes: version(1) + salt(16) + nonce(12) + ciphertext + tag(16).

    Raises:
        RuntimeError: If cryptography package is not installed.
    """
    if not HAS_CRYPTOGRAPHY:
        raise RuntimeError("cryptography package required for AES encryption")

    salt = os.urandom(_AES_SALT_LEN)
    key = _derive_aes_key(password, salt)
    nonce = os.urandom(_AES_NONCE_LEN)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, data, None)  # includes 16-byte tag

    return bytes([_AES_VERSION]) + salt + nonce + ciphertext


def aes_decrypt(data: bytes, password: str) -> bytes | None:
    """
    Decrypt AES-256-GCM encrypted data.

    Args:
        data: Encrypted bytes (version + salt + nonce + ciphertext + tag).
        password: Password for key derivation.

    Returns:
        Decrypted data, or None if decryption/verification fails.

    Raises:
        RuntimeError: If cryptography package is not installed.
    """
    if not HAS_CRYPTOGRAPHY:
        raise RuntimeError("cryptography package required for AES decryption")

    header_len = 1 + _AES_SALT_LEN + _AES_NONCE_LEN
    if len(data) < header_len + 16:  # minimum: header + GCM tag
        return None

    version = data[0]
    if version != _AES_VERSION:
        return None

    salt = data[1:1 + _AES_SALT_LEN]
    nonce = data[1 + _AES_SALT_LEN:header_len]
    ciphertext = data[header_len:]

    try:
        key = _derive_aes_key(password, salt)
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext, None)
    except Exception:
        return None


def encrypt(data: bytes, password: str) -> bytes:
    """
    Encrypt data using the best available method.

    Prefers AES-256-GCM when cryptography is installed, falls back to XOR.

    Args:
        data: Plaintext data.
        password: Password.

    Returns:
        Encrypted bytes.
    """
    if HAS_CRYPTOGRAPHY:
        return aes_encrypt(data, password)
    logger.warning("cryptography not installed — falling back to XOR obfuscation")
    return xor_bytes(data, password)


def decrypt(data: bytes, password: str) -> bytes | None:
    """
    Decrypt data, auto-detecting the format.

    If the data starts with the AES version marker, uses AES-256-GCM.
    Otherwise falls back to XOR decryption.

    Args:
        data: Encrypted data.
        password: Password.

    Returns:
        Decrypted data, or None if AES decryption fails.
    """
    if len(data) > 0 and data[0] == _AES_VERSION and HAS_CRYPTOGRAPHY:
        return aes_decrypt(data, password)
    # XOR fallback (symmetric, always succeeds)
    return xor_bytes(data, password)


def xor_bytes(data: bytes, password: str) -> bytes:
    """
    XOR data with password key. Symmetric: encrypt == decrypt.

    Args:
        data: Data to process.
        password: Password (key).

    Returns:
        Processed data.
    """
    if not password:
        return data

    key_bytes = password.encode('utf-8')
    result = bytearray(len(data))

    for i in range(len(data)):
        result[i] = data[i] ^ key_bytes[i % len(key_bytes)]

    return bytes(result)


# Backward-compatible aliases
xor_encrypt = xor_bytes
xor_decrypt = xor_bytes


def xor_file(input_path: str, output_path: str, password: str) -> int:
    """
    XOR a file with password. Works for both encryption and decryption.

    Args:
        input_path: Path to the source file.
        output_path: Path to save the result.
        password: Password.

    Returns:
        File size in bytes.
    """
    with Path(input_path).open('rb') as f:
        data = f.read()

    result = xor_bytes(data, password)

    with Path(output_path).open('wb') as f:
        f.write(result)

    return len(result)


# Backward-compatible aliases
xor_encrypt_file = xor_file
xor_decrypt_file = xor_file


def compute_hmac(data: bytes, key: str) -> str:
    """
    Compute HMAC-SHA256 for data integrity verification.

    Args:
        data: Data to sign.
        key: HMAC key.

    Returns:
        Hex-encoded HMAC string.
    """
    return hmac.new(key.encode('utf-8'), data, hashlib.sha256).hexdigest()


def verify_hmac(data: bytes, key: str, expected_hmac: str) -> bool:
    """
    Verify HMAC-SHA256.

    Args:
        data: Data to verify.
        key: HMAC key.
        expected_hmac: Expected HMAC value.

    Returns:
        True if the HMAC is valid.
    """
    computed = compute_hmac(data, key)
    return hmac.compare_digest(computed, expected_hmac)


def xor_encrypt_with_hmac(data: bytes, password: str) -> tuple[bytes, str]:
    """
    XOR encryption with HMAC for integrity verification.

    Args:
        data: Data to encrypt.
        password: Password.

    Returns:
        Tuple (encrypted data, HMAC).
    """
    encrypted = xor_bytes(data, password)
    mac = compute_hmac(encrypted, password)
    return encrypted, mac


def xor_decrypt_with_hmac(data: bytes, password: str, mac: str) -> bytes | None:
    """
    XOR decryption with HMAC verification.

    Args:
        data: Encrypted data.
        password: Password.
        mac: HMAC to verify.

    Returns:
        Decrypted data or None if HMAC is invalid.
    """
    if not verify_hmac(data, password, mac):
        return None
    return xor_bytes(data, password)
