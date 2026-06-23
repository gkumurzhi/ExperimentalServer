# ADR-008: Direct-peer client identity and trusted-proxy prerequisites

- **Status:** accepted

## Context

The runtime currently keys Basic Auth throttling on the accepted socket peer
address in `src/server.py`. That matches the simplest trust boundary the
process can actually verify: the direct TCP peer connected to the server.

At the same time, realistic exposed deployments often introduce a reverse
proxy, CDN, or ingress layer for TLS termination, request caps, routing, or
public host management. Several documents already mention proxy-side throttling
or untrusted forwarded headers, but the repository does not yet have one ADR
that defines the maintained client-identity boundary or the prerequisites for
ever changing it.

Without that decision record, there is a recurring risk that routine proxy or
deployment work will accidentally imply partial support for trusting
`Forwarded`, `X-Forwarded-For`, `X-Real-IP`, or vendor-specific client-IP
headers even though the runtime has no safe opt-in trust model for them today.

## Decision

The maintained client-identity boundary remains the direct TCP peer from the
accepted socket.

The application does not currently trust `Forwarded`, `X-Forwarded-For`,
`X-Real-IP`, or similar headers for authentication throttling, policy
decisions, or canonical client identity. Those headers are treated as
untrusted request metadata unless a future design explicitly changes that
contract.

When `exphttp` runs behind a reverse proxy, load balancer, CDN, or ingress,
operators must enforce per-client auth throttling and request/header/body size
limits in that front layer. In proxied topologies, the app-side Basic Auth
limiter and its `429` cooldown semantics apply to the proxy connection unless
the proxy blocks end users earlier.

Future trusted-proxy support is deferred. No implementation work should start
until all of the following land together:

1. an explicit opt-in trust configuration with narrow proxy allowlists or CIDR
   boundaries and safe defaults that remain off by default;
2. one canonical forwarded-client header policy with strict hop parsing and
   failure behavior for malformed or mixed-header chains;
3. threat-model coverage for direct exposure, bypass around the proxy, and
   mixed topologies where some paths are proxied and others are not;
4. end-to-end tests for direct, single-proxy, multi-proxy, malformed-header,
   and bypass cases;
5. observability semantics that distinguish direct peer identity from any
   asserted client identity in logs and metrics;
6. operator-facing deployment and rollback guidance that makes the trust
   prerequisites explicit.

## Consequences

### Positive

- The documented trust boundary now matches the current runtime behavior.
- Reverse-proxy guidance can point to one maintained decision instead of
  repeating slightly different wording in multiple docs.
- Future proxy work has a clear bar for what must be solved before header
  trust becomes an implementation task.

### Negative

- Operators behind a reverse proxy must duplicate some request-throttling and
  size-cap controls in the proxy layer because the application cannot derive a
  trustworthy end-user IP on its own.
- A future trusted-proxy feature cannot be added casually as a small flag; it
  requires dedicated design, testing, and observability work.

### Follow-up

- Operator-facing docs should reference this ADR when describing proxy
  deployments and Basic Auth throttling semantics.
- Any future trusted-proxy feature should supersede this ADR rather than
  weakening the direct-peer contract piecemeal.
