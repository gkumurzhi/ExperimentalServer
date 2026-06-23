<!-- Generated from ../SECURITY.md by tools/sync_docs.py. Edit SECURITY.md and rerun the sync tool. -->

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

A full threat model lives in [`docs/threat-model.md`](threat-model.md).
High-level assumptions:

- **In scope:** path traversal, auth bypass, timing side channels on Basic
  Auth, WebSocket frame smuggling, Content-Length/Transfer-Encoding
  smuggling, TLS misconfiguration, advanced upload payload forgery.
- **Out of scope:** advanced traffic analysis of the advanced upload flow, timing
  attacks below microsecond resolution, DoS via resource exhaustion from
  authenticated users, vulnerabilities in `cryptography` / `acme` /
  PyOpenSSL / Python stdlib (report upstream).

## Secure Notepad durability boundary

Secure Notepad stores encrypted note blobs plus plaintext metadata, but it does
not persist the client-derived AES key or other durable recovery material.
Reloading the page, restarting the client or server, session expiry, or LRU
session eviction can strand previously saved note bodies even though the
ciphertext remains on disk.

ADR-009 keeps durable recovery out of scope for now. Current HTTP and
WebSocket Notepad flows are not a backup system, multi-device sync protocol, or
server-side plaintext recovery feature. Any future recovery work would need a
separate envelope-encryption/key-wrapping design, a recovery-secret model,
migration rules for existing blobs, threat-model coverage, and end-to-end
tests before implementation starts.

## API/client support boundary

The current HTTP/WebSocket surface is a legacy v0 contract, not a versioned
public API program. The built-in browser UI, bundled examples, and
operator-owned scripts are reference consumers of that surface, but they do not
constitute an official SDK or a promise of broad public-client compatibility.

ADR-010 defers `/api/v1` and any official SDK/client commitment until
versioning, normalized error/idempotency semantics, feature selection,
security/deployment expectations, ownership, and migration rules are approved
together.

## Advanced Upload Caveats

Advanced upload is a built-in transport convenience with optional payload
obfuscation, not a replacement for TLS or authentication:

- Advanced upload is disabled by default and enabled only by the `lab` feature
  profile. Prefer `--profile serve` for read-only sharing and the default
  `--profile workspace` for normal upload/delete workspaces.
- `SMUGGLE` is also `lab` only. Treat it as a temporary operator-owned artifact
  generator for controlled demo/inspection flows, not as sanctioned bypass or
  third-party delivery guidance. The safe builder is intentionally closed: it
  only allows the fixed extensions `txt`, `bin`, `dat`, `zip`, and `pdf`,
  only renders the fixed presets `direct`, `card_manual`, and `card_auto`, and
  does not permit arbitrary HTML, CSS, JavaScript, external redirects, or
  deceptive prompts. Keep the visible lab/test-artifact marker enabled unless
  you are validating the explicit `show_notice=0` contract in an internal test.
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
  containers, and CI mount a secret-manager file containing one
  `user:password` line and pass it with `--auth-file`.
- Use a dedicated `--dir` so `<dir>/uploads/` contains only files intended for this server.
- Select the narrowest `--profile` that supports the workflow; avoid `lab` for
  externally reachable services unless experimental methods are required.
- Bind to `127.0.0.1` unless external access is explicitly required.
- Prefer `--config` for services and run `exphttp --config <file>
  --check-config` before enabling a unit/container. For direct public exposure,
  set `public_direct = true` so startup validation requires real TLS,
  `auth_file`, explicit memory budget, enabled timeouts, non-lab profile, and
  no wildcard write CORS.
- For Docker, keep the default Compose plain HTTP publication on host loopback
  and use mounted secret files with `--auth-file` for TLS/auth profiles. The
  `deploy/docker/docker-compose.public-direct.yml` preset uses the published
  GHCR image, mounted INI config, and Docker secrets.
- Place behind a reverse proxy with per-client rate limiting and request-size
  limits when the service is exposed beyond localhost or a trusted lab.
- Configure an exact `--cors-origin` for a trusted browser UI. Wildcard
  `--cors-origin *` is read-only CORS and does not authorize browser writes or
  WebSocket upgrades.
- Basic Auth rate limiting in the app keys failures by the direct TCP peer IP
  address from the accepted socket. The app does not trust `Forwarded` or
  `X-Forwarded-For` headers, so proxied deployments need proxy-side per-client
  auth/request throttling and request-size limits in the front layer.

ADR-008 keeps client identity at that accepted-socket peer boundary. The app
does not trust `Forwarded`, `X-Forwarded-For`, `X-Real-IP`, or similar headers
for throttling or policy decisions. In proxied deployments, app-side `401` and
`429` behavior therefore reflects the proxy connection unless the proxy blocks
end users earlier.

Any future trusted-proxy support is deferred until a dedicated opt-in design
lands with narrow proxy allowlists, one canonical forwarded-header policy,
mixed-topology threat-model coverage, end-to-end tests, and observability that
distinguishes direct peer identity from asserted client identity.

### External exposure baseline

Before exposing the service to untrusted networks, require all of: real TLS,
strong Basic Auth credentials, a dedicated data directory, firewall allowlists
where possible, reverse-proxy per-client throttling, reverse-proxy
request/header/body size caps, an explicit `--body-memory-budget` sized for
available RAM, explicit slow-body settings (`--body-idle-timeout`,
`--body-timeout`, and optionally `--body-min-rate`), monitoring of `/metrics`,
and an exact browser-origin policy for any separate UI origin. Keep
`--stream-send-idle-timeout` and `--stream-send-timeout` enabled for exposed
file downloads so slow readers cannot hold worker threads indefinitely.
For containers, align Docker memory/CPU/PID/file-descriptor limits with
`--workers`, `--max-size`, `--body-memory-budget`, and the upload/notepad/
SMUGGLE storage quota flags. Protect ACME state volumes as secret certificate
material and schedule controlled restarts before certificate expiry so
startup-time renewal can run.

The root Dockerfile and example Compose file are local/operator examples.
Tagged releases publish the `exphttp` PyPI package and the
`ghcr.io/gkumurzhi/exphttp` image with provenance/SBOM settings in the release
workflow, but deployment topology remains operator-owned. Treat
`exphttp:local` as a local build and review the Compose topology before
adapting it to an exposed environment. The checked-in Docker commands use the
app `workspace` profile explicitly; change to `serve` for read-only containers
and use `lab` only in controlled labs with TLS/Auth, firewall controls,
proxy-side throttling, and resource limits. The ACME Compose profile exposes
public ports for HTTP-01 and HTTPS and requires a Basic Auth secret.

## Known Limitations

See `CHANGELOG.md` under `### Security` for a log of past fixes and their
reference IDs (B01–B47).
