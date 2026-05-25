# Security Policy

## Scope

ExperimentalHTTPServer is an **experimental** research-grade project. It is
intended for learning, CTF practice, and controlled red/blue team exercises —
not for untrusted internet exposure. Nothing in this document promises
production-grade assurances.

## Operating Modes

- **Localhost:** the default bind address is `127.0.0.1`; use this for
  single-machine experiments.
- **Trusted lab:** binding to `0.0.0.0` is appropriate only on a controlled
  network with TLS, authentication, and firewall/NAT restrictions.
- **External exposure:** do not treat `--tls`, `--auth`, or a public bind as a
  complete internet hardening story. Use the baseline below and review the
  threat model before exposing the service outside a trusted lab.

## Supported Versions

| Version | Security fixes |
|---------|----------------|
| `2.x`   | ✅ Supported    |
| `< 2.0` | ❌ End of life |

Only the latest minor release on the `main` branch receives security fixes.

## Reporting a Vulnerability

**Do not open public GitHub issues for security vulnerabilities.**

Instead:

1. Open a [GitHub Security Advisory](https://github.com/gkumurzhi/ExperimentalServer/security/advisories/new)
   (*Report a vulnerability*) — this keeps the report private until a fix ships.
2. Alternatively, contact the maintainer privately through the repository
   `Issues` page by requesting a private channel.

Please include:

- Affected version / commit hash
- Minimal reproduction (request, command line, expected vs. actual behavior)
- Impact assessment (confidentiality / integrity / availability)
- Optional: proposed mitigation

### Response SLA (best effort)

| Step               | Target          |
|--------------------|-----------------|
| First response     | 5 business days |
| Triage & severity  | 10 business days|
| Fix / mitigation   | 30 business days|
| Public disclosure  | after fix ships |

Coordinated disclosure is preferred. Credit will be given in the CHANGELOG
unless the reporter requests anonymity.

## Threat Model

A full threat model lives in [`docs/threat-model.md`](docs/threat-model.md).
High-level assumptions:

- **In scope:** path traversal, auth bypass, timing side channels on Basic
  Auth, WebSocket frame smuggling, Content-Length/Transfer-Encoding
  smuggling, TLS misconfiguration, advanced upload payload forgery.
- **Out of scope:** advanced traffic analysis of the advanced upload flow, timing
  attacks below microsecond resolution, DoS via resource exhaustion from
  authenticated users, vulnerabilities in `cryptography` / `acme` /
  PyOpenSSL / Python stdlib (report upstream).

## Advanced Upload Caveats

Advanced upload is a built-in transport convenience with optional payload
obfuscation, not a replacement for TLS or authentication:

- XOR + HMAC is *not* a substitute for authenticated encryption; the HMAC
  validates payload bytes only, not filename or transport metadata.
- Unknown non-standard methods carrying `d`/`data`, `X-D`, `X-D-0`, or `?d=`
  payload data are treated as upload requests.
- Payload placement in headers or URL parameters may be logged by upstream
  proxies; use JSON body transport for sensitive data and pair it with TLS.

Do not rely on advanced upload as the sole defense against a motivated attacker.

## Hardening Recommendations

When running the server outside a trusted lab:

- Always use `--tls` with a real certificate (Let's Encrypt or internal CA).
- Use `--auth random` only in an interactive terminal; for services,
  containers, and CI pass an explicit strong `user:password` from a secret
  manager.
- Use a dedicated `--dir` so `<dir>/uploads/` contains only files intended for this server.
- Bind to `127.0.0.1` unless external access is explicitly required.
- Place behind a reverse proxy with rate limiting and request-size limits.
- Configure an exact `--cors-origin` for a trusted browser UI; avoid
  `--cors-origin *` on internet-facing deployments.

### External exposure baseline

Before exposing the service to untrusted networks, require all of: real TLS,
strong Basic Auth credentials, a dedicated data directory, firewall allowlists
where possible, reverse-proxy rate limiting, reverse-proxy request/header/body
size caps, an explicit `--body-memory-budget` sized for available RAM,
explicit slow-body settings (`--body-idle-timeout`, `--body-timeout`, and
optionally `--body-min-rate`), monitoring of `/metrics`, and an exact
browser-origin policy for any separate UI origin. Keep
`--stream-send-idle-timeout` and `--stream-send-timeout` enabled for exposed
file downloads so slow readers cannot hold worker threads indefinitely.

## Known Limitations

See `CHANGELOG.md` under `### Security` for a log of past fixes and their
reference IDs (B01–B47).
