"""
Experimental HTTP Server — modular HTTP server with custom method support.
"""

from importlib import import_module
from typing import TYPE_CHECKING, Any

from .config import (
    HIDDEN_FILES,
    __version__,  # noqa: F401 — re-export
)

if TYPE_CHECKING:
    from .http import HTTPRequest, HTTPResponse
    from .security import (
        BasicAuthenticator,
        check_openssl_available,
        compute_hmac,
        generate_random_credentials,
        generate_self_signed_cert,
        verify_hmac,
        xor_decrypt,
        xor_decrypt_with_hmac,
        xor_encrypt,
        xor_encrypt_with_hmac,
    )
    from .server import ExperimentalHTTPServer
    from .utils import generate_password_captcha, generate_smuggling_html

__all__ = [
    # Core
    "HTTPRequest",
    "HTTPResponse",
    "ExperimentalHTTPServer",
    # Security
    "BasicAuthenticator",
    "generate_random_credentials",
    "xor_encrypt",
    "xor_decrypt",
    "compute_hmac",
    "verify_hmac",
    "xor_encrypt_with_hmac",
    "xor_decrypt_with_hmac",
    "generate_self_signed_cert",
    "check_openssl_available",
    # Utils
    "generate_password_captcha",
    "generate_smuggling_html",
    # Constants
    "HIDDEN_FILES",
    "__version__",
]

_LAZY_EXPORTS = {
    "HTTPRequest": ("src.http", "HTTPRequest"),
    "HTTPResponse": ("src.http", "HTTPResponse"),
    "ExperimentalHTTPServer": ("src.server", "ExperimentalHTTPServer"),
    "BasicAuthenticator": ("src.security", "BasicAuthenticator"),
    "generate_random_credentials": ("src.security", "generate_random_credentials"),
    "xor_encrypt": ("src.security", "xor_encrypt"),
    "xor_decrypt": ("src.security", "xor_decrypt"),
    "compute_hmac": ("src.security", "compute_hmac"),
    "verify_hmac": ("src.security", "verify_hmac"),
    "xor_encrypt_with_hmac": ("src.security", "xor_encrypt_with_hmac"),
    "xor_decrypt_with_hmac": ("src.security", "xor_decrypt_with_hmac"),
    "generate_self_signed_cert": ("src.security", "generate_self_signed_cert"),
    "check_openssl_available": ("src.security", "check_openssl_available"),
    "generate_password_captcha": ("src.utils", "generate_password_captcha"),
    "generate_smuggling_html": ("src.utils", "generate_smuggling_html"),
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
