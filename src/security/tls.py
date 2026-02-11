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


def check_certbot_available() -> bool:
    """Проверка доступности certbot."""
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
    Проверка, нужно ли обновлять сертификат.

    Args:
        cert_path: Путь к сертификату
        days: За сколько дней до истечения обновлять

    Returns:
        True если сертификат не существует или истечёт в течение days дней
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
        # returncode 0 = сертификат действителен ещё >= days дней
        # returncode 1 = сертификат истечёт в течение days дней
        return result.returncode != 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return True


def obtain_letsencrypt_cert(
    domain: str,
    email: str | None = None,
    config_dir: str | Path | None = None,
) -> tuple[Path, Path]:
    """
    Получение сертификата Let's Encrypt через certbot standalone.

    Args:
        domain: Домен для сертификата
        email: Email для уведомлений (None = без email)
        config_dir: Директория для хранения сертификатов

    Returns:
        Кортеж (путь к fullchain.pem, путь к privkey.pem)

    Raises:
        RuntimeError: Если certbot не найден или произошла ошибка
    """
    if config_dir is None:
        config_dir = Path.home() / ".exphttp" / "letsencrypt"
    config_dir = Path(config_dir)

    work_dir = config_dir / "work"
    logs_dir = config_dir / "logs"

    # Создаём директории
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

    except FileNotFoundError:
        raise RuntimeError(
            "certbot not found. Install certbot: https://certbot.eff.org/"
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("certbot command timed out (120s)")

    cert_path = config_dir / "live" / domain / "fullchain.pem"
    key_path = config_dir / "live" / domain / "privkey.pem"

    if not cert_path.exists() or not key_path.exists():
        raise RuntimeError(
            f"certbot succeeded but certificate files not found:\n"
            f"  cert: {cert_path}\n  key: {key_path}"
        )

    return cert_path, key_path


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
