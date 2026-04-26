<!-- Generated from ../SECURITY.md by tools/sync_docs.py. Edit SECURITY.md and rerun the sync tool. -->

# Security Policy

## Scope

ExperimentalHTTPServer is an **experimental** research-grade project. It is
intended for learning, CTF practice, and controlled red/blue team exercises —
not for untrusted internet exposure. Nothing in this document promises
production-grade assurances.

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

A full threat model lives in [`docs/threat-model.md`](threat-model.md).
High-level assumptions:

- **In scope:** path traversal, auth bypass, timing side channels on Basic
  Auth, WebSocket frame smuggling, Content-Length/Transfer-Encoding
  smuggling, TLS misconfiguration, advanced upload payload forgery.
- **Out of scope:** advanced traffic analysis of the advanced upload flow, timing
  attacks below microsecond resolution, DoS via resource exhaustion from
  authenticated users, vulnerabilities in `cryptography` / OpenSSL / Python
  stdlib (report upstream).

## Advanced Upload Caveats

Advanced upload is a transport convenience with optional payload obfuscation,
not a replacement for TLS or authentication:

- XOR + HMAC is *not* a substitute for authenticated encryption.
- Any unknown non-standard method carrying `d`/`data`, `X-D`, `X-D-0`, or
  `?d=` payload data is treated as an upload request.
- Payload placement in headers or URL parameters may be logged by upstream
  proxies; use JSON body transport for sensitive data and pair it with TLS.

Do not rely on advanced upload as the sole defense against a motivated attacker.

## Hardening Recommendations

When running the server outside a trusted lab:

- Always use `--tls` with a real certificate (Let's Encrypt or internal CA).
- Always use `--auth random` or supply a strong `user:password`.
- Use a dedicated `--dir` so `<dir>/uploads/` contains only files intended for this server.
- Bind to `127.0.0.1` unless external access is explicitly required.
- Place behind a reverse proxy with rate limiting and request-size limits.

## Known Limitations

See `CHANGELOG.md` under `### Security` for a log of past fixes and their
reference IDs (B01–B47).
