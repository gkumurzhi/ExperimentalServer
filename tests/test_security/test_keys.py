"""Tests for the ECDH key exchange manager."""

import pytest

from src.security.keys import HAS_ECDH, ECDHKeyManager

pytestmark = pytest.mark.skipif(not HAS_ECDH, reason="cryptography not installed")


class TestECDHKeyManager:
    def test_public_key_is_65_bytes(self):
        mgr = ECDHKeyManager()
        raw = mgr.get_public_key_raw()
        assert len(raw) == 65
        assert raw[0] == 0x04  # uncompressed point prefix

    def test_derive_session_returns_id_and_key(self):
        server = ECDHKeyManager()
        client = ECDHKeyManager()

        client_pub = client.get_public_key_raw()
        session_id, key = server.derive_session(client_pub)

        assert len(session_id) == 32  # hex(16 bytes)
        assert len(key) == 32  # 256-bit AES key

    def test_get_session_key_returns_key(self):
        mgr = ECDHKeyManager()
        client = ECDHKeyManager()
        session_id, key = mgr.derive_session(client.get_public_key_raw())

        assert mgr.get_session_key(session_id) == key

    def test_get_session_key_unknown_returns_none(self):
        mgr = ECDHKeyManager()
        assert mgr.get_session_key("nonexistent") is None

    def test_remove_session(self):
        mgr = ECDHKeyManager()
        client = ECDHKeyManager()
        session_id, _ = mgr.derive_session(client.get_public_key_raw())

        mgr.remove_session(session_id)
        assert mgr.get_session_key(session_id) is None

    def test_remove_nonexistent_session_is_noop(self):
        mgr = ECDHKeyManager()
        mgr.remove_session("doesnotexist")  # should not raise

    def test_encrypt_decrypt_roundtrip(self):
        mgr = ECDHKeyManager()
        client = ECDHKeyManager()
        session_id, _ = mgr.derive_session(client.get_public_key_raw())

        plaintext = b"Hello, encrypted notepad!"
        encrypted = mgr.encrypt(session_id, plaintext)

        # encrypted = nonce(12) + ciphertext + tag(16)
        assert len(encrypted) > 12 + 16
        assert encrypted != plaintext

        decrypted = mgr.decrypt(session_id, encrypted)
        assert decrypted == plaintext

    def test_encrypt_unknown_session_raises(self):
        mgr = ECDHKeyManager()
        with pytest.raises(ValueError, match="Unknown session"):
            mgr.encrypt("bad_session", b"data")

    def test_decrypt_unknown_session_raises(self):
        mgr = ECDHKeyManager()
        with pytest.raises(ValueError, match="Unknown session"):
            mgr.decrypt("bad_session", b"x" * 30)

    def test_decrypt_too_short_raises(self):
        mgr = ECDHKeyManager()
        client = ECDHKeyManager()
        session_id, _ = mgr.derive_session(client.get_public_key_raw())

        with pytest.raises(ValueError, match="Data too short"):
            mgr.decrypt(session_id, b"short")

    def test_decrypt_tampered_data_fails(self):
        mgr = ECDHKeyManager()
        client = ECDHKeyManager()
        session_id, _ = mgr.derive_session(client.get_public_key_raw())

        encrypted = mgr.encrypt(session_id, b"secret")
        # Tamper with a byte in the ciphertext
        tampered = bytearray(encrypted)
        tampered[-5] ^= 0xFF
        tampered = bytes(tampered)

        with pytest.raises((ValueError, Exception)):  # InvalidTag from cryptography
            mgr.decrypt(session_id, tampered)

    def test_multiple_sessions_independent(self):
        mgr = ECDHKeyManager()

        client1 = ECDHKeyManager()
        sid1, _ = mgr.derive_session(client1.get_public_key_raw())

        client2 = ECDHKeyManager()
        sid2, _ = mgr.derive_session(client2.get_public_key_raw())

        assert sid1 != sid2
        assert mgr.get_session_key(sid1) != mgr.get_session_key(sid2)

        # Each session encrypts independently
        enc1 = mgr.encrypt(sid1, b"msg1")
        enc2 = mgr.encrypt(sid2, b"msg2")

        assert mgr.decrypt(sid1, enc1) == b"msg1"
        assert mgr.decrypt(sid2, enc2) == b"msg2"

    def test_public_key_stable(self):
        """Same manager returns the same public key each time."""
        mgr = ECDHKeyManager()
        assert mgr.get_public_key_raw() == mgr.get_public_key_raw()

    def test_expired_sessions_cleaned_on_access(self):
        current_time = [1000.0]

        def fake_time() -> float:
            return current_time[0]

        mgr = ECDHKeyManager(session_ttl_seconds=10.0, time_fn=fake_time)
        client = ECDHKeyManager()
        session_id, _ = mgr.derive_session(client.get_public_key_raw())

        assert mgr.active_session_count() == 1

        current_time[0] += 11.0

        assert mgr.get_session_key(session_id) is None
        assert mgr.active_session_count() == 0

    def test_lru_session_cap_evicts_oldest_active_session(self):
        current_time = [2000.0]

        def fake_time() -> float:
            return current_time[0]

        mgr = ECDHKeyManager(max_sessions=2, time_fn=fake_time)
        client1 = ECDHKeyManager()
        sid1, _ = mgr.derive_session(client1.get_public_key_raw())

        current_time[0] += 1.0
        client2 = ECDHKeyManager()
        sid2, _ = mgr.derive_session(client2.get_public_key_raw())

        current_time[0] += 1.0
        assert mgr.get_session_key(sid1) is not None

        current_time[0] += 1.0
        client3 = ECDHKeyManager()
        sid3, _ = mgr.derive_session(client3.get_public_key_raw())

        assert mgr.active_session_count() == 2
        assert mgr.get_session_key(sid1) is not None
        assert mgr.get_session_key(sid2) is None
        assert mgr.get_session_key(sid3) is not None
