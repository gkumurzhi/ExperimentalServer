# ADR-010: Legacy v0 client boundary and API v1 entry criteria

- **Status:** accepted

## Context

The repository already exposes a usable HTTP/WebSocket surface, but it is a
custom legacy contract built around profile-gated methods and `PING`
capability discovery rather than a versioned public API. `API.md` documents
that status directly, yet there is still no single ADR that answers the
adjacent product question: which clients are supported today, and what would
have to be true before `/api/v1` or an official SDK becomes real work?

Without that decision record, the built-in browser UI, README snippets, or
example scripts can be misread as a broad public-client commitment. That would
be inaccurate. The current surface mixes legacy error shapes, lab-only methods,
profile-gated capabilities, and operator-owned deployment assumptions that do
not automatically translate into a stable public SDK story.

## Decision

The maintained client boundary today is the legacy v0 surface documented in
`API.md` and discovered at runtime through `PING` plus the selected profile.

Supported consumers today are:

1. the built-in browser UI that ships with the server;
2. bundled examples and tests that exercise the documented legacy surface;
3. operator-owned scripts or integrations that can tolerate the narrow v0
   compatibility contract and use `PING` discovery for feature gating.

What is **not** supported today:

1. `/api/v1` endpoints or any versioned API prefix;
2. an official SDK/client library with its own compatibility or release
   cadence promise;
3. a public-client program that treats every legacy lab-only method or
   endpoint shape as a future stable API candidate.

Any future `/api/v1` or official SDK work is deferred until all of the
following are decided together:

1. a versioning and discovery strategy for stable public clients;
2. normalized error and idempotency semantics instead of mixed legacy response
   bodies;
3. a clear feature set for v1, including which current lab-only flows remain
   experimental and which ones graduate;
4. a security and deployment model for public/browser clients that remains
   compatible with ADR-007, ADR-008, and ADR-009;
5. ownership, release cadence, compatibility guarantees, and test coverage for
   any official SDK/client artifact;
6. a migration story from legacy v0 integrations to the approved v1 surface.

## Consequences

### Positive

- API and README docs can stay honest about the current surface without
  implying a roadmap that maintainers have not committed to.
- External integrators get a clear signal that `PING` discovery and release
  notes are the safe way to consume the legacy surface today.
- Future v1 or SDK work now has an explicit design and ownership bar before
  runtime implementation starts.

### Negative

- Third-party clients must own more compatibility testing themselves because
  there is no official SDK or public-client support program yet.
- Legacy lab-only features remain available but are explicitly not promised as
  automatic v1 building blocks.

### Follow-up

- API, README, and SECURITY docs should reference this ADR when describing the
  current client boundary.
- Any future versioned API or SDK plan should supersede this ADR rather than
  incrementally widening the v0 compatibility promise.
