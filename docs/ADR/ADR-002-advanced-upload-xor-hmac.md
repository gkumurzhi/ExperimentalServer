# ADR-002: Advanced upload payload protection — XOR + HMAC baseline with optional AES-GCM

- **Status:** accepted; dependency-policy portions superseded by
  [ADR-003](ADR-003-cryptography-optional.md)

## Context

Advanced upload allows clients to send encoded payloads through JSON bodies,
headers, chunked headers, or URL parameters. Early versions also needed a
stdlib-only way to obfuscate payload bytes and detect accidental or malicious
tampering. The default runtime now includes `cryptography`; the XOR+HMAC path is
kept as a compatibility baseline, not as a dependency-policy requirement.

Requirements:

- Preserve the existing XOR+HMAC wire format.
- Provide authenticity, not just confidentiality (detect tampering).
- Accept an upgrade path to modern AEAD when the library is available.

## Decision

1. **Baseline (stdlib):** XOR-stream against a key derived from a shared
   secret, followed by an HMAC-SHA256 tag over the payload ciphertext bytes.
   This gives payload integrity and rudimentary confidentiality; it is **not**
   a substitute for AEAD and does not authenticate filename or transport
   metadata.
2. **Upgrade:** with the runtime `cryptography` dependency, the upload path uses
   AES-256-GCM with a random 12-byte nonce; wire format
   carries a version byte so both clients and the server can distinguish
   baseline vs. AEAD payloads.
3. **Transport selection is explicit:** clients choose JSON body, header,
   chunked-header, or URL transport. Method names are not treated as secrets.

## Consequences

### Positive

- Existing XOR+HMAC clients remain compatible.
- The wire format is versioned (`src/security/crypto.py`), so future
  algorithms can be added without breaking existing clients.
- HMAC prevents silent corruption of uploaded payload bytes when the client
  supplies a tag.

### Negative — explicitly out of scope

- XOR+HMAC is **not IND-CPA secure**. A motivated attacker who captures
  multiple encrypted uploads with known plaintext can recover the key.
  Document this in `SECURITY.md` and `docs/threat-model.md`.
- Non-standard method names and payload placement do not defeat traffic
  analysis (timing, body sizes, TLS fingerprint).
- Advanced upload obfuscation is not a complete security layer. Users must
  layer TLS and auth on top for any real-world deployment.
