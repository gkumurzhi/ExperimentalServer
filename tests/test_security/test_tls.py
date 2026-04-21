"""Tests for TLS certificate utilities."""

from __future__ import annotations

import subprocess

import pytest

from src.security.tls import (
    check_cert_needs_renewal,
    check_certbot_available,
    check_openssl_available,
    generate_cert_in_memory,
    generate_self_signed_cert,
    get_cert_info,
    obtain_letsencrypt_cert,
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

    def test_returns_false_when_openssl_missing(self, monkeypatch):
        def fake_run(*_args, **_kwargs):
            raise FileNotFoundError

        monkeypatch.setattr("src.security.tls.subprocess.run", fake_run)

        assert check_openssl_available() is False

    def test_returns_false_when_openssl_check_times_out(self, monkeypatch):
        def fake_run(*_args, **_kwargs):
            raise subprocess.TimeoutExpired(cmd="openssl version", timeout=5)

        monkeypatch.setattr("src.security.tls.subprocess.run", fake_run)

        assert check_openssl_available() is False


class TestCheckCertbot:
    def test_returns_bool(self):
        result = check_certbot_available()
        assert isinstance(result, bool)

    def test_returns_false_when_certbot_returns_nonzero(self, monkeypatch):
        monkeypatch.setattr(
            "src.security.tls.subprocess.run",
            lambda cmd, **_kwargs: subprocess.CompletedProcess(cmd, 1, stdout="", stderr="boom"),
        )

        assert check_certbot_available() is False

    def test_returns_false_when_certbot_missing(self, monkeypatch):
        def fake_run(*_args, **_kwargs):
            raise FileNotFoundError

        monkeypatch.setattr("src.security.tls.subprocess.run", fake_run)

        assert check_certbot_available() is False

    def test_returns_false_when_certbot_check_times_out(self, monkeypatch):
        def fake_run(*_args, **_kwargs):
            raise subprocess.TimeoutExpired(cmd="certbot --version", timeout=5)

        monkeypatch.setattr("src.security.tls.subprocess.run", fake_run)

        assert check_certbot_available() is False


class TestGenerateCertInMemory:
    def test_returns_string_paths(self, monkeypatch, tmp_path):
        cert_path = tmp_path / "cert.pem"
        key_path = tmp_path / "key.pem"
        monkeypatch.setattr(
            "src.security.tls.generate_self_signed_cert",
            lambda: (cert_path, key_path),
        )

        cert_result, key_result = generate_cert_in_memory()

        assert cert_result == str(cert_path)
        assert key_result == str(key_path)


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

    def test_retries_without_addext_when_initial_command_fails(self, tmp_path, monkeypatch):
        calls: list[list[str]] = []

        def fake_run(cmd, **_kwargs):
            calls.append(cmd)
            if len(calls) == 1:
                return subprocess.CompletedProcess(cmd, 1, stderr="unknown option -addext")
            return subprocess.CompletedProcess(cmd, 0, stderr="")

        monkeypatch.setattr("src.security.tls.subprocess.run", fake_run)

        cert_path, key_path = generate_self_signed_cert(
            cert_path=tmp_path / "cert.pem",
            key_path=tmp_path / "key.pem",
        )

        assert cert_path == tmp_path / "cert.pem"
        assert key_path == tmp_path / "key.pem"
        assert len(calls) == 2
        assert "-addext" in calls[0]
        assert "-addext" not in calls[1]

    def test_timeout_raises_runtime_error(self, tmp_path, monkeypatch):
        def fake_run(*_args, **_kwargs):
            raise subprocess.TimeoutExpired(cmd="openssl", timeout=30)

        monkeypatch.setattr("src.security.tls.subprocess.run", fake_run)

        with pytest.raises(RuntimeError, match="timed out"):
            generate_self_signed_cert(
                cert_path=tmp_path / "cert.pem",
                key_path=tmp_path / "key.pem",
            )

    def test_missing_openssl_raises_runtime_error(self, tmp_path, monkeypatch):
        def fake_run(*_args, **_kwargs):
            raise FileNotFoundError

        monkeypatch.setattr("src.security.tls.subprocess.run", fake_run)

        with pytest.raises(RuntimeError, match="OpenSSL not found"):
            generate_self_signed_cert(
                cert_path=tmp_path / "cert.pem",
                key_path=tmp_path / "key.pem",
            )

    def test_raises_runtime_error_when_fallback_also_fails(self, tmp_path, monkeypatch):
        calls: list[list[str]] = []

        def fake_run(cmd, **_kwargs):
            calls.append(cmd)
            return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="still broken")

        monkeypatch.setattr("src.security.tls.subprocess.run", fake_run)

        with pytest.raises(RuntimeError, match="still broken"):
            generate_self_signed_cert(
                cert_path=tmp_path / "cert.pem",
                key_path=tmp_path / "key.pem",
            )

        assert len(calls) == 2
        assert "-addext" in calls[0]
        assert "-addext" not in calls[1]


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

    def test_missing_openssl_treats_cert_as_needing_renewal(self, tmp_path, monkeypatch):
        cert_path = tmp_path / "cert.pem"
        cert_path.write_text("cert", encoding="utf-8")

        def fake_run(*_args, **_kwargs):
            raise FileNotFoundError

        monkeypatch.setattr("src.security.tls.subprocess.run", fake_run)

        assert check_cert_needs_renewal(cert_path, days=30) is True

    def test_timeout_treats_cert_as_needing_renewal(self, tmp_path, monkeypatch):
        cert_path = tmp_path / "cert.pem"
        cert_path.write_text("cert", encoding="utf-8")

        def fake_run(*_args, **_kwargs):
            raise subprocess.TimeoutExpired(cmd="openssl x509", timeout=10)

        monkeypatch.setattr("src.security.tls.subprocess.run", fake_run)

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

    def test_ignores_non_key_value_lines(self, tmp_path, monkeypatch):
        cert_path = tmp_path / "cert.pem"
        cert_path.write_text("cert", encoding="utf-8")

        monkeypatch.setattr(
            "src.security.tls.subprocess.run",
            lambda cmd, **_kwargs: subprocess.CompletedProcess(
                cmd,
                0,
                stdout="subject=CN = demo\nnotBefore=now\nnotAfter=later\nnoise-without-equals\n",
                stderr="",
            ),
        )

        info = get_cert_info(cert_path)

        assert info == {
            "subject": "CN = demo",
            "notBefore": "now",
            "notAfter": "later",
        }

    def test_returns_error_when_openssl_call_raises(self, tmp_path, monkeypatch):
        cert_path = tmp_path / "cert.pem"
        cert_path.write_text("cert", encoding="utf-8")

        def fake_run(*_args, **_kwargs):
            raise OSError("boom")

        monkeypatch.setattr("src.security.tls.subprocess.run", fake_run)

        info = get_cert_info(cert_path)

        assert info == {"error": "boom"}


class TestObtainLetsEncryptCert:
    def test_uses_default_config_dir_when_not_provided(self, tmp_path, monkeypatch):
        fake_home = tmp_path / "home"
        config_dir = fake_home / ".exphttp" / "letsencrypt"
        live_dir = config_dir / "live" / "example.com"
        cert_path = live_dir / "fullchain.pem"
        key_path = live_dir / "privkey.pem"

        monkeypatch.setattr("src.security.tls.Path.home", lambda: fake_home)

        def fake_run(cmd, **_kwargs):
            live_dir.mkdir(parents=True, exist_ok=True)
            cert_path.write_text("cert", encoding="utf-8")
            key_path.write_text("key", encoding="utf-8")
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

        monkeypatch.setattr("src.security.tls.subprocess.run", fake_run)

        result_cert, result_key = obtain_letsencrypt_cert(domain="example.com")

        assert result_cert == cert_path
        assert result_key == key_path

    def test_returns_generated_live_paths(self, tmp_path, monkeypatch):
        config_dir = tmp_path / "letsencrypt"
        live_dir = config_dir / "live" / "example.com"
        cert_path = live_dir / "fullchain.pem"
        key_path = live_dir / "privkey.pem"

        def fake_run(cmd, **_kwargs):
            live_dir.mkdir(parents=True, exist_ok=True)
            cert_path.write_text("cert", encoding="utf-8")
            key_path.write_text("key", encoding="utf-8")
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

        monkeypatch.setattr("src.security.tls.subprocess.run", fake_run)

        result_cert, result_key = obtain_letsencrypt_cert(
            domain="example.com",
            email="ops@example.com",
            config_dir=config_dir,
        )

        assert result_cert == cert_path
        assert result_key == key_path
        assert (config_dir / "work").exists()
        assert (config_dir / "logs").exists()

    def test_missing_output_files_raise_runtime_error(self, tmp_path, monkeypatch):
        def fake_run(cmd, **_kwargs):
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

        monkeypatch.setattr("src.security.tls.subprocess.run", fake_run)

        with pytest.raises(RuntimeError, match="certificate files not found"):
            obtain_letsencrypt_cert(domain="example.com", config_dir=tmp_path)

    def test_nonzero_certbot_exit_raises_runtime_error(self, tmp_path, monkeypatch):
        def fake_run(cmd, **_kwargs):
            return subprocess.CompletedProcess(cmd, 2, stdout="", stderr="certbot failed")

        monkeypatch.setattr("src.security.tls.subprocess.run", fake_run)

        with pytest.raises(RuntimeError, match="certbot error \\(code 2\\)"):
            obtain_letsencrypt_cert(domain="example.com", config_dir=tmp_path)

    def test_missing_certbot_raises_runtime_error(self, tmp_path, monkeypatch):
        def fake_run(*_args, **_kwargs):
            raise FileNotFoundError

        monkeypatch.setattr("src.security.tls.subprocess.run", fake_run)

        with pytest.raises(RuntimeError, match="certbot not found"):
            obtain_letsencrypt_cert(domain="example.com", config_dir=tmp_path)

    def test_timeout_raises_runtime_error(self, tmp_path, monkeypatch):
        def fake_run(*_args, **_kwargs):
            raise subprocess.TimeoutExpired(cmd="certbot", timeout=120)

        monkeypatch.setattr("src.security.tls.subprocess.run", fake_run)

        with pytest.raises(RuntimeError, match="certbot command timed out"):
            obtain_letsencrypt_cert(domain="example.com", config_dir=tmp_path)
