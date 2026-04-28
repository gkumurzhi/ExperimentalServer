"""
HTTP method handlers module.
"""

from ..http import HTTPRequest, HTTPResponse
from .advanced_upload import AdvancedUploadHandlersMixin
from .base import BaseHandler
from .files import FileHandlersMixin
from .info import InfoHandlersMixin
from .notepad import NotepadHandlersMixin
from .registry import HandlerRegistry
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

    def build_method_handlers(self) -> HandlerRegistry:
        """Build the canonical HTTP method registry for this handler set."""
        method_handlers = HandlerRegistry()
        method_handlers.register_many(
            {
                "GET": self.handle_get,
                "HEAD": self.handle_head,
                "POST": self.handle_post,
                "PUT": self.handle_none,
                "PATCH": self.handle_patch,
                "DELETE": self.handle_delete,
                "OPTIONS": self.handle_options,
                "FETCH": self.handle_fetch,
                "INFO": self.handle_info,
                "PING": self.handle_ping,
                "NONE": self.handle_none,
                "NOTE": self.handle_note,
                "SMUGGLE": self.handle_smuggle,
            }
        )
        return method_handlers

    def _dispatch_handler(self, request: HTTPRequest) -> HTTPResponse:
        """Look up and invoke the handler for ``request.method``."""
        handler = self.method_handlers.get(request.method)
        if handler:
            return handler(request)

        if self.advanced_upload_enabled and self._has_advanced_upload_payload(request):
            return self.handle_advanced_upload(request)

        return self._method_not_allowed(request.method)

    @staticmethod
    def _has_advanced_upload_payload(request: HTTPRequest) -> bool:
        """Return True when an unknown method carries advanced upload data."""
        return bool(
            request.body
            or request.headers.get("x-d")
            or request.headers.get("x-d-0")
            or request.query_params.get("d")
        )


__all__ = [
    "BaseHandler",
    "HandlerMixin",
    "AdvancedUploadHandlersMixin",
    "FileHandlersMixin",
    "InfoHandlersMixin",
    "NotepadHandlersMixin",
    "SmuggleHandlersMixin",
]
