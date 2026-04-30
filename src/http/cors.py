"""CORS policy helpers."""

from __future__ import annotations

import re

CORS_ALLOW_METHODS: tuple[str, ...] = (
    "GET",
    "HEAD",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "FETCH",
    "INFO",
    "PING",
    "NONE",
    "NOTE",
    "SMUGGLE",
    "OPTIONS",
)

CORS_ALLOW_HEADERS: tuple[str, ...] = (
    "Authorization",
    "Content-Type",
    "If-None-Match",
    "X-File-Name",
    "X-Session-Id",
    "X-Exphttp-No-Gzip",
    "X-D",
    "X-E",
    "X-K",
    "X-Kb64",
    "X-N",
    "X-H",
    "X-D-0",
    "X-D-1",
    "X-D-2",
    "X-D-3",
    "X-D-4",
    "X-D-5",
    "X-D-6",
    "X-D-7",
    "X-D-8",
    "X-D-9",
)

CORS_EXPOSE_HEADERS: tuple[str, ...] = (
    "ETag",
    "X-Request-Id",
    "X-File-Name",
    "X-File-Size",
    "X-File-Path",
    "X-File-Modified",
    "X-Upload-Status",
    "X-Fetch-Status",
    "X-Ping-Response",
    "X-Smuggle-URL",
)

CORS_ALLOW_METHODS_HEADER = ", ".join(CORS_ALLOW_METHODS)
CORS_ALLOW_HEADERS_HEADER = ", ".join(CORS_ALLOW_HEADERS)
CORS_EXPOSE_HEADERS_HEADER = ", ".join(CORS_EXPOSE_HEADERS)

_HTTP_TOKEN_RE = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")
_HEADER_NAME_MAP = {header.lower(): header for header in CORS_ALLOW_HEADERS}


def parse_cors_origins(configured_origin: str | None) -> tuple[str, ...]:
    """Parse a comma-separated CORS origin config into an allowlist."""
    if not configured_origin:
        return ()

    origins: list[str] = []
    seen: set[str] = set()
    for raw_origin in configured_origin.split(","):
        origin = raw_origin.strip()
        if not origin or origin in seen:
            continue
        origins.append(origin)
        seen.add(origin)

    if "*" in seen and len(origins) > 1:
        raise ValueError("CORS wildcard origin '*' cannot be combined with explicit origins")
    if "*" in seen:
        return ("*",)
    return tuple(origins)


def resolve_cors_origin(
    configured_origin: str | None,
    request_origin: str | None,
) -> str | None:
    """Return the browser-valid ACAO value for a request, or None."""
    origins = parse_cors_origins(configured_origin)
    if not origins:
        return None
    if origins == ("*",):
        return "*"
    if request_origin and request_origin in origins:
        return request_origin
    return None


def normalize_cors_header_origin(cors_origin: str | None) -> str | None:
    """Accept only a single valid ACAO value for response emission."""
    origins = parse_cors_origins(cors_origin)
    if len(origins) != 1:
        return None
    return origins[0]


def is_http_token(value: str) -> bool:
    """Return True when value is an RFC HTTP token."""
    return bool(_HTTP_TOKEN_RE.fullmatch(value))


def resolve_preflight_allow_methods(
    requested_method: str,
    *,
    advanced_upload_enabled: bool,
) -> str:
    """Return allowed methods, conditionally including an advanced upload token."""
    methods = list(CORS_ALLOW_METHODS)
    method = requested_method.strip().upper()
    if (
        method
        and method not in methods
        and advanced_upload_enabled
        and is_http_token(method)
    ):
        methods.append(method)
    return ", ".join(methods)


def resolve_preflight_allow_headers(requested_headers: str) -> str | None:
    """Return the allowed subset of requested CORS headers."""
    allowed: list[str] = []
    seen: set[str] = set()
    for raw_header in requested_headers.split(","):
        header = raw_header.strip()
        if not header or not is_http_token(header):
            continue
        header_lower = header.lower()
        canonical = _HEADER_NAME_MAP.get(header_lower)
        if canonical is None and header_lower.startswith("x-d-"):
            suffix = header_lower[4:]
            if suffix.isdigit():
                canonical = f"X-D-{suffix}"
        if canonical is None or canonical.lower() in seen:
            continue
        allowed.append(canonical)
        seen.add(canonical.lower())

    if not allowed:
        return None
    return ", ".join(allowed)
