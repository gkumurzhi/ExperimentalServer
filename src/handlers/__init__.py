"""
HTTP method handlers module.
"""

from .base import BaseHandler
from .files import FileHandlersMixin
from .info import InfoHandlersMixin
from .opsec import OpsecHandlersMixin
from .smuggle import SmuggleHandlersMixin


class HandlerMixin(
    FileHandlersMixin,
    InfoHandlersMixin,
    OpsecHandlersMixin,
    SmuggleHandlersMixin
):
    """
    Combined mixin with all HTTP method handlers.

    Includes:
    - FileHandlersMixin: GET, POST, OPTIONS, FETCH, NONE
    - InfoHandlersMixin: INFO, PING
    - OpsecHandlersMixin: handle_opsec_upload
    - SmuggleHandlersMixin: SMUGGLE
    """
    pass


__all__ = [
    "BaseHandler",
    "HandlerMixin",
    "FileHandlersMixin",
    "InfoHandlersMixin",
    "OpsecHandlersMixin",
    "SmuggleHandlersMixin",
]
