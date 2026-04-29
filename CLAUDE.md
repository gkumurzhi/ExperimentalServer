# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ExperimentalHTTPServer is a feature-rich HTTP server written in pure Python 3.10+ with zero external dependencies for core functionality. It supports custom HTTP methods, TLS/HTTPS, Basic Authentication, uploads-only file access, advanced uploads, Secure Notepad, and HTML Smuggling.

Canonical project documentation lives in:

- `README.md` — user-facing runtime overview and examples
- `API.md` — HTTP method contracts and response shapes
- `CONTRIBUTING.md` — code conventions and contribution workflow
- `docs/ADR/ADR-004-uploads-relative-to.md` — path containment rules for uploads-only access

## Commands

```bash
# Install for development
pip install -e ".[dev]"

# Run the server
python -m src
# or after install:
exphttp

# Common CLI options
exphttp --tls --auth random           # HTTPS with random credentials
exphttp --advanced-upload             # Enable unknown-method advanced uploads
exphttp -H 0.0.0.0 -p 8443 -m 500     # Custom host, port, max upload MB

# Run tests
pytest

# Run tests with coverage
pytest --cov=src

# XOR encryption/decryption tool
python tools/decrypt.py -e -k "key" file.txt    # encrypt
python tools/decrypt.py -k "key" file.txt.enc   # decrypt
```

## Architecture

### Mixin-Based Handler Pattern

The server uses Python mixins for composable HTTP method handling:

```
ExperimentalHTTPServer (src/server.py)
    ↓
HandlerMixin (handlers/__init__.py - composition of all handlers)
    ├── FileHandlersMixin      → GET, HEAD, POST, PUT, PATCH, DELETE, OPTIONS, FETCH, NONE
    ├── InfoHandlersMixin      → INFO, PING
    ├── NotepadHandlersMixin   → NOTE (Secure Notepad with ECDH)
    ├── AdvancedUploadHandlersMixin → advanced upload fallback for unknown methods
    └── SmuggleHandlersMixin   → HTML Smuggling
        ↓
BaseHandler (handlers/base.py - common utilities)
```

### Request Processing Flow

1. Client connection → TLS wrapped if enabled
2. `_receive_request()` → Parse raw HTTP from socket
3. `HTTPRequest` (http/request.py) → Parse method, path, headers, body
4. Auth check → Validate Basic Auth if enabled
5. Handler lookup → Match a registered HTTP method
6. Handler execution → Call appropriate mixin method
7. Unknown method fallback → If `--advanced-upload` is enabled and the request carries advanced payload data, call `handle_advanced_upload`
8. `HTTPResponse.build()` (http/response.py) → Generate response

### Key Modules

- **src/server.py** - Main `ExperimentalHTTPServer` class with socket handling and ThreadPoolExecutor
- **src/handlers/** - Method handlers (each mixin handles specific HTTP methods)
- **src/handlers/advanced_upload.py** - Unknown-method advanced upload handling for body/header/query payloads
- **src/handlers/notepad.py** - Secure Notepad with end-to-end AES-256-GCM encryption
- **src/security/** - Auth (Basic Auth), crypto (XOR/HMAC), tls (self-signed cert generation)
- **src/security/keys.py** - ECDH P-256 key exchange and HKDF session key derivation
- **src/http/** - Request parsing, response building, path utilities
- **src/config.py** - Constants such as hidden file names and HTTP status messages
- **src/websocket.py** - WebSocket frame parsing and handshake (RFC 6455)

### Security Layers

1. **Transport**: TLS 1.2+ with self-signed or custom certs (security/tls.py)
2. **Authentication**: HTTP Basic Auth with SHA256+salt hashing (security/auth.py)
3. **Authorization**: User file operations are constrained to `uploads/`, with hidden file protection
4. **Advanced upload integrity**: Optional XOR obfuscation and HMAC verification for advanced upload payloads
5. **Secure Notepad**: ECDH key exchange and AES-256-GCM note encryption when `cryptography` is installed

## Adding New HTTP Methods

1. Create or extend a mixin class in `src/handlers/` inheriting `BaseHandler`
2. Add handler method: `def handle_methodname(self, request: HTTPRequest) -> HTTPResponse`
3. Register the method in `HandlerMixin.build_method_handlers()` in `src/handlers/__init__.py`
4. Add to `HandlerMixin` composition in `src/handlers/__init__.py`

## Code Conventions

- Full type annotations using Python 3.10+ syntax (`X | None` not `Optional[X]`)
- `pathlib.Path` for all file operations with `.resolve()` for absolute paths
- Path traversal defense: use `Path.resolve().relative_to()` containment via `resolve_descendant_path()` / `BaseHandler._resolve_safe_path()`; see ADR-004
- Logger name: `"httpserver"` with format `%(asctime)s [%(levelname)s] %(message)s`

## Custom HTTP Methods Reference

| Method | Handler | Purpose |
|--------|---------|---------|
| GET | handle_get | Serve files (index.html, uploads, static) |
| HEAD | handle_head | Same as GET but headers only (no body) |
| POST | handle_post | File upload (delegates to handle_none) |
| PUT | handle_none | Binary file upload (alias) |
| PATCH | handle_patch | Binary file upload (delegates to handle_none) |
| DELETE | handle_delete | Delete uploaded file from uploads/ |
| OPTIONS | handle_options | CORS preflight |
| FETCH | handle_fetch | Download with Content-Disposition |
| INFO | handle_info | Directory listing (JSON) |
| PING | handle_ping | Health check |
| NONE | handle_none | Binary file upload |
| NOTE | handle_note | Secure Notepad (ECDH + AES-256-GCM) |
| SMUGGLE | handle_smuggle | Generate HTML smuggling page |
| Unknown method with advanced payload | handle_advanced_upload | Advanced upload when `--advanced-upload` is enabled |
