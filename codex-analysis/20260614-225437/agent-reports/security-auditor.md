# security-auditor Report
_Generated: 2026-06-14 23:43:14 Europe/Moscow_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/analysis-plan.md_

## Summary
Read-only static audit completed. No files modified and no tests run.

Scope analyzed: the requested security paths plus supporting CLI/Docker/docs/tests for profile, CORS/origin, auth limiting, WebSocket, Notepad, SMUGGLE, and upload behavior.

Overall: current controls are coherent for the documented localhost/trusted-lab audience, but there are two medium operational risks and one low defense-in-depth gap. The Notepad durability question is not a current vulnerability, but it is a high-risk future design area.

## Documentation Checks
`SECURITY.md` clearly says this is experimental/trusted-lab software, not production-hardened, and recommends TLS, auth, narrow profiles, reverse-proxy limits, and exact CORS origins.

`API.md` documents profiles, Notepad non-recoverability, WebSocket origin rules, wildcard CORS read-only behavior, and browser-origin mutation guard.

`docs/threat-model.md` says auth rate limiting is IP-based, but it does not define that this means direct TCP peer IP only, nor a trusted-proxy model.

No additional Context7 lookup was needed; I relied on the parent's crypto and Docker checks.

## Detailed Findings
**F1 - Medium: `lab` default is acceptable only for explicit lab-first usage, not as a general packaged/container default.**

Evidence: `DEFAULT_PROFILE = "lab"` in [src/features.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/features.py:23). `lab` enables advanced upload, SMUGGLE, NOTE, note delete/clear, upload clear, and WebSocket notes in [src/features.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/features.py:89). CLI default also uses `lab` in [src/cli.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/cli.py:140). Docker defaults bind `0.0.0.0` and do not set profile/auth/TLS in [Dockerfile](/home/user/PycharmProjects/ExperimentalHTTPServer/Dockerfile:66).

Attack path: operator runs the default image with a published port and no explicit `--profile`, `--auth`, or TLS. Remote users can reach the full lab surface.

Impact: unauthorized upload/delete/clear operations, Notepad blob manipulation, SMUGGLE artifact creation, and storage exhaustion.

Prerequisites: network reachability and no external auth/firewall/proxy restriction.

**F2 - Medium: auth rate limiting is direct-socket-IP based, but reverse-proxy deployments are under-specified.**

Evidence: `_authenticate_request` keys rate limiting on `client_address[0]` in [src/server.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/server.py:798). `AuthRateLimiter` is IP-keyed in [src/security/auth.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/security/auth.py:183). Docs recommend reverse-proxy rate limiting in [SECURITY.md](/home/user/PycharmProjects/ExperimentalHTTPServer/SECURITY.md:103), and nginx examples set forwarded headers, but the app does not consume them.

Attack path: behind a proxy, all users share the proxy peer IP. One attacker can trigger app-side lockout for everyone, while the app cannot enforce per-client brute-force limits unless the proxy does.

Impact: availability loss for legitimate users and weaker app-local brute-force control.

Prerequisites: Basic Auth enabled behind a reverse proxy without correct proxy-side per-client limiting.

**F3 - Low: WebSocket destructive note operations are not independently capability-checked after upgrade.**

Evidence: WebSocket admission only checks `websocket_notes` in [src/server.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/server.py:1067). After upgrade, `delete` and `clear` call note deletion/clear directly in [src/handlers/notepad.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/notepad.py:312), while HTTP NOTE delete/clear explicitly checks `note_delete` and `note_clear` in [src/handlers/notepad.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/notepad.py:93).

Current exploitability: low, because named profiles only enable WebSocket in `lab`, where delete/clear are also enabled.

Future attack path: a future/custom profile enables WebSocket notes but intends to disable destructive operations.

Impact: unintended note deletion/clear over WebSocket.

**F4 - Design risk: durable Notepad recovery cannot safely be added by persisting the current session model.**

Evidence: ECDH sessions are in-memory, TTL/LRU-bound, and keyed by random session IDs in [src/security/keys.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/security/keys.py:56). Session IDs are explicitly audit-only, not authorization or recovery tokens, in [src/handlers/notepad.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/notepad.py:45). Docs state notes are not durably recoverable in [API.md](/home/user/PycharmProjects/ExperimentalHTTPServer/API.md:467).

Risk: persisting session AES keys, reusing session IDs as recovery handles, or making the server able to unwrap all note keys would regress the current client-side encryption boundary.

## Issues Found
1. Medium: broad `lab` default is risky for packaged/container exposure.
2. Medium: no explicit trusted-proxy/client-IP model for auth throttling.
3. Low: WebSocket destructive note operations lack message-level capability checks.
4. Future high-risk design area: durable Notepad recovery needs a new crypto design, not persistence of current session keys.

## Concrete Recommendations
Keep direct socket IP as the app default. Do not trust `X-Forwarded-For` unless a future `--trusted-proxy-cidr` model is added.

For proxied deployments, document proxy-side per-client auth rate limits as required, and state that app-side auth limits key on the proxy IP.

Make Docker safer by default: set `--profile serve` or `--profile workspace` in the image/Compose default, or require an explicit profile for externally published examples.

Add WebSocket message checks for `note_delete` and `note_clear`, matching HTTP NOTE behavior.

For durable Notepad recovery, design envelope encryption: per-note data keys, unique AES-GCM nonces per encryption, versioned metadata, client-held recovery secret or passphrase-derived wrapping key, and migration/test vectors.

## Quick Wins
Add a short "Client IP and proxies" section to `SECURITY.md`.

Add regression tests for WebSocket `delete`/`clear` when `websocket_notes=True` but destructive note caps are false.

Make Docker examples pass an explicit `--profile`.

Add startup warning when `profile=lab`, host is non-loopback, and auth is disabled.

## Deeper Improvements
Introduce an explicit trusted-proxy configuration only if the project intends to support hosted reverse-proxy deployments.

Plan a compatibility path to move the default profile from `lab` to `workspace` or `serve`.

Write a Notepad durability ADR before implementing recovery.

## Open Questions
Should `lab` remain the CLI default for 2.x compatibility?

Should the Docker image default be safer than the CLI default?

Is reverse-proxy deployment officially supported by the app, or should rate limiting remain fully proxy-owned?

Is Secure Notepad meant to stay ephemeral, or become a durable encrypted workspace?
