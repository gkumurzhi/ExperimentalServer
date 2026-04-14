# ADR-002: OPSEC cipher — XOR + HMAC baseline with optional AES-GCM

- **Status:** accepted

## Context

OPSEC mode aims to make uploaded files *unreadable to a passive observer who
captures traffic* without requiring a separate TLS termination. The server
must work in environments where installing `cryptography` is impossible (air-
gapped research VMs, minimal containers).

Requirements:

- Run with stdlib only.
- Provide authenticity, not just confidentiality (detect tampering).
- Accept an upgrade path to modern AEAD when the library is available.

## Decision

1. **Baseline (stdlib):** XOR-stream against a key derived from a shared
   secret, followed by an HMAC-SHA256 tag over ciphertext + metadata. This
   gives integrity and rudimentary confidentiality; it is **not** a
   substitute for AEAD.
2. **Upgrade (optional):** when `cryptography>=44.0` is available, the
   upload path uses AES-256-GCM with a random 12-byte nonce; wire format
   carries a version byte so both clients and the server can distinguish
   baseline vs. AEAD payloads.
3. **Method names are randomised at startup** so intent is not readable
   from access logs; names are persisted to `.opsec_config.json` for the
   client.

## Consequences

### Positive

- Zero external deps in the common case; AES-GCM is an opt-in upgrade.
- The wire format is versioned (`src/security/crypto.py`), so future
  algorithms can be added without breaking existing clients.
- HMAC prevents silent corruption of uploaded bytes.

### Negative — explicitly out of scope

- XOR+HMAC is **not IND-CPA secure**. A motivated attacker who captures
  multiple encrypted uploads with known plaintext can recover the key.
  Document this in `SECURITY.md` and `docs/threat-model.md`.
- Random method names obscure intent but do not defeat traffic analysis
  (timing, body sizes, TLS fingerprint) — nginx masquerading headers are
  decorative.
- OPSEC mode is *obfuscation*, not *cryptographic secrecy*. Users must
  layer TLS and auth on top for any real-world deployment.
