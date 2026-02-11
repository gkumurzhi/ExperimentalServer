"""
Модуль обработчиков HTTP-методов.
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
    Объединённый миксин со всеми обработчиками HTTP-методов.

    Включает:
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
