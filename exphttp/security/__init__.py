"""Public security exports for exphttp."""

from importlib import import_module
from typing import TYPE_CHECKING, Any

from src.security import (
    HAS_CRYPTOGRAPHY,
    BasicAuthenticator,
    aes_decrypt,
    aes_encrypt,
    compute_hmac,
    decrypt,
    encrypt,
    generate_random_credentials,
    hash_password,
    parse_basic_auth,
    verify_hmac,
    verify_password,
    xor_bytes,
    xor_decrypt,
    xor_decrypt_file,
    xor_decrypt_with_hmac,
    xor_encrypt,
    xor_encrypt_file,
    xor_encrypt_with_hmac,
    xor_file,
)

if TYPE_CHECKING:
    from src.security import (
        check_openssl_available,
        generate_cert_in_memory,
        generate_self_signed_cert,
        get_cert_info,
    )

__all__ = [
    "BasicAuthenticator",
    "parse_basic_auth",
    "hash_password",
    "verify_password",
    "generate_random_credentials",
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
    "generate_self_signed_cert",
    "generate_cert_in_memory",
    "check_openssl_available",
    "get_cert_info",
]

_LAZY_EXPORTS = {
    "generate_self_signed_cert": ("src.security", "generate_self_signed_cert"),
    "generate_cert_in_memory": ("src.security", "generate_cert_in_memory"),
    "check_openssl_available": ("src.security", "check_openssl_available"),
    "get_cert_info": ("src.security", "get_cert_info"),
}


def __getattr__(name: str) -> Any:
    if name not in _LAZY_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module_name, attr_name = _LAZY_EXPORTS[name]
    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
