"""Server feature profile definitions."""

from __future__ import annotations

from dataclasses import dataclass

SERVE_METHODS: tuple[str, ...] = ("GET", "HEAD", "OPTIONS", "FETCH", "INFO", "PING")
WORKSPACE_METHODS: tuple[str, ...] = (
    "GET",
    "HEAD",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "OPTIONS",
    "FETCH",
    "INFO",
    "PING",
    "NONE",
)
LAB_METHODS: tuple[str, ...] = WORKSPACE_METHODS + ("NOTE", "SMUGGLE")
KNOWN_PROFILE_NAMES: tuple[str, ...] = ("serve", "workspace", "lab")
DEFAULT_PROFILE = "lab"
BROWSER_PROTECTED_MUTATION_METHODS = frozenset(
    {
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "NONE",
        "NOTE",
        "SMUGGLE",
    }
)
BROWSER_READ_ONLY_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "FETCH", "INFO", "PING"})
WEBSOCKET_NOTES_PATH_PREFIX = "/notes/ws"


@dataclass(frozen=True)
class FeatureSet:
    """Immutable server capability set derived from one named profile."""

    profile: str
    methods: tuple[str, ...]
    ordinary_upload: bool
    file_delete: bool
    clear_uploads: bool
    advanced_upload: bool
    smuggle: bool
    note_http: bool
    note_delete: bool
    note_clear: bool
    websocket_notes: bool

    @property
    def allow_unknown_advanced_upload_methods(self) -> bool:
        """Return True when unknown-method advanced upload fallback is enabled."""
        return self.advanced_upload

    def registry_methods(self) -> tuple[str, ...]:
        """Return HTTP methods that should be registered for this profile."""
        return self.methods

    def cors_methods(self, *, read_only: bool = False) -> tuple[str, ...]:
        """Return HTTP methods that should be advertised through CORS."""
        return SERVE_METHODS if read_only else self.methods

    def allows_unknown_cors_method(self, requested_method: str, *, read_only: bool = False) -> bool:
        """Return True when CORS may echo an advanced upload method token."""
        return (
            not read_only
            and self.allow_unknown_advanced_upload_methods
            and bool(requested_method.strip())
        )

    def allows_advanced_upload_fallback(self, *, has_payload: bool) -> bool:
        """Return True when an unknown method may route to advanced upload."""
        return self.allow_unknown_advanced_upload_methods and has_payload

    def requires_browser_mutation_guard(
        self,
        method: str,
        *,
        method_registered: bool,
        has_advanced_upload_payload: bool,
    ) -> bool:
        """Return True when browser-origin mutation policy applies to a request."""
        method_upper = method.upper()
        if method_upper in BROWSER_PROTECTED_MUTATION_METHODS and method_registered:
            return True
        if method_upper in BROWSER_READ_ONLY_METHODS:
            return False
        return self.allows_advanced_upload_fallback(has_payload=has_advanced_upload_payload)

    def websocket_route_enabled(self, path: str) -> bool:
        """Return True when this profile admits the notepad WebSocket route."""
        return self.websocket_notes and path.startswith(WEBSOCKET_NOTES_PATH_PREFIX)

    def capabilities(self) -> dict[str, bool]:
        """Return the public capability map exposed by PING and the UI."""
        return {
            "ordinary_upload": self.ordinary_upload,
            "file_delete": self.file_delete,
            "clear_uploads": self.clear_uploads,
            "advanced_upload": self.advanced_upload,
            "smuggle": self.smuggle,
            "note_http": self.note_http,
            "note_delete": self.note_delete,
            "note_clear": self.note_clear,
            "websocket_notes": self.websocket_notes,
        }


FEATURE_PROFILES: dict[str, FeatureSet] = {
    "serve": FeatureSet(
        profile="serve",
        methods=SERVE_METHODS,
        ordinary_upload=False,
        file_delete=False,
        clear_uploads=False,
        advanced_upload=False,
        smuggle=False,
        note_http=False,
        note_delete=False,
        note_clear=False,
        websocket_notes=False,
    ),
    "workspace": FeatureSet(
        profile="workspace",
        methods=WORKSPACE_METHODS,
        ordinary_upload=True,
        file_delete=True,
        clear_uploads=False,
        advanced_upload=False,
        smuggle=False,
        note_http=False,
        note_delete=False,
        note_clear=False,
        websocket_notes=False,
    ),
    "lab": FeatureSet(
        profile="lab",
        methods=LAB_METHODS,
        ordinary_upload=True,
        file_delete=True,
        clear_uploads=True,
        advanced_upload=True,
        smuggle=True,
        note_http=True,
        note_delete=True,
        note_clear=True,
        websocket_notes=True,
    ),
}


def resolve_feature_profile(profile: str | None) -> FeatureSet:
    """Resolve a profile name to its immutable feature set."""
    profile_name = (profile or DEFAULT_PROFILE).strip().lower()
    try:
        return FEATURE_PROFILES[profile_name]
    except KeyError:
        allowed = ", ".join(KNOWN_PROFILE_NAMES)
        raise ValueError(f"profile must be one of: {allowed}") from None


def profile_names() -> tuple[str, ...]:
    """Return supported profile names for CLI choices."""
    return KNOWN_PROFILE_NAMES
