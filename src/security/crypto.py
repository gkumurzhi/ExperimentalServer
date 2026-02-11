"""
Криптографические функции для шифрования/расшифровки данных.
"""

import hmac
import hashlib


def xor_encrypt(data: bytes, password: str) -> bytes:
    """
    XOR шифрование данных.

    Args:
        data: Данные для шифрования
        password: Пароль (ключ)

    Returns:
        Зашифрованные данные
    """
    if not password:
        return data

    key_bytes = password.encode('utf-8')
    result = bytearray(len(data))

    for i in range(len(data)):
        result[i] = data[i] ^ key_bytes[i % len(key_bytes)]

    return bytes(result)


def xor_decrypt(data: bytes, password: str) -> bytes:
    """
    XOR расшифровка данных.

    XOR симметричен, поэтому расшифровка идентична шифрованию.

    Args:
        data: Зашифрованные данные
        password: Пароль (ключ)

    Returns:
        Расшифрованные данные
    """
    return xor_encrypt(data, password)


def xor_encrypt_file(input_path: str, output_path: str, password: str) -> int:
    """
    Шифрование файла с помощью XOR.

    Args:
        input_path: Путь к исходному файлу
        output_path: Путь для сохранения зашифрованного файла
        password: Пароль для шифрования

    Returns:
        Размер зашифрованного файла в байтах
    """
    with open(input_path, 'rb') as f:
        data = f.read()

    encrypted = xor_encrypt(data, password)

    with open(output_path, 'wb') as f:
        f.write(encrypted)

    return len(encrypted)


def xor_decrypt_file(input_path: str, output_path: str, password: str) -> int:
    """
    Расшифровка файла с помощью XOR.

    Args:
        input_path: Путь к зашифрованному файлу
        output_path: Путь для сохранения расшифрованного файла
        password: Пароль для расшифровки

    Returns:
        Размер расшифрованного файла в байтах
    """
    return xor_encrypt_file(input_path, output_path, password)


def compute_hmac(data: bytes, key: str) -> str:
    """
    Вычисление HMAC-SHA256 для проверки целостности данных.

    Args:
        data: Данные для подписи
        key: Ключ HMAC

    Returns:
        Hex-строка HMAC
    """
    return hmac.new(key.encode('utf-8'), data, hashlib.sha256).hexdigest()


def verify_hmac(data: bytes, key: str, expected_hmac: str) -> bool:
    """
    Проверка HMAC-SHA256.

    Args:
        data: Данные для проверки
        key: Ключ HMAC
        expected_hmac: Ожидаемый HMAC

    Returns:
        True если HMAC валидный
    """
    computed = compute_hmac(data, key)
    return hmac.compare_digest(computed, expected_hmac)


def xor_encrypt_with_hmac(data: bytes, password: str) -> tuple[bytes, str]:
    """
    XOR шифрование с HMAC для проверки целостности.

    Args:
        data: Данные для шифрования
        password: Пароль

    Returns:
        Кортеж (зашифрованные данные, HMAC)
    """
    encrypted = xor_encrypt(data, password)
    mac = compute_hmac(encrypted, password)
    return encrypted, mac


def xor_decrypt_with_hmac(data: bytes, password: str, mac: str) -> bytes | None:
    """
    XOR расшифровка с проверкой HMAC.

    Args:
        data: Зашифрованные данные
        password: Пароль
        mac: HMAC для проверки

    Returns:
        Расшифрованные данные или None если HMAC неверный
    """
    if not verify_hmac(data, password, mac):
        return None
    return xor_decrypt(data, password)
