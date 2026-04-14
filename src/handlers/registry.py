"""Registry of HTTP method handlers.

Replaces the hard-coded `method_handlers` dict with a first-class object that
supports dynamic registration (needed for OPSEC-mode random method names) and
provides a single place to look up handlers during request dispatch.

The legacy `method_handlers` dict on the server is kept as a live view of the
registry for backwards compatibility with tests and the INFO handler.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..http import HTTPRequest, HTTPResponse

Handler = Callable[["HTTPRequest"], "HTTPResponse"]


class HandlerRegistry(Mapping[str, Handler]):
    """Maps HTTP method names to handler callables.

    Implements the Mapping protocol so it can be passed anywhere a
    ``dict[str, Callable]`` is expected — keeps existing test fixtures
    working without modification.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, Handler] = {}

    def register(self, method: str, handler: Handler) -> None:
        """Register a handler for an HTTP method (uppercased)."""
        self._handlers[method.upper()] = handler

    def register_many(self, mapping: Mapping[str, Handler]) -> None:
        for method, handler in mapping.items():
            self.register(method, handler)

    def unregister(self, method: str) -> None:
        self._handlers.pop(method.upper(), None)

    def get_handler(self, method: str) -> Handler | None:
        """Look up a handler by method name (case-insensitive)."""
        return self._handlers.get(method.upper())

    def methods(self) -> list[str]:
        """List of registered method names, preserving insertion order."""
        return list(self._handlers.keys())

    # ---- Mapping protocol (for dict compatibility) ----

    def __getitem__(self, key: str) -> Handler:
        return self._handlers[key.upper()]

    def __iter__(self) -> Iterator[str]:
        return iter(self._handlers)

    def __len__(self) -> int:
        return len(self._handlers)

    def __contains__(self, key: object) -> bool:
        if isinstance(key, str):
            return key.upper() in self._handlers
        return False
