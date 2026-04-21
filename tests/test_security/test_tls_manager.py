"""Tests for src.security.tls_manager.TLSManager."""

from __future__ import annotations

import ssl
from pathlib import Path
from unittest.mock import Mock

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


class TestTLSManagerControlFlow:
    def test_generate_self_signed_disables_tls_when_openssl_missing(self, monkeypatch) -> None:
        m = TLSManager(
            enabled=True,
            cert_file=None,
            key_file=None,
            letsencrypt=False,
            domain=None,
            email=None,
            host="127.0.0.1",
        )

        monkeypatch.setattr("src.security.tls_manager.check_openssl_available", lambda: False)

        assert m._generate_self_signed() is False
        assert m.enabled is False
        assert m.cert_file is None
        assert m.key_file is None

    def test_try_letsencrypt_uses_existing_certificate(self, tmp_path: Path, monkeypatch) -> None:
        config_dir = tmp_path / ".exphttp" / "letsencrypt"
        live_dir = config_dir / "live" / "example.com"
        cert_path = live_dir / "fullchain.pem"
        key_path = live_dir / "privkey.pem"
        live_dir.mkdir(parents=True)
        cert_path.write_text("cert", encoding="utf-8")
        key_path.write_text("key", encoding="utf-8")

        obtain_mock = Mock()
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.setattr("src.security.tls_manager.check_certbot_available", lambda: True)
        monkeypatch.setattr(
            "src.security.tls_manager.check_cert_needs_renewal",
            lambda _path: False,
        )
        monkeypatch.setattr("src.security.tls_manager.obtain_letsencrypt_cert", obtain_mock)

        m = TLSManager(
            enabled=True,
            cert_file=None,
            key_file=None,
            letsencrypt=True,
            domain="example.com",
            email="ops@example.com",
            host="example.com",
        )

        m._try_letsencrypt()

        assert m.cert_file == str(cert_path)
        assert m.key_file == str(key_path)
        obtain_mock.assert_not_called()

    def test_try_letsencrypt_obtains_when_certificate_needs_renewal(
        self,
        tmp_path: Path,
        monkeypatch,
    ) -> None:
        config_dir = tmp_path / ".exphttp" / "letsencrypt"
        obtained_cert = config_dir / "live" / "example.com" / "fullchain.pem"
        obtained_key = config_dir / "live" / "example.com" / "privkey.pem"

        def fake_obtain(**_kwargs):
            obtained_cert.parent.mkdir(parents=True, exist_ok=True)
            obtained_cert.write_text("cert", encoding="utf-8")
            obtained_key.write_text("key", encoding="utf-8")
            return obtained_cert, obtained_key

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.setattr("src.security.tls_manager.check_certbot_available", lambda: True)
        monkeypatch.setattr("src.security.tls_manager.check_cert_needs_renewal", lambda _path: True)
        monkeypatch.setattr("src.security.tls_manager.obtain_letsencrypt_cert", fake_obtain)

        m = TLSManager(
            enabled=True,
            cert_file=None,
            key_file=None,
            letsencrypt=True,
            domain="example.com",
            email="ops@example.com",
            host="example.com",
        )

        m._try_letsencrypt()

        assert m.cert_file == str(obtained_cert)
        assert m.key_file == str(obtained_key)

    def test_setup_falls_back_from_missing_certbot_to_self_signed(
        self,
        tmp_path: Path,
        monkeypatch,
    ) -> None:
        cert_path = tmp_path / "cert.pem"
        key_path = tmp_path / "key.pem"
        cert_path.write_text("cert", encoding="utf-8")
        key_path.write_text("key", encoding="utf-8")

        monkeypatch.setattr("src.security.tls_manager.check_certbot_available", lambda: False)
        monkeypatch.setattr("src.security.tls_manager.check_openssl_available", lambda: True)
        monkeypatch.setattr(
            "src.security.tls_manager.generate_self_signed_cert",
            lambda **_kwargs: (cert_path, key_path),
        )

        m = TLSManager(
            enabled=True,
            cert_file=None,
            key_file=None,
            letsencrypt=True,
            domain="example.com",
            email=None,
            host="127.0.0.1",
        )

        def fake_build_context() -> None:
            m.ssl_context = "built"  # type: ignore[assignment]

        monkeypatch.setattr(m, "_build_context", fake_build_context)

        m.setup()

        assert m.enabled is True
        assert m.cert_file == str(cert_path)
        assert m.key_file == str(key_path)
        assert m.describe() == "Let's Encrypt (example.com)"
        assert m.ssl_context == "built"

    def test_setup_returns_without_context_when_self_signed_generation_fails(
        self,
        monkeypatch,
    ) -> None:
        m = TLSManager(
            enabled=True,
            cert_file=None,
            key_file=None,
            letsencrypt=True,
            domain=None,
            email=None,
            host="127.0.0.1",
        )

        monkeypatch.setattr(m, "_generate_self_signed", lambda: False)

        build_mock = Mock()
        monkeypatch.setattr(m, "_build_context", build_mock)

        m.setup()

        assert m.ssl_context is None
        build_mock.assert_not_called()

    def test_cleanup_ignores_unlink_errors_and_clears_list(self, monkeypatch) -> None:
        m = TLSManager(
            enabled=True,
            cert_file=None,
            key_file=None,
            letsencrypt=False,
            domain=None,
            email=None,
            host="127.0.0.1",
        )
        m.temp_cert_files = ["/tmp/cert.pem", "/tmp/key.pem"]

        def fake_unlink(self) -> None:
            raise OSError("locked")

        monkeypatch.setattr(Path, "unlink", fake_unlink)

        m.cleanup()

        assert m.temp_cert_files == []
