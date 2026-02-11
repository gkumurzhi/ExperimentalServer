"""
Модуль безопасности - аутентификация, шифрование, TLS.
"""

from .auth import (
    BasicAuthenticator,
    parse_basic_auth,
    hash_password,
    verify_password,
    generate_random_credentials,
)
from .crypto import (
    xor_encrypt,
    xor_decrypt,
    xor_encrypt_file,
    xor_decrypt_file,
    compute_hmac,
    verify_hmac,
    xor_encrypt_with_hmac,
    xor_decrypt_with_hmac,
)
from .tls import (
    generate_self_signed_cert,
    generate_cert_in_memory,
    check_openssl_available,
    get_cert_info,
)

__all__ = [
    # Auth
    "BasicAuthenticator",
    "parse_basic_auth",
    "hash_password",
    "verify_password",
    "generate_random_credentials",
    # Crypto
    "xor_encrypt",
    "xor_decrypt",
    "xor_encrypt_file",
    "xor_decrypt_file",
    "compute_hmac",
    "verify_hmac",
    "xor_encrypt_with_hmac",
    "xor_decrypt_with_hmac",
    # TLS
    "generate_self_signed_cert",
    "generate_cert_in_memory",
    "check_openssl_available",
    "get_cert_info",
]
