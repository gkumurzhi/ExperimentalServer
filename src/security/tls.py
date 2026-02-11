"""
Генерация самоподписных TLS сертификатов.

Использует только стандартную библиотеку Python (без cryptography/pyOpenSSL).
Генерирует сертификаты с помощью subprocess вызова openssl.
"""

import subprocess
import tempfile
import os
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
    Генерация самоподписного сертификата с помощью openssl.

    Args:
        cert_path: Путь для сохранения сертификата (None = временный файл)
        key_path: Путь для сохранения приватного ключа (None = временный файл)
        days: Срок действия сертификата в днях
        common_name: Common Name (CN) для сертификата
        organization: Название организации
        key_size: Размер RSA ключа в битах

    Returns:
        Кортеж (путь к сертификату, путь к ключу)

    Raises:
        RuntimeError: Если openssl не найден или произошла ошибка генерации
    """
    # Определяем пути
    if cert_path is None:
        cert_fd, cert_path = tempfile.mkstemp(suffix=".pem", prefix="cert_")
        os.close(cert_fd)
    if key_path is None:
        key_fd, key_path = tempfile.mkstemp(suffix=".pem", prefix="key_")
        os.close(key_fd)

    cert_path = Path(cert_path)
    key_path = Path(key_path)

    # Subject для сертификата
    subject = f"/CN={common_name}/O={organization}"

    # Команда openssl
    cmd = [
        "openssl", "req",
        "-x509",
        "-newkey", f"rsa:{key_size}",
        "-keyout", str(key_path),
        "-out", str(cert_path),
        "-days", str(days),
        "-nodes",  # Без пароля на ключ
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
            # Пробуем без -addext (старые версии openssl)
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

    except FileNotFoundError:
        raise RuntimeError(
            "OpenSSL not found. Install OpenSSL or provide cert/key files manually.\n"
            "Windows: https://slproweb.com/products/Win32OpenSSL.html\n"
            "Linux: apt install openssl / yum install openssl\n"
            "macOS: brew install openssl"
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("OpenSSL command timed out")

    return cert_path, key_path


def generate_cert_in_memory() -> tuple[str, str]:
    """
    Генерация сертификата во временных файлах.

    Returns:
        Кортеж (путь к сертификату, путь к ключу)
    """
    cert_path, key_path = generate_self_signed_cert()
    return str(cert_path), str(key_path)


def check_openssl_available() -> bool:
    """Проверка доступности OpenSSL."""
    try:
        result = subprocess.run(
            ["openssl", "version"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def get_cert_info(cert_path: str | Path) -> dict:
    """
    Получение информации о сертификате.

    Args:
        cert_path: Путь к сертификату

    Returns:
        Словарь с информацией о сертификате
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
