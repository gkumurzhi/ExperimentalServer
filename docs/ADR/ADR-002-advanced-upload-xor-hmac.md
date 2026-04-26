# ADR-002: Advanced upload payload protection — XOR + HMAC baseline with optional AES-GCM

- **Status:** accepted

## Context

Advanced upload allows clients to send encoded payloads through JSON bodies,
headers, chunked headers, or URL parameters. Some clients also need a stdlib-only
way to obfuscate payload bytes and detect accidental or malicious tampering.
The server must work in environments where installing `cryptography` is
impossible (air-gapped research VMs, minimal containers).

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
3. **Transport selection is explicit:** clients choose JSON body, header,
   chunked-header, or URL transport. Method names are not treated as secrets.

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
- Non-standard method names and payload placement do not defeat traffic
  analysis (timing, body sizes, TLS fingerprint).
- Advanced upload obfuscation is not a complete security layer. Users must
  layer TLS and auth on top for any real-world deployment.
