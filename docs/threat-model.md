# Threat model

## System boundary

`exphttp` is a single-process HTTP(S) server. The trust boundary is the TCP
socket it listens on. Everything outside is untrusted input; everything
inside the process (configuration, certificate files, uploaded binaries) is
trusted *after* it is validated at the boundary.

## Assets

| Asset | Why it matters |
|-------|----------------|
| Files on disk | Confidentiality (sandbox escape leaks user data), integrity (arbitrary write corrupts the host) |
| Server process | Availability (DoS pins resources, makes the service unusable) |
| Basic Auth credentials | Confidentiality (leaked credentials grant full access) |
| TLS private key | If leaked, enables passive decryption of all recorded traffic |
| Notepad ECDH session key | Short-lived; leak compromises one session, not a permanent secret |
| OPSEC config (`.opsec_config.json`) | If leaked to an attacker, reveals the randomised method names |

## STRIDE summary

### Spoofing

| Threat | Mitigation |
|--------|------------|
| Client impersonating a legit user | Basic Auth with SHA-256 + salt; rate limiting on failed auth |
| Server impersonation (MITM) | TLS with modern ciphers; Let's Encrypt or user-supplied cert |
| Forged WebSocket Upgrade | `Sec-WebSocket-Key` handshake validated via stdlib HMAC |

### Tampering

| Threat | Mitigation |
|--------|------------|
| Path traversal in upload/download | `Path.resolve().relative_to(base)` — see ADR-004 |
| Content-Length smuggling (duplicate/negative CL) | Rejected in `src/http/io.py:_parse_content_length` |
| Transfer-Encoding smuggling | Chunked encoding is not supported by the reader |
| OPSEC payload modification | HMAC-SHA256 tag over ciphertext + metadata |
| WebSocket frame injection | Frame size capped at 10 MB in `src/websocket.py` |

### Repudiation

| Threat | Mitigation |
|--------|------------|
| Denial that an action occurred | Structured JSON logs with request IDs; not tamper-evident (deferred) |

### Information disclosure

| Threat | Mitigation |
|--------|------------|
| Hidden file access (`.env`, `.opsec_config.json`) | `HIDDEN_FILES` frozenset blocks GET regardless of sandbox mode |
| Directory listing in production | `--no-info` disables the INFO method |
| Auth timing side channel | Dummy password verification on unknown users (`verify_password`) |
| TLS downgrade | Minimum TLS 1.2; modern cipher suite only |
| Error messages leaking internal paths | OPSEC mode returns generic `{"error": "Error"}`; non-OPSEC returns `Internal Server Error` without traceback |

### Denial of Service

| Threat | Mitigation |
|--------|------------|
| Slowloris (headers never end) | 30-second header read timeout |
| Large upload fills disk | `--max-upload MB` enforced before and during read |
| Infinite keep-alive | `KEEP_ALIVE_MAX = 100` requests per connection, 15 s idle timeout |
| WebSocket flood | Frame size limit; notepad writes behind `self._notes_lock` |
| Auth brute force | `AuthRateLimiter` blocks IPs after repeated failures |

**Explicitly out of scope:** sophisticated DDoS (volumetric, amplification,
resource-exhaustion from thousands of authenticated clients). Deploy behind
a reverse proxy / CDN if that is a concern.

### Elevation of privilege

| Threat | Mitigation |
|--------|------------|
| Symlink escape from sandbox | Symlinks are resolved before the `relative_to` check |
| Uploading an executable to a served directory | Sandbox mode restricts writes to `uploads/`; clients must not serve uploads/ with `X-Content-Type-Options: nosniff` disabled (default headers set this) |
| OPSEC mode used as sole security layer | Documented in `SECURITY.md` and ADR-002 — always pair with TLS + Auth |

## Non-goals

- **Perfect forward secrecy for OPSEC uploads.** XOR+HMAC baseline is
  fragile against chosen-plaintext; use AES-GCM path (`[crypto]` extra) for
  real-world deployments.
- **Resistance to traffic analysis.** OPSEC method-name obfuscation masks
  intent from logs, not from wire observers who can see timings and
  sizes.
- **Defense against compromised peer.** Once a client holds valid Basic
  Auth credentials, the server trusts every request it sends.

## Versioned

This document is reviewed on every major release. Last review: 2026-04-14.
