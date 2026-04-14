"""TLS context lifecycle management.

Encapsulates certificate acquisition (Let's Encrypt, self-signed, user-supplied),
SSL context creation with modern defaults, and cleanup of temporary files.
"""

from __future__ import annotations

import atexit
import logging
import ssl
from pathlib import Path

from .tls import (
    check_cert_needs_renewal,
    check_certbot_available,
    check_openssl_available,
    generate_self_signed_cert,
    obtain_letsencrypt_cert,
)

logger = logging.getLogger("httpserver")


class TLSManager:
    """Owns the SSL context and the temporary files backing it."""

    def __init__(
        self,
        *,
        enabled: bool,
        cert_file: str | None,
        key_file: str | None,
        letsencrypt: bool,
        domain: str | None,
        email: str | None,
        host: str,
    ) -> None:
        self.enabled = enabled
        self.cert_file = cert_file
        self.key_file = key_file
        self.letsencrypt = letsencrypt
        self.domain = domain
        self.email = email
        self.host = host
        self.ssl_context: ssl.SSLContext | None = None
        self.temp_cert_files: list[str] = []
        self._used_self_signed = False

    def setup(self) -> None:
        """Acquire a certificate and build the SSL context.

        On failure to locate tooling, disables TLS and logs a warning instead
        of raising — callers check `self.enabled` afterwards.
        """
        if not self.enabled:
            return

        if self.letsencrypt and self.domain:
            self._try_letsencrypt()

        if not self.cert_file or not self.key_file:
            if not self._generate_self_signed():
                return

        self._build_context()

    def _try_letsencrypt(self) -> None:
        if not check_certbot_available():
            print("[WARNING] certbot not found. Falling back to self-signed certificate.")
            print("  Install certbot: https://certbot.eff.org/")
            return

        assert self.domain is not None
        config_dir = Path.home() / ".exphttp" / "letsencrypt"
        cert_path = config_dir / "live" / self.domain / "fullchain.pem"
        key_path = config_dir / "live" / self.domain / "privkey.pem"

        if not cert_path.exists() or check_cert_needs_renewal(cert_path):
            print(f"[TLS] Obtaining Let's Encrypt certificate for {self.domain}...")
            cert_path, key_path = obtain_letsencrypt_cert(
                domain=self.domain,
                email=self.email,
                config_dir=config_dir,
            )
            print(f"[TLS] Certificate obtained: {cert_path}")
        else:
            print(f"[TLS] Using existing Let's Encrypt certificate for {self.domain}")

        self.cert_file = str(cert_path)
        self.key_file = str(key_path)

    def _generate_self_signed(self) -> bool:
        if not check_openssl_available():
            print("[WARNING] OpenSSL not found. TLS disabled.")
            print("  Install OpenSSL or provide --cert and --key files.")
            self.enabled = False
            return False

        print("[TLS] Generating self-signed certificate...")
        common_name = self.host if self.host != "0.0.0.0" else "localhost"
        cert_path, key_path = generate_self_signed_cert(common_name=common_name)
        self.cert_file = str(cert_path)
        self.key_file = str(key_path)
        self.temp_cert_files = [self.cert_file, self.key_file]
        self._used_self_signed = True
        atexit.register(self.cleanup)
        return True

    def _build_context(self) -> None:
        assert self.cert_file is not None and self.key_file is not None
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(self.cert_file, self.key_file)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.set_ciphers("ECDHE+AESGCM:DHE+AESGCM:ECDHE+CHACHA20:DHE+CHACHA20")
        self.ssl_context = context

    def describe(self) -> str:
        """Short human-readable description of the active certificate."""
        if self.letsencrypt and self.domain:
            return f"Let's Encrypt ({self.domain})"
        if self._used_self_signed:
            return "self-signed"
        return self.cert_file or "unknown"

    def cleanup(self) -> None:
        """Remove any temporary cert/key files we created."""
        for path in self.temp_cert_files:
            try:
                Path(path).unlink()
            except OSError:
                pass
        self.temp_cert_files.clear()
