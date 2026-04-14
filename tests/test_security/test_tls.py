"""Tests for TLS certificate utilities."""

import subprocess

import pytest

from src.security.tls import (
    check_cert_needs_renewal,
    check_certbot_available,
    check_openssl_available,
    generate_self_signed_cert,
    get_cert_info,
)

# Skip all tests that require openssl if it's not available
HAS_OPENSSL = check_openssl_available()
needs_openssl = pytest.mark.skipif(not HAS_OPENSSL, reason="openssl not available")


class TestCheckOpenssl:
    def test_returns_bool(self):
        result = check_openssl_available()
        assert isinstance(result, bool)

    @needs_openssl
    def test_openssl_available_on_this_system(self):
        assert check_openssl_available() is True


class TestCheckCertbot:
    def test_returns_bool(self):
        result = check_certbot_available()
        assert isinstance(result, bool)


@needs_openssl
class TestGenerateSelfSignedCert:
    def test_generates_cert_and_key_files(self, tmp_path):
        cert_path = tmp_path / "cert.pem"
        key_path = tmp_path / "key.pem"

        result_cert, result_key = generate_self_signed_cert(
            cert_path=cert_path,
            key_path=key_path,
        )

        assert result_cert == cert_path
        assert result_key == key_path
        assert cert_path.exists()
        assert key_path.exists()
        assert cert_path.stat().st_size > 0
        assert key_path.stat().st_size > 0

    def test_generates_temp_files_when_no_path(self):
        cert_path, key_path = generate_self_signed_cert()
        try:
            assert cert_path.exists()
            assert key_path.exists()
            # PEM files should start with -----BEGIN
            assert cert_path.read_text().startswith("-----BEGIN")
            assert key_path.read_text().startswith("-----BEGIN")
        finally:
            cert_path.unlink(missing_ok=True)
            key_path.unlink(missing_ok=True)

    def test_custom_common_name(self, tmp_path):
        cert_path, key_path = generate_self_signed_cert(
            cert_path=tmp_path / "cert.pem",
            key_path=tmp_path / "key.pem",
            common_name="myhost.local",
        )
        # Verify CN via openssl
        result = subprocess.run(
            ["openssl", "x509", "-in", str(cert_path), "-noout", "-subject"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert "myhost.local" in result.stdout

    def test_custom_validity_days(self, tmp_path):
        cert_path, key_path = generate_self_signed_cert(
            cert_path=tmp_path / "cert.pem",
            key_path=tmp_path / "key.pem",
            days=7,
        )
        assert cert_path.exists()

    def test_cert_is_x509(self, tmp_path):
        cert_path, key_path = generate_self_signed_cert(
            cert_path=tmp_path / "cert.pem",
            key_path=tmp_path / "key.pem",
        )
        result = subprocess.run(
            ["openssl", "x509", "-in", str(cert_path), "-noout", "-text"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "Issuer:" in result.stdout


@needs_openssl
class TestCheckCertNeedsRenewal:
    def test_nonexistent_cert_needs_renewal(self, tmp_path):
        assert check_cert_needs_renewal(tmp_path / "nope.pem") is True

    def test_fresh_cert_does_not_need_renewal(self, tmp_path):
        cert_path, key_path = generate_self_signed_cert(
            cert_path=tmp_path / "cert.pem",
            key_path=tmp_path / "key.pem",
            days=365,
        )
        # A 365-day cert should not need renewal within 30 days
        assert check_cert_needs_renewal(cert_path, days=30) is False

    def test_short_lived_cert_needs_renewal(self, tmp_path):
        cert_path, key_path = generate_self_signed_cert(
            cert_path=tmp_path / "cert.pem",
            key_path=tmp_path / "key.pem",
            days=1,
        )
        # A 1-day cert needs renewal if we check with 30-day window
        assert check_cert_needs_renewal(cert_path, days=30) is True


@needs_openssl
class TestGetCertInfo:
    def test_returns_dict_with_subject(self, tmp_path):
        cert_path, _ = generate_self_signed_cert(
            cert_path=tmp_path / "cert.pem",
            key_path=tmp_path / "key.pem",
            common_name="test.local",
        )
        info = get_cert_info(cert_path)
        assert isinstance(info, dict)
        assert "error" not in info
        # Should have date fields
        assert any("Not" in k or "subject" in k.lower() for k in info)

    def test_nonexistent_cert_returns_error(self, tmp_path):
        info = get_cert_info(tmp_path / "nope.pem")
        assert "error" in info
