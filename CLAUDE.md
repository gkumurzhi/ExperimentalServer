# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ExperimentalHTTPServer is a feature-rich HTTP server written in pure Python 3.10+ with zero external dependencies for core functionality. It supports custom HTTP methods, TLS/HTTPS, Basic Authentication, OPSEC mode (obfuscated file transfer with encryption), and sandbox restrictions.

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
exphttp --opsec --sandbox             # OPSEC mode with restricted paths
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
    ├── FileHandlersMixin      → GET, POST, PUT, OPTIONS, FETCH, NONE
    ├── InfoHandlersMixin      → INFO, PING
    ├── OpsecHandlersMixin     → OPSEC upload handling
    └── SmuggleHandlersMixin   → HTML Smuggling
        ↓
BaseHandler (handlers/base.py - common utilities)
```

### Request Processing Flow

1. Client connection → TLS wrapped if enabled
2. `_receive_request()` → Parse raw HTTP from socket
3. `HTTPRequest` (http/request.py) → Parse method, path, headers, body
4. Auth check → Validate Basic Auth if enabled
5. Handler lookup → Match HTTP method (random names in OPSEC mode)
6. Handler execution → Call appropriate mixin method
7. `HTTPResponse.build()` (http/response.py) → Generate response
8. OPSEC processing → Add nginx masquerading headers if enabled

### Key Modules

- **src/server.py** - Main `ExperimentalHTTPServer` class with socket handling and ThreadPoolExecutor
- **src/handlers/** - Method handlers (each mixin handles specific HTTP methods)
- **src/security/** - Auth (Basic Auth), crypto (XOR/HMAC), tls (self-signed cert generation)
- **src/http/** - Request parsing, response building, path utilities
- **src/config.py** - `ServerConfig` dataclass and constants (hidden files list, OPSEC prefixes/suffixes)

### Security Layers

1. **Transport**: TLS 1.2+ with self-signed or custom certs (security/tls.py)
2. **Authentication**: HTTP Basic Auth with SHA256+salt hashing (security/auth.py)
3. **Authorization**: Sandbox mode restricts to `uploads/` directory, hidden file protection
4. **Obfuscation (OPSEC)**: Random HTTP method names, XOR encryption, HMAC verification, nginx header spoofing

## Adding New HTTP Methods

1. Create or extend a mixin class in `src/handlers/` inheriting `BaseHandler`
2. Add handler method: `def handle_methodname(self, request: HTTPRequest) -> HTTPResponse`
3. Register in `ExperimentalHTTPServer.method_handlers` dict in `src/server.py`
4. Add to `HandlerMixin` composition in `src/handlers/__init__.py`

## Code Conventions

- Full type annotations using Python 3.10+ syntax (`X | None` not `Optional[X]`)
- `pathlib.Path` for all file operations with `.resolve()` for absolute paths
- Path traversal defense: always verify `str(resolved_path).startswith(str(base_dir))`
- Logger name: `"httpserver"` with format `%(asctime)s [%(levelname)s] %(message)s`
- Custom exceptions in `src/exceptions.py` map to HTTP status codes

## Custom HTTP Methods Reference

| Method | Handler | Purpose |
|--------|---------|---------|
| GET | handle_get | Serve files (index.html, uploads, static) |
| POST | handle_post | Echo request body |
| FETCH | handle_fetch | Download with Content-Disposition |
| INFO | handle_info | Directory listing (JSON) |
| PING | handle_ping | Health check |
| NONE | handle_none | Binary file upload |
| SMUGGLE | handle_smuggle | Generate HTML smuggling page |
| OPSEC_* | handle_opsec_upload | Encrypted upload (random method name) |
