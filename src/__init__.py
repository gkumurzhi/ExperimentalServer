"""
Experimental HTTP Server — modular HTTP server with custom method support.
"""

from .config import (
    HIDDEN_FILES,
    __version__,  # noqa: F401 — re-export
)
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
from .utils import (
    generate_password_captcha,
    generate_smuggling_html,
)

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
