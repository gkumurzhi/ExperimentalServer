# ADR-003: Runtime crypto and ACME dependencies

- **Status:** accepted

## Context

The project originally advertised "zero external dependencies for core functionality".
That kept simple installs small, but it made production-grade TLS and Secure Notepad
harder to operate:

- Self-signed TLS certificates depended on an external `openssl` executable.
- Let's Encrypt issuance depended on an external `certbot` executable.
- Secure Notepad and AEAD upload handling needed `cryptography` anyway.

## Decision

Make crypto and ACME support part of the default runtime install:

- Keep `cryptography` as a normal dependency for AES-GCM, ECDH, X.509 parsing,
  and self-signed certificate generation.
- Add Certbot's official `acme` Python library as a normal dependency for
  built-in HTTP-01 certificate issuance.
- Keep the `[crypto]` extra as an empty compatibility extra so old install
  commands continue to work.
- Keep fail-closed behavior if the crypto backend is unavailable in an
  unsupported or manually modified environment.

## Consequences

### Positive

- `pip install exphttp` includes the same crypto/TLS behavior used by CI and
  Docker.
- TLS no longer requires external `openssl` or `certbot` binaries.
- Let’s Encrypt and sslip.io certificate issuance can be tested through Python
  mocks rather than subprocess behavior.

### Negative

- The default dependency surface is larger and includes OpenSSL-backed wheels.
- Dependency security scanning matters more because crypto/ACME packages are now
  in the normal runtime path.
- Environments that require strict stdlib-only Python installs must pin an older
  release or vendor their own reduced build.
