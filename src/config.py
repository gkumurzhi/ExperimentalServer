"""
Server configuration.
"""

# Project version (single source of truth)
__version__ = "2.0.0"


# Hidden files, inaccessible via GET
HIDDEN_FILES: frozenset[str] = frozenset({
    ".opsec_config.json",
    ".env",
    ".gitignore",
    ".git",
    "__pycache__",
})

# Prefixes for OPSEC method name generation
OPSEC_METHOD_PREFIXES: tuple[str, ...] = (
    "CHECK", "SYNC", "VERIFY", "UPDATE", "QUERY",
    "REPORT", "SUBMIT", "VALIDATE", "PROCESS", "EXECUTE"
)

OPSEC_METHOD_SUFFIXES: tuple[str, ...] = (
    "DATA", "STATUS", "INFO", "CONTENT", "RESOURCE",
    "ITEM", "OBJECT", "RECORD", "ENTRY", ""
)

# HTTP status codes
HTTP_STATUS_MESSAGES: dict[int, str] = {
    200: "OK",
    201: "Created",
    204: "No Content",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    413: "Payload Too Large",
    500: "Internal Server Error",
}
