<!-- Generated from ../CHANGELOG.md by tools/sync_docs.py. Edit CHANGELOG.md and rerun the sync tool. -->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- **Infrastructure:** GitHub Actions CI (Python 3.10–3.13 matrix) with ruff/mypy/pytest and a 65 % coverage gate
- **Infrastructure:** `security.yml` workflow running `pip-audit` and `bandit` weekly and on every PR
- **Infrastructure:** `dependabot.yml` for weekly pip and github-actions updates
- **Infrastructure:** `.pre-commit-config.yaml` mirroring CI checks locally
- **Docs:** `tools/sync_docs.py` generates the MkDocs mirrors for `API.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, and `SECURITY.md`, with CI drift checks
- **Docs:** standalone `LICENSE` (MIT) file in repo root
- **Docs:** `SECURITY.md` — disclosure policy, supported versions, response SLA
- **Docs:** five ADRs in `docs/ADR/` documenting key design decisions
- **Docs:** `docs/threat-model.md` — STRIDE-based threat analysis
- **Docs:** `examples/` directory with `basic_file_server.sh`, `opsec_deployment.md`, `notepad_client.py`, Docker compose
- **Docs:** MkDocs + Material configuration (`mkdocs.yml`) for documentation site
- **Docs:** expanded `CONTRIBUTING.md` with Conventional Commits policy and PR checklist
- **Docs:** `.github/PULL_REQUEST_TEMPLATE.md`
- **Infrastructure:** multi-stage `Dockerfile` with non-root user and HEALTHCHECK, plus `.dockerignore`
- **Tests:** 46 new tests (`test_metrics.py`, `test_handler_registry.py`, `test_security/test_tls_manager.py`, `test_http/test_io.py`, `test_property/` with Hypothesis)
- **Deps:** new optional extras `[test]` (hypothesis, pytest-benchmark) and `[docs]` (mkdocs-material)

### Changed
- **Refactor:** extracted `MetricsCollector` to `src/metrics.py`
- **Refactor:** extracted `TLSManager` to `src/security/tls_manager.py` — SSL context, cert acquisition, cleanup
- **Refactor:** introduced `HandlerRegistry` in `src/handlers/registry.py` (Mapping-compatible) to replace the plain dict while keeping backwards-compatible lookups
- **Refactor:** extracted `receive_request()` to `src/http/io.py` with unit tests
- **Refactor:** split `_process_request` into guard functions (`_check_payload_size`, `_resolve_keep_alive`, `_post_process_response`, `_build_error_response`)
- **Docs:** architecture and threat-model docs now describe `RequestPipeline`, `NotepadService`, `TLSManager`, PBKDF2 auth, and the shared descendant-path resolver that exist in the codebase today
- **Size:** `src/server.py` reduced from 1,000 LOC to 869 LOC

- NOTE method for Secure Notepad with end-to-end AES-256-GCM encryption
- ECDH P-256 key exchange for session key derivation (requires `cryptography` package)
- WebSocket support (RFC 6455) for real-time notepad sync via `/notes/ws`
- Upload method selector — POST, PUT, PATCH, and NONE all perform file upload
- HEAD, PATCH, DELETE HTTP method handlers

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
