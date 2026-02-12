"""Tests for cryptographic functions."""

from pathlib import Path

from src.security.crypto import (
    HAS_CRYPTOGRAPHY,
    aes_decrypt,
    aes_encrypt,
    compute_hmac,
    decrypt,
    encrypt,
    verify_hmac,
    xor_decrypt,
    xor_decrypt_file,
    xor_decrypt_with_hmac,
    xor_encrypt,
    xor_encrypt_file,
    xor_encrypt_with_hmac,
)


class TestXOREncryption:
    """Tests for XOR encryption/decryption."""

    def test_encrypt_decrypt_roundtrip(self):
        """Test that encrypt then decrypt returns original data."""
        data = b"Hello, World!"
        password = "secret_key"

        encrypted = xor_encrypt(data, password)
        decrypted = xor_decrypt(encrypted, password)

        assert decrypted == data

    def test_encryption_changes_data(self):
        """Test that encryption produces different data."""
        data = b"Hello, World!"
        password = "secret_key"

        encrypted = xor_encrypt(data, password)

        assert encrypted != data

    def test_different_passwords_different_results(self):
        """Test that different passwords produce different encrypted data."""
        data = b"Hello, World!"

        encrypted1 = xor_encrypt(data, "key1")
        encrypted2 = xor_encrypt(data, "key2")

        assert encrypted1 != encrypted2

    def test_empty_password_returns_original(self):
        """Test that empty password returns original data."""
        data = b"Hello, World!"

        assert xor_encrypt(data, "") == data
        assert xor_decrypt(data, "") == data

    def test_binary_data(self):
        """Test encryption of binary data."""
        data = bytes(range(256))
        password = "binary_key"

        encrypted = xor_encrypt(data, password)
        decrypted = xor_decrypt(encrypted, password)

        assert decrypted == data


class TestXORFileEncryption:
    """Tests for XOR file encryption/decryption."""

    def test_encrypt_file(self, temp_dir: Path):
        """Test file encryption."""
        input_file = temp_dir / "input.txt"
        output_file = temp_dir / "output.enc"
        input_file.write_bytes(b"Test content for encryption")

        size = xor_encrypt_file(str(input_file), str(output_file), "password")

        assert output_file.exists()
        assert size == len(b"Test content for encryption")
        assert output_file.read_bytes() != input_file.read_bytes()

    def test_decrypt_file(self, temp_dir: Path):
        """Test file decryption."""
        input_file = temp_dir / "input.txt"
        encrypted_file = temp_dir / "encrypted.enc"
        decrypted_file = temp_dir / "decrypted.txt"
        original_content = b"Original content"

        input_file.write_bytes(original_content)
        xor_encrypt_file(str(input_file), str(encrypted_file), "password")
        xor_decrypt_file(str(encrypted_file), str(decrypted_file), "password")

        assert decrypted_file.read_bytes() == original_content


class TestHMAC:
    """Tests for HMAC functions."""

    def test_compute_hmac(self):
        """Test HMAC computation."""
        data = b"test data"
        key = "secret_key"

        hmac_value = compute_hmac(data, key)

        assert isinstance(hmac_value, str)
        assert len(hmac_value) == 64  # SHA256 hex digest

    def test_verify_hmac_valid(self):
        """Test HMAC verification with valid HMAC."""
        data = b"test data"
        key = "secret_key"

        hmac_value = compute_hmac(data, key)

        assert verify_hmac(data, key, hmac_value) is True

    def test_verify_hmac_invalid(self):
        """Test HMAC verification with invalid HMAC."""
        data = b"test data"
        key = "secret_key"

        assert verify_hmac(data, key, "invalid_hmac") is False

    def test_verify_hmac_wrong_key(self):
        """Test HMAC verification with wrong key."""
        data = b"test data"

        hmac_value = compute_hmac(data, "key1")

        assert verify_hmac(data, "key2", hmac_value) is False

    def test_verify_hmac_modified_data(self):
        """Test HMAC verification with modified data."""
        data = b"original data"
        key = "secret_key"

        hmac_value = compute_hmac(data, key)

        assert verify_hmac(b"modified data", key, hmac_value) is False


class TestXORWithHMAC:
    """Tests for XOR encryption with HMAC."""

    def test_encrypt_with_hmac(self):
        """Test encryption with HMAC generation."""
        data = b"sensitive data"
        password = "password"

        encrypted, hmac_value = xor_encrypt_with_hmac(data, password)

        assert encrypted != data
        assert len(hmac_value) == 64

    def test_decrypt_with_hmac_valid(self):
        """Test decryption with valid HMAC."""
        data = b"sensitive data"
        password = "password"

        encrypted, hmac_value = xor_encrypt_with_hmac(data, password)
        decrypted = xor_decrypt_with_hmac(encrypted, password, hmac_value)

        assert decrypted == data

    def test_decrypt_with_hmac_invalid(self):
        """Test decryption with invalid HMAC returns None."""
        data = b"sensitive data"
        password = "password"

        encrypted, _ = xor_encrypt_with_hmac(data, password)
        result = xor_decrypt_with_hmac(encrypted, password, "invalid_hmac")

        assert result is None

    def test_decrypt_with_hmac_tampered_data(self):
        """Test decryption of tampered data returns None."""
        data = b"sensitive data"
        password = "password"

        encrypted, hmac_value = xor_encrypt_with_hmac(data, password)
        tampered = bytes([b ^ 1 for b in encrypted])  # Flip bits
        result = xor_decrypt_with_hmac(tampered, password, hmac_value)

        assert result is None


class TestAES256GCM:
    """Tests for AES-256-GCM encryption/decryption."""

    def test_aes_encrypt_decrypt_roundtrip(self):
        """Test AES encrypt then decrypt returns original data."""
        assert HAS_CRYPTOGRAPHY, "cryptography package required"
        data = b"Hello, AES-256-GCM!"
        password = "strong_password"

        encrypted = aes_encrypt(data, password)
        decrypted = aes_decrypt(encrypted, password)

        assert decrypted == data

    def test_aes_version_marker(self):
        """Test that AES ciphertext starts with version byte 0x01."""
        assert HAS_CRYPTOGRAPHY
        encrypted = aes_encrypt(b"test", "pw")
        assert encrypted[0] == 0x01

    def test_aes_different_each_time(self):
        """Test that two encryptions of same data differ (random salt/nonce)."""
        assert HAS_CRYPTOGRAPHY
        data = b"same data"
        enc1 = aes_encrypt(data, "pw")
        enc2 = aes_encrypt(data, "pw")
        assert enc1 != enc2

    def test_aes_wrong_password(self):
        """Test that wrong password returns None."""
        assert HAS_CRYPTOGRAPHY
        encrypted = aes_encrypt(b"secret", "correct_pw")
        result = aes_decrypt(encrypted, "wrong_pw")
        assert result is None

    def test_aes_tampered_ciphertext(self):
        """Test that tampered ciphertext returns None."""
        assert HAS_CRYPTOGRAPHY
        encrypted = aes_encrypt(b"data", "pw")
        tampered = bytearray(encrypted)
        tampered[-1] ^= 0xFF  # Flip last byte (part of GCM tag)
        result = aes_decrypt(bytes(tampered), "pw")
        assert result is None

    def test_aes_too_short_data(self):
        """Test that truncated data returns None."""
        assert HAS_CRYPTOGRAPHY
        result = aes_decrypt(b"\x01" + b"\x00" * 10, "pw")
        assert result is None

    def test_aes_binary_data(self):
        """Test AES encryption of binary data."""
        assert HAS_CRYPTOGRAPHY
        data = bytes(range(256)) * 10
        password = "binary_key"
        encrypted = aes_encrypt(data, password)
        decrypted = aes_decrypt(encrypted, password)
        assert decrypted == data

    def test_aes_empty_data(self):
        """Test AES encryption of empty data."""
        assert HAS_CRYPTOGRAPHY
        encrypted = aes_encrypt(b"", "pw")
        decrypted = aes_decrypt(encrypted, "pw")
        assert decrypted == b""


class TestUnifiedEncryptDecrypt:
    """Tests for the unified encrypt/decrypt interface."""

    def test_encrypt_uses_aes_when_available(self):
        """Test that encrypt() uses AES when cryptography is installed."""
        assert HAS_CRYPTOGRAPHY
        data = b"test data"
        encrypted = encrypt(data, "pw")
        # Should have AES version marker
        assert encrypted[0] == 0x01

    def test_decrypt_auto_detects_aes(self):
        """Test that decrypt() auto-detects AES format."""
        assert HAS_CRYPTOGRAPHY
        data = b"test data"
        encrypted = encrypt(data, "pw")
        decrypted = decrypt(encrypted, "pw")
        assert decrypted == data

    def test_decrypt_handles_xor_data(self):
        """Test that decrypt() falls back to XOR for non-AES data."""
        data = b"test data"
        password = "key"
        xor_encrypted = xor_encrypt(data, password)
        decrypted = decrypt(xor_encrypted, password)
        assert decrypted == data

    def test_roundtrip_large_payload(self):
        """Test encrypt/decrypt with a larger payload."""
        assert HAS_CRYPTOGRAPHY
        data = b"A" * 1_000_000  # 1 MB
        encrypted = encrypt(data, "password")
        decrypted = decrypt(encrypted, "password")
        assert decrypted == data
