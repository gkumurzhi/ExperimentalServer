"""
Self-signed TLS certificate generation.

Uses only the Python standard library (no cryptography/pyOpenSSL).
Generates certificates via subprocess calls to openssl.
"""

import os
import subprocess
import tempfile
from pathlib import Path


def generate_self_signed_cert(
    cert_path: str | Path | None = None,
    key_path: str | Path | None = None,
    days: int = 365,
    common_name: str = "localhost",
    organization: str = "ExperimentalHTTPServer",
    key_size: int = 2048
) -> tuple[Path, Path]:
    """
    Generate a self-signed certificate using openssl.

    Args:
        cert_path: Path to save the certificate (None = temp file).
        key_path: Path to save the private key (None = temp file).
        days: Certificate validity in days.
        common_name: Common Name (CN) for the certificate.
        organization: Organization name.
        key_size: RSA key size in bits.

    Returns:
        Tuple (certificate path, key path).

    Raises:
        RuntimeError: If openssl is not found or generation fails.
    """
    # Determine paths
    if cert_path is None:
        cert_fd, cert_path = tempfile.mkstemp(suffix=".pem", prefix="cert_")
        os.close(cert_fd)
    if key_path is None:
        key_fd, key_path = tempfile.mkstemp(suffix=".pem", prefix="key_")
        os.close(key_fd)

    cert_path = Path(cert_path)
    key_path = Path(key_path)

    # Certificate subject
    subject = f"/CN={common_name}/O={organization}"

    # OpenSSL command
    cmd = [
        "openssl", "req",
        "-x509",
        "-newkey", f"rsa:{key_size}",
        "-keyout", str(key_path),
        "-out", str(cert_path),
        "-days", str(days),
        "-nodes",  # No passphrase on key
        "-subj", subject,
        "-addext", f"subjectAltName=DNS:{common_name},DNS:localhost,IP:127.0.0.1"
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            # Retry without -addext (older openssl versions)
            cmd_fallback = [
                "openssl", "req",
                "-x509",
                "-newkey", f"rsa:{key_size}",
                "-keyout", str(key_path),
                "-out", str(cert_path),
                "-days", str(days),
                "-nodes",
                "-subj", subject
            ]
            result = subprocess.run(
                cmd_fallback,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                raise RuntimeError(f"OpenSSL error: {result.stderr}")

    except FileNotFoundError as err:
        raise RuntimeError(
            "OpenSSL not found. Install OpenSSL or provide cert/key files manually.\n"
            "Windows: https://slproweb.com/products/Win32OpenSSL.html\n"
            "Linux: apt install openssl / yum install openssl\n"
            "macOS: brew install openssl"
        ) from err
    except subprocess.TimeoutExpired as err:
        raise RuntimeError("OpenSSL command timed out") from err

    return cert_path, key_path


def generate_cert_in_memory() -> tuple[str, str]:
    """
    Generate a certificate using temporary files.

    Returns:
        Tuple (certificate path, key path).
    """
    cert_path, key_path = generate_self_signed_cert()
    return str(cert_path), str(key_path)


def check_openssl_available() -> bool:
    """Check if OpenSSL is available."""
    try:
        result = subprocess.run(
            ["openssl", "version"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def check_certbot_available() -> bool:
    """Check if certbot is available."""
    try:
        result = subprocess.run(
            ["certbot", "--version"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def check_cert_needs_renewal(cert_path: str | Path, days: int = 30) -> bool:
    """
    Check if a certificate needs renewal.

    Args:
        cert_path: Path to the certificate.
        days: Renew if expiring within this many days.

    Returns:
        True if the certificate does not exist or expires within *days* days.
    """
    cert_path = Path(cert_path)
    if not cert_path.exists():
        return True

    seconds = days * 86400
    try:
        result = subprocess.run(
            ["openssl", "x509", "-in", str(cert_path), "-checkend", str(seconds)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        # returncode 0 = certificate is valid for >= days more days
        # returncode 1 = certificate expires within days days
        return result.returncode != 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return True


def obtain_letsencrypt_cert(
    domain: str,
    email: str | None = None,
    config_dir: str | Path | None = None,
) -> tuple[Path, Path]:
    """
    Obtain a Let's Encrypt certificate via certbot standalone.

    Args:
        domain: Domain for the certificate.
        email: Notification email (None = no email).
        config_dir: Directory for storing certificates.

    Returns:
        Tuple (path to fullchain.pem, path to privkey.pem).

    Raises:
        RuntimeError: If certbot is not found or an error occurs.
    """
    if config_dir is None:
        config_dir = Path.home() / ".exphttp" / "letsencrypt"
    config_dir = Path(config_dir)

    work_dir = config_dir / "work"
    logs_dir = config_dir / "logs"

    # Create directories
    for d in (config_dir, work_dir, logs_dir):
        d.mkdir(parents=True, exist_ok=True)

    cmd = [
        "certbot", "certonly", "--standalone",
        "-d", domain,
        "--config-dir", str(config_dir),
        "--work-dir", str(work_dir),
        "--logs-dir", str(logs_dir),
        "--non-interactive",
        "--agree-tos",
    ]

    if email:
        cmd.extend(["--email", email])
    else:
        cmd.append("--register-unsafely-without-email")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"certbot error (code {result.returncode}):\n{result.stderr}"
            )

    except FileNotFoundError as err:
        raise RuntimeError(
            "certbot not found. Install certbot: https://certbot.eff.org/"
        ) from err
    except subprocess.TimeoutExpired as err:
        raise RuntimeError("certbot command timed out (120s)") from err

    cert_path = config_dir / "live" / domain / "fullchain.pem"
    key_path = config_dir / "live" / domain / "privkey.pem"

    if not cert_path.exists() or not key_path.exists():
        raise RuntimeError(
            f"certbot succeeded but certificate files not found:\n"
            f"  cert: {cert_path}\n  key: {key_path}"
        )

    return cert_path, key_path


def get_cert_info(cert_path: str | Path) -> dict[str, str]:
    """
    Get certificate information.

    Args:
        cert_path: Path to the certificate.

    Returns:
        Dict with certificate information.
    """
    try:
        result = subprocess.run(
            ["openssl", "x509", "-in", str(cert_path), "-noout", "-subject", "-dates"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            return {"error": result.stderr}

        info = {}
        for line in result.stdout.strip().split("\n"):
            if "=" in line:
                key, value = line.split("=", 1)
                info[key.strip()] = value.strip()

        return info

    except Exception as e:
        return {"error": str(e)}
