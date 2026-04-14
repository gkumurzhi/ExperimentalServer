"""Tests for src.security.tls_manager.TLSManager."""

from __future__ import annotations

import ssl
from pathlib import Path

import pytest

from src.security.tls_manager import TLSManager


class TestTLSManagerDisabled:
    def test_disabled_setup_is_noop(self) -> None:
        m = TLSManager(
            enabled=False,
            cert_file=None,
            key_file=None,
            letsencrypt=False,
            domain=None,
            email=None,
            host="127.0.0.1",
        )
        m.setup()

        assert m.ssl_context is None
        assert m.enabled is False

    def test_describe_unknown_when_no_cert(self) -> None:
        m = TLSManager(
            enabled=False,
            cert_file=None,
            key_file=None,
            letsencrypt=False,
            domain=None,
            email=None,
            host="127.0.0.1",
        )
        assert m.describe() == "unknown"


class TestTLSManagerSelfSigned:
    def test_self_signed_generated_on_setup(self, tmp_path: Path) -> None:
        m = TLSManager(
            enabled=True,
            cert_file=None,
            key_file=None,
            letsencrypt=False,
            domain=None,
            email=None,
            host="127.0.0.1",
        )

        m.setup()
        try:
            # Either OpenSSL is available and we got a context, or TLS was
            # disabled due to missing openssl. Both are valid outcomes.
            if m.enabled:
                assert isinstance(m.ssl_context, ssl.SSLContext)
                assert m.ssl_context.minimum_version == ssl.TLSVersion.TLSv1_2
                assert m.cert_file and Path(m.cert_file).exists()
                assert m.describe() == "self-signed"
                # Temporary cert tracked for cleanup
                assert m.temp_cert_files
            else:
                # OpenSSL missing — cert files should not exist
                assert m.ssl_context is None
        finally:
            m.cleanup()
            # After cleanup, temp files should be removed
            for path in m.temp_cert_files:
                assert not Path(path).exists()
            assert not m.temp_cert_files


class TestTLSManagerWithProvidedCert:
    def test_uses_provided_cert_without_generating(self, tmp_path: Path) -> None:
        # Generate a throwaway self-signed cert to point TLSManager at.
        # Skip if OpenSSL is unavailable.
        from src.security.tls import check_openssl_available, generate_self_signed_cert

        if not check_openssl_available():
            pytest.skip("OpenSSL not available")

        cert, key = generate_self_signed_cert(common_name="localhost")
        try:
            m = TLSManager(
                enabled=True,
                cert_file=str(cert),
                key_file=str(key),
                letsencrypt=False,
                domain=None,
                email=None,
                host="localhost",
            )
            m.setup()

            assert m.enabled
            assert isinstance(m.ssl_context, ssl.SSLContext)
            assert m.describe() == str(cert)
            # User-supplied cert is not marked for cleanup
            assert m.temp_cert_files == []
        finally:
            cert.unlink(missing_ok=True)
            key.unlink(missing_ok=True)


class TestTLSManagerDescribe:
    def test_letsencrypt_description(self) -> None:
        m = TLSManager(
            enabled=True,
            cert_file="/tmp/fake.pem",
            key_file="/tmp/fake.key",
            letsencrypt=True,
            domain="example.com",
            email=None,
            host="example.com",
        )
        assert m.describe() == "Let's Encrypt (example.com)"
