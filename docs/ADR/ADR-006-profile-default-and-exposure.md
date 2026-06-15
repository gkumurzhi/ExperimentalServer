# ADR-006: Profile default and exposure policy

- **Status:** accepted

## Context

The server currently defaults to the `lab` feature profile for compatibility.
That profile enables the full experimental surface, including advanced upload,
`SMUGGLE`, `NOTE`, WebSocket notes, upload clearing, and note clearing.

The analysis for the 2026-06 implementation plan recommended a safer
new-user path before changing runtime defaults or promoting distribution/API
tracks. The project also has explicit deployment guidance for localhost,
trusted labs, and external exposure, but the profile default, reverse-proxy
semantics, Docker status, and compatibility expectations need one recorded
decision.

## Decision

The supported profile direction is:

| Profile | First path |
|---|---|
| `serve` | Read-only sharing and inspection when uploads or mutations are not needed. |
| `workspace` | Normal file workspace with ordinary uploads and single-file deletes; this is the intended future default for new users. |
| `lab` | Explicit opt-in for experiments and compatibility with scripts that need advanced upload, `SMUGGLE`, `NOTE`, WebSocket notes, or clear operations. |

The current runtime default remains `lab` until the default migration stage.
Before that migration, documentation and release notes must tell operators to
pin `--profile lab` for scripts that rely on implicit experimental behavior.
The `lab` profile and the deprecated `--advanced-upload` alias remain
available as compatibility paths; the default migration must not remove those
capabilities.

External exposure is not a supported safe default. Binding to a public
interface, enabling TLS, or enabling Basic Auth is not enough on its own for
arbitrary internet exposure. Operators exposing the service outside localhost
or a controlled lab must provide the external-exposure baseline documented in
`SECURITY.md`, including real TLS, strong credentials, firewall allowlists
where possible, exact browser-origin policy, resource limits, monitoring, and
reverse-proxy request controls.

The application-side Basic Auth rate limiter keys failures on the direct TCP
peer IP address from the accepted socket. The server does not currently trust
or parse `Forwarded` or `X-Forwarded-For` headers. Reverse-proxy deployments
therefore must enforce proxy-side per-client auth/request throttling and
request-size limits unless a future trusted-proxy model is added.

The checked-in `Dockerfile` and `examples/docker/docker-compose.yml` are
operator convenience examples for local builds and topology experiments. They
are not a supported published artifact track. Published image policy,
rollback boundaries, and release automation belong to a later Docker stage.

## Consequences

### Positive

- New users get a clear safe-by-default direction before the CLI default
  changes.
- Existing automation has an explicit compatibility path: pass
  `--profile lab` when experimental methods are required.
- Reverse-proxy deployments cannot accidentally treat forwarded headers as a
  trusted client identity boundary.
- Docker examples remain usable without implying a supported image release
  lifecycle.

### Negative

- The documented future direction and the current runtime default temporarily
  differ.
- Operators behind a reverse proxy must configure per-client controls in the
  proxy until trusted-proxy support exists in the application.
- Scripts that rely on implicit `lab` behavior need a migration note and an
  explicit profile flag before the default changes.

### Follow-up

- STAGE-003 can centralize capability policy around this profile boundary.
- STAGE-004 may change the CLI default only after compatibility notes are in
  place and tests prove `--profile lab` preserves the legacy surface.
- STAGE-008 may promote or defer Docker artifact support based on this
  operator-convenience status.
