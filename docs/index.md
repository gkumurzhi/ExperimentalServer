# ExperimentalHTTPServer

An experimental HTTP server in pure Python 3.10+ for research, CTF practice,
and controlled red/blue team exercises.

!!! warning "Experimental by design"
    This project is not hardened for untrusted internet exposure. See
    [Security](threat-model.md) and the disclosure policy in
    [SECURITY.md](security.md).

## Highlights

- Custom HTTP methods beyond the RFC 7231 set: `FETCH`, `INFO`, `PING`,
  `NONE`, `NOTE`, `SMUGGLE`, plus randomised OPSEC methods.
- Full TLS 1.2+ with self-signed, user-supplied, or Let's Encrypt
  certificates.
- Basic Auth with PBKDF2-SHA256 hashing and rate-limited brute-force
  protection.
- Secure Notepad with ECDH P-256 + AES-256-GCM when `cryptography` is
  installed.
- WebSocket support (RFC 6455) for real-time note synchronisation.
- OPSEC mode: randomised method names, nginx-header masquerading,
  XOR+HMAC baseline cipher with optional AES-GCM upgrade.
- Sandbox mode restricts file operations to the `uploads/` directory.

## Install

```bash
pip install exphttp            # core only, stdlib
pip install "exphttp[crypto]"  # adds AES-GCM + ECDH features
```

The NOTE API and `/notes/ws` fail closed with `501` when the server is
installed without `exphttp[crypto]`.

## Quick start

```bash
exphttp --tls --auth random --sandbox
```

## Next steps

- [API reference](api.md) — every HTTP method and its payload.
- [Architecture](architecture.md) — how the pieces fit together.
- [Threat model](threat-model.md) — what OPSEC mode does and does not do.
- [Contributing](contributing.md) — how to get a PR merged.
