"""
HTTP method handlers module.
"""

from .base import BaseHandler
from .advanced_upload import AdvancedUploadHandlersMixin
from .files import FileHandlersMixin
from .info import InfoHandlersMixin
from .notepad import NotepadHandlersMixin
from .smuggle import SmuggleHandlersMixin


class HandlerMixin(
    FileHandlersMixin,
    InfoHandlersMixin,
    NotepadHandlersMixin,
    AdvancedUploadHandlersMixin,
    SmuggleHandlersMixin,
):
    """
    Combined mixin with all HTTP method handlers.

    Includes:
    - FileHandlersMixin: GET, POST, OPTIONS, FETCH, NONE
    - InfoHandlersMixin: INFO, PING
    - NotepadHandlersMixin: NOTE
    - AdvancedUploadHandlersMixin: handle_advanced_upload
    - SmuggleHandlersMixin: SMUGGLE
    """

    pass


__all__ = [
    "BaseHandler",
    "HandlerMixin",
    "AdvancedUploadHandlersMixin",
    "FileHandlersMixin",
    "InfoHandlersMixin",
    "NotepadHandlersMixin",
    "SmuggleHandlersMixin",
]
