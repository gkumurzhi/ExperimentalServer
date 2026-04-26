# ADR-003: `cryptography` is an optional dependency

- **Status:** accepted

## Context

The project advertises "zero external dependencies for core functionality".
However, three features benefit from modern crypto primitives:

- AES-256-GCM encryption for advanced upload payloads (superior to XOR+HMAC baseline).
- ECDH P-256 key exchange for the Secure Notepad end-to-end mode.
- Let's Encrypt certificate acquisition (via `certbot`, external tool).

Requiring `cryptography` unconditionally would conflict with the "works in
any minimal Python environment" goal — the library pulls in OpenSSL FFI
bindings and can be awkward on restricted systems.

## Decision

Keep `cryptography>=44.0` in the `[crypto]` optional extras group of
`pyproject.toml`. The code:

- Detects availability at import time (`try: from cryptography... except ImportError`).
- Falls back to stdlib primitives for advanced upload payload handling (XOR+HMAC) and disables the
  Secure Notepad ECDH path entirely when unavailable.
- Logs a warning (not an error) when a feature is degraded due to missing
  deps.
- Marks tests that require `cryptography` with `@pytest.mark.skipif(not HAS_CRYPTOGRAPHY, ...)`.

## Consequences

### Positive

- `pip install exphttp` still works on any Python 3.10+; the minimal path
  serves files and supports advanced uploads with XOR handling.
- Enthusiasts who need AEAD/ECDH install with `pip install exphttp[crypto]`.
- CI matrix tests both with and without the extra, catching drift between
  code paths.

### Negative

- Two code paths to maintain for advanced upload encryption (baseline + AEAD).
- Test matrix gets a conditional dimension; 34 tests are skipped on the
  crypto-less path.
- Feature-parity warnings must be kept accurate as new features are added.
