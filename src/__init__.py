"""
Experimental HTTP Server - модульный HTTP-сервер с поддержкой произвольных методов.
"""

from .http import HTTPRequest, HTTPResponse
from .server import ExperimentalHTTPServer
from .config import ServerConfig, HIDDEN_FILES
from .exceptions import (
    ServerError,
    PathTraversalError,
    FileTooLargeError,
    AuthenticationError,
    MethodNotAllowedError,
    InvalidRequestError,
    HMACVerificationError,
)
from .security import (
    BasicAuthenticator,
    generate_random_credentials,
    xor_encrypt,
    xor_decrypt,
    compute_hmac,
    verify_hmac,
    xor_encrypt_with_hmac,
    xor_decrypt_with_hmac,
    generate_self_signed_cert,
    check_openssl_available,
)
from .utils import (
    generate_password_captcha,
    generate_smuggling_html,
)

from .config import __version__  # noqa: F401 — re-export
__all__ = [
    # Core
    "HTTPRequest",
    "HTTPResponse",
    "ExperimentalHTTPServer",
    "ServerConfig",
    # Exceptions
    "ServerError",
    "PathTraversalError",
    "FileTooLargeError",
    "AuthenticationError",
    "MethodNotAllowedError",
    "InvalidRequestError",
    "HMACVerificationError",
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
]
