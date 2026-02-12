"""
Security module — authentication, encryption, TLS.
"""

from .auth import (
    BasicAuthenticator,
    generate_random_credentials,
    hash_password,
    parse_basic_auth,
    verify_password,
)
from .crypto import (
    HAS_CRYPTOGRAPHY,
    aes_decrypt,
    aes_encrypt,
    compute_hmac,
    decrypt,
    encrypt,
    verify_hmac,
    xor_bytes,
    xor_decrypt,
    xor_decrypt_file,
    xor_decrypt_with_hmac,
    xor_encrypt,
    xor_encrypt_file,
    xor_encrypt_with_hmac,
    xor_file,
)
from .tls import (
    check_openssl_available,
    generate_cert_in_memory,
    generate_self_signed_cert,
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
    "HAS_CRYPTOGRAPHY",
    "aes_encrypt",
    "aes_decrypt",
    "encrypt",
    "decrypt",
    "xor_bytes",
    "xor_file",
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
