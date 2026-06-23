# ExperimentalHTTPServer

An experimental HTTP server for Python 3.10-3.14, built for
research, CTF practice, and controlled red/blue team exercises.

!!! warning "Experimental by design"
    This project is not hardened for untrusted internet exposure. See
    [Security](threat-model.md) and the disclosure policy in
    [SECURITY.md](security.md).

## Highlights

- Custom HTTP methods beyond the RFC 7231 set: `FETCH`, `INFO`, `PING`,
  `NONE`, `NOTE`, `SMUGGLE`, plus advanced upload through any unknown
  method carrying upload payload data.
- Full TLS 1.2+ with self-signed, user-supplied, Let's Encrypt, or sslip.io
  certificates.
- Basic Auth with PBKDF2-SHA256 hashing and rate-limited brute-force
  protection.
- Secure Notepad with ECDH P-256 + AES-256-GCM.
- WebSocket support (RFC 6455) for real-time note synchronisation.
- Advanced upload through JSON body, HTTP headers, or URL parameters with
  optional XOR+HMAC payload handling.
- File operations are restricted to the `uploads/` directory by default.

## Install

For local development, install from a checkout:

```bash
pip install -e .
```

Tagged releases publish the `exphttp` Python package to PyPI and the
`ghcr.io/gkumurzhi/exphttp` image to GHCR. Manual `Release Artifacts` runs
still produce signed wheel/sdist/SBOM artifacts without registry publication.
These public artifacts are supported distribution surfaces, not a managed
hosting service or an internet-safety guarantee by themselves.

The default install includes the runtime crypto and ACME dependencies used by
TLS and Secure Notepad.

## Quick start

```bash
exphttp --tls --auth random
```

## Next steps

- [API reference](api.md) — every HTTP method and its payload.
- [Architecture](architecture.md) — how the pieces fit together.
- [Threat model](threat-model.md) — security boundaries and known limitations.
- [Contributing](contributing.md) — how to get a PR merged.
