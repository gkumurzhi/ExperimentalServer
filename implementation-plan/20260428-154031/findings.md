# Normalized Findings
_Generated: 2026-04-28 15:40:31 MSK_

| Finding ID | Source | Severity | Area | Evidence | Root cause | Proposed outcome | Confidence |
|---|---|---:|---|---|---|---|---:|
| F-001 | project-analysis-report Critical & High #1; security-auditor | HIGH | Security | `/static/...` can resolve outside packaged UI assets | Static package resource path bypasses uploads resolver and lacks containment checks | Static paths are validated and confined to bundled asset root | High |
| F-002 | project-analysis-report Critical & High #2; performance/python/qa | HIGH | Performance | `_maybe_gzip_response()` reads streamed files into memory | Gzip post-processing converts `stream_path` to full body | Streamed files remain bounded-memory under gzip requests | High |
| F-003 | performance-engineer | HIGH | Performance | SMUGGLE reads/encodes full files and generated HTML | Feature has no source-size memory ceiling | SMUGGLE has explicit cap and bounded serving behavior | High |
| F-004 | websocket-engineer; qa; security | HIGH | WebSocket | Inbound unmasked client frames are accepted | Generic parser accepts server and client frames identically | Inbound parser requires client masking | High |
| F-005 | frontend-developer; python-pro | HIGH | Frontend/Packaging | `index.html` loads untracked `inspector.js` | Static asset introduced without tracking/package verification | Referenced UI assets are tracked or removed | High |
| F-006 | frontend-developer | HIGH | Frontend/Security | Raw/copy inspector exposes advanced-upload keys and payloads | Redaction not centralized before raw render/copy state | Sensitive fields are redacted before display/copy | High |
| F-007 | docker-expert | HIGH | Docker/Supply chain | .dockerignore misses runtime/secret-like files | Build context hygiene incomplete | Docker context excludes runtime data and secrets | High |
| F-008 | devops-engineer | HIGH | CI/Security | `pip-audit --disable-pip` likely mismatched to environment audit | Workflow uses incompatible audit mode | Security workflow runs a valid audit mode | High |
| F-009 | api-documenter | HIGH | Docs/API | SMUGGLE documented as direct HTML response | API docs do not match handler response | Docs describe JSON + `X-Smuggle-URL` flow | High |
| F-010 | api-documenter | HIGH | Docs/API | Global JSON error model is false | Docs overgeneralize endpoint error bodies | Docs or implementation has accurate error contract | High |
| F-011 | documentation-engineer; architect-reviewer | HIGH | Docs/Process | `CLAUDE.md` contains removed flags and unsafe path advice | AI-facing guidance stale | Guide is current or redirects to canonical docs | High |
| F-012 | python-pro | MEDIUM | Backend | Malformed request lines can reach dispatch | Parser swallows failures and exposes empty method/path | Invalid parse returns 400 before side effects | High |
| F-013 | security-auditor; qa | MEDIUM | Security | Advanced upload crypto failures can succeed | Decrypt failure/no-crypto AES not fail-closed | Crypto failures reject upload clearly | High |
| F-014 | security-auditor | MEDIUM | Security | Hidden uploads exposed through FETCH/SMUGGLE/DELETE | Hidden-file policy is method-specific | Policy enforced uniformly | High |
| F-015 | security-auditor; api-documenter | MEDIUM | CORS/API | Comma CORS emitted as invalid ACAO; headers/methods drift | CORS config not represented as browser-valid allowlist | CORS origin/method/header contract is valid | High |
| F-016 | websocket-engineer | MEDIUM | WebSocket | FIN/RSV/opcode/Host semantics missing | Parser lacks full protocol validation | Malformed frames/handshakes fail before side effects | High |
| F-017 | websocket-engineer; performance-engineer | MEDIUM | Reliability | Long-lived/slow WS can pin worker pool and buffers | No WS budget or partial-frame timeout | WS resources are bounded | High |
| F-018 | python-pro; performance-engineer | MEDIUM | Observability | Metrics undercount handler-produced failures | Error counter only increments for explicit exception flag | Metrics semantics are explicit and complete enough | High |
| F-019 | performance-engineer | MEDIUM | Performance | Uploads and base64 transports multiply memory | Receive/body/base64 paths buffer full payloads | Oversized and memory-heavy payloads are rejected earlier/capped | High |
| F-020 | devops/dependency-manager | MEDIUM | Tooling | Pre-commit/constraints/CI versions drift | Multiple partial toolchain authorities | Local and CI tool pins align | High |
| F-021 | dependency-manager/devops | MEDIUM | Dependencies | `uv.lock`, constraints, Dependabot, Python 3.14 policy drift | Dependency authority and update surfaces unclear | One policy and matching automation exist | High |
| F-022 | docker-expert | MEDIUM | Docker | Healthcheck/volume/digest/hardening gaps | Docker example assumes default runtime and manual refresh | Docker examples are explicit and safer | High |
| F-023 | frontend-developer | MEDIUM | Frontend/QA | UI ignores advanced capability, a11y/smoke gaps | UI state and tests do not reflect server capabilities | UI and smoke tests align with server state | High |
| F-024 | documentation/api-documenter | MEDIUM | Docs | Remaining docs drift: changelog, threat model, INFO/CORS/WS, ADR HMAC | Canonical docs stale despite mirror sync | Docs and mirrors match implementation | High |
| F-025 | architect-reviewer | MEDIUM | Data hygiene | `notes/` runtime data not ignored | Runtime data policy incomplete | Note runtime data ignored like uploads | High |
