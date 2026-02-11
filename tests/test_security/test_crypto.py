"""Tests for cryptographic functions."""

from pathlib import Path

import pytest

from src.security.crypto import (
    compute_hmac,
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
