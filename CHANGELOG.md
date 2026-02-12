# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Security
- Fix XSS in HTML smuggling — filenames escaped via `json.dumps()` for JS context, `innerHTML` replaced with `textContent` (B01)
- Replace SHA-256 password hashing with PBKDF2-SHA256 (600K iterations) (B07)
- Fix path traversal check — replace `startswith()` with `Path.relative_to()` (B06)
- Add auth rate limiting — 5 failures per IP = 30s cooldown (B08)
- Add per-request total timeout — 30s headers, 300s body (anti-Slowloris) (B02)

### Performance
- Replace O(n^2) buffer concatenation with chunks list in request receiver (B03)
- Move TLS handshake from accept loop to worker thread (B04)
- Increase socket listen backlog from 5 to 128 (B05)
- Add `cancel_futures=True` to ThreadPoolExecutor shutdown (B32)
- Streaming file I/O — GET and FETCH stream files in 64KB chunks from disk instead of loading entirely into memory (B17)

### Improved
- Log response status code and latency: `[reqid] IP - METHOD /path -> 200 (12ms)` (B09, B37)
- Log path traversal attempts at WARNING level (B10)
- Log DoS protection triggers (oversized requests, timeouts) (B11)
- Use `logger.exception()` for stack traces on request errors (B12)
- Fix HTTP header parser to accept `Header:value` without space (B19)
- Thread-safe smuggle temp file set with `threading.Lock` (B20)
- Centralize path validation into `_resolve_safe_path()` method (B21)
- Merge XOR encrypt/decrypt into single `xor_bytes()` function (B22)
- Clean partial files on write failure in upload and OPSEC handlers (B30)
- Clean smuggle temp files on server shutdown (B31)
- Add Content-Security-Policy header to HTML responses (B34)
- Block symlink access in file serving (defense-in-depth) (B35)
- Use cryptographically secure RNG (`SystemRandom`) in captcha generation (B36)
- Add 8-char hex request ID for log correlation + `X-Request-Id` response header (B37)
- Add pagination to INFO directory listing: `?offset=N&limit=M` (B39)
- Parse query string parameters from URL into `request.query_params` dict
- Remove server root directory path from PING response (B47)
- In-memory metrics (request count, errors, bytes sent, status codes) exposed via PING (B28)
- Add `--json-log` CLI flag for structured JSON log output (B38)
- Add Table of Contents to README (B43)
- Update README: fix outdated technical details (backlog, timeouts, auth hashing)

### Code Quality
- Fix all ruff lint errors: `open()` → `Path.open()`, `raise ... from err`, line length (B23)
- Per-file E501 ignore for minified CSS/HTML templates in ruff config
- Add `make_request()` test helper in conftest (B25)
- Add path traversal test suite — 15 tests covering traversal, sandbox, symlinks (B26)
- Add handler integration tests — 30 tests for GET/POST/FETCH/INFO/PING/OPTIONS/OPSEC (B27)
- Add streaming, symlink, pagination, and query param tests
- Add CLI argument parsing tests (16 tests) and server routing/OPSEC/smuggle tests (16 tests) (B44)
- Fix mypy errors: 20 → 0 across 8 files (B24)
- Test count: 64 → 149

### Removed
- Remove unused `ServerConfig` dataclass from `config.py` (B15)
- Remove unused exception hierarchy from `exceptions.py` (B16)

## [2.0.0] - 2025-02-08

### Added
- Custom HTTP methods: GET, POST, FETCH, INFO, PING, NONE, SMUGGLE
- TLS/HTTPS with self-signed or custom certificates
- Let's Encrypt support via certbot subprocess
- HTTP Basic Authentication with random credential generation
- OPSEC mode: random method names, XOR encryption, HMAC verification, nginx header spoofing
- Sandbox mode: restrict file access to `uploads/` directory
- HTML Smuggling with optional password-protected downloads
- Password captcha generation for protected downloads
- `--open` flag to auto-open browser
- Web UI with file upload, download, and directory listing
- XOR encryption/decryption CLI tool (`tools/decrypt.py`)
