# ADR-009: Secure Notepad durable-recovery boundary

- **Status:** accepted

## Context

Secure Notepad currently derives an AES-256-GCM key per session via ECDH and
stores note bodies on disk only as opaque encrypted blobs plus plaintext
metadata. The browser UI and example client keep the derived key in process
memory, and the server does not persist note decryption keys.

That model already provides a clear cryptographic boundary in practice, but the
repository does not yet have one explicit ADR saying whether durable recovery
is supported, deferred, or intentionally out of scope. Without that decision,
stored ciphertext plus metadata can be misread as an eventual recovery feature
instead of what it is today: an ephemeral encrypted scratchpad that can strand
data once the client-held session key is lost.

Durable recovery would also force product and security choices that do not fit
inside a small follow-up patch: how recovery secrets are created and stored,
whether the feature is single-device restore or multi-device sync, how metadata
privacy changes, how envelopes or wrapped keys rotate, and how rollback/replay
risks are tested.

## Decision

Durable Secure Notepad recovery is out of scope for the current product.

The maintained contract is:

1. the server stores encrypted note blobs and plaintext metadata, but not the
   client-derived AES key or other durable recovery material;
2. reloading the page, restarting the client, restarting the server, session
   expiry, or LRU session eviction can leave previously saved note bodies
   undecryptable by that client;
3. the HTTP and WebSocket Notepad flows are not a backup system, multi-device
   sync protocol, or server-side recovery feature;
4. the server exposes no API to decrypt, unwrap, export, or re-key stored note
   blobs after the client-held session key is gone.

Future durable-recovery work must not start until all of the following are
specified together:

1. a product contract for restore/sync behavior, device/account boundaries,
   conflict handling, and rollback expectations;
2. a cryptographic design covering envelope encryption or key wrapping, AEAD
   versioning, nonce handling, key rotation, and test vectors;
3. a recovery-secret model that does not silently turn the server into a
   plaintext recovery oracle;
4. a migration/backfill story for existing stored note blobs and metadata;
5. a threat model covering lost devices, stolen metadata, compromised servers,
   replay/rollback, and recovery abuse paths;
6. end-to-end tests and operator/user documentation that make the new trust
   boundary explicit.

## Consequences

### Positive

- Current docs can describe the actual Secure Notepad behavior without
  implying hidden recovery guarantees.
- Operators and users get a clear warning that persisted note blobs are not a
  substitute for durable encrypted storage.
- Any future recovery project now has an explicit design bar before runtime
  work begins.

### Negative

- Users who lose the client-held session key can lose the ability to decrypt
  previously stored note bodies even though the ciphertext remains on disk.
- Persisted note blobs may outlive the session that can decrypt them; this is a
  supported limitation rather than a recoverable-by-default workflow.

### Follow-up

- README, SECURITY, threat model, and API docs should reference this ADR when
  describing Secure Notepad persistence semantics.
- Any future recovery implementation should supersede this ADR rather than
  adding partial persistence or key-export behavior incrementally.
