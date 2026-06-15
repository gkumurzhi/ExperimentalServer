# product-manager Report
_Generated: 2026-06-14 23:36:55 Europe/Moscow_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/analysis-plan.md_

## Summary
Recommendation: make the next dominant path **safe-by-default server / file workspace**, not secure workspace, API platform, or full distribution product yet.

Default profile for new users should become **`workspace`**, with `lab` kept as explicit opt-in for compatibility and experiments. `workspace` preserves the main user value: upload, browse, download, and delete files, while disabling lab-only features like advanced upload fallback, `SMUGGLE`, `NOTE`, WebSocket notes, and destructive clears. Evidence: `lab` is still the code and CLI default in [src/features.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/features.py:23) and [README.md](/home/user/PycharmProjects/ExperimentalHTTPServer/README.md:184), while profiles already cleanly separate `serve`, `workspace`, and `lab` in [src/features.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/features.py:62).

Core value: safe local file workspace plus operational guardrails. Experimental examples: advanced upload, unknown-method fallback, `SMUGGLE`, XOR tooling, and Secure Notepad/WebSocket until durability is decided.

## Documentation Checks
Read-only checks only. I read the requested plan, README, API, SECURITY, CHANGELOG, architecture doc, previous plan artifacts, stage status/reports, and previous analysis report.

I verified `python tools/sync_docs.py --check` still fails:
`API.md -> docs/api.md` and `CONTRIBUTING.md -> docs/contributing.md` are out of sync. This matches the current source plan at [analysis-plan.md](/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/analysis-plan.md:57).

I did not re-query Context7 because the recommendation does not depend on new library/platform semantics. The parent plan already records Context7 checks for cryptography, pytest, Docker, and Python release status in [analysis-plan.md](/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/analysis-plan.md:67).

## Detailed Findings
The previous 11-stage remediation plan is genuinely closed: storage quotas, auth-file support, profiles, CORS policy, Docker readiness, release artifacts, package identity, and WebSocket ops are all marked `CLOSED` in [stage-status.md](/home/user/PycharmProjects/ExperimentalHTTPServer/implementation-plan/20260525-133607/stage-status.md:5).

The product still presents as a trusted-lab tool. SECURITY says the project is experimental and not for untrusted internet exposure in [SECURITY.md](/home/user/PycharmProjects/ExperimentalHTTPServer/SECURITY.md:5), while README external-exposure guidance requires proxy rate limits, monitoring, firewall allowlists, and exact CORS in [README.md](/home/user/PycharmProjects/ExperimentalHTTPServer/README.md:249).

The codebase is more mature than that positioning: package name is `exphttp`, typed, beta-classified, with runtime deps and console script in [pyproject.toml](/home/user/PycharmProjects/ExperimentalHTTPServer/pyproject.toml:5), CI covers Python 3.10-3.13 in [.github/workflows/ci.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/.github/workflows/ci.yml:26), and release artifacts include wheel/sdist/SBOM/attestations in [.github/workflows/release.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/.github/workflows/release.yml:51).

Secure Notepad should not be marketed as durable secure notes yet. API explicitly says current keys are session-bound and not durably recoverable in [API.md](/home/user/PycharmProjects/ExperimentalHTTPServer/API.md:467), and `sessionId` is audit-only, not authorization, in [API.md](/home/user/PycharmProjects/ExperimentalHTTPServer/API.md:535).

API/client-platform work is premature. Error contracts are mixed by design, with JSON, text, empty bodies, close-without-body, endpoint-specific JSON, and WebSocket frames all documented in [API.md](/home/user/PycharmProjects/ExperimentalHTTPServer/API.md:7).

Distribution/ops is viable but should be "next after default safety," not the dominant path. The release lane builds and attests artifacts but does not publish to PyPI or a registry, explicitly documented in [README.md](/home/user/PycharmProjects/ExperimentalHTTPServer/README.md:973).

## Issues Found
P0: Docs mirror drift is present now. Fix before any roadmap work.

P0: `lab` default conflicts with safe new-user posture. `lab` enables full experimental surface in [src/features.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/features.py:89), while docs warn external users to avoid broad exposure.

P1: Product identity is split between "experimental research-grade" and "packaged beta server." This increases support and adoption risk.

P1: Notepad has high expectation risk: "Secure Notepad" sounds durable, but recovery is intentionally absent.

P1: Reverse-proxy/rate-limit story remains policy-only. SECURITY recommends proxy rate limiting in [SECURITY.md](/home/user/PycharmProjects/ExperimentalHTTPServer/SECURITY.md:103), but app-level trusted proxy identity is still an open backlog item in [backlog.md](/home/user/PycharmProjects/ExperimentalHTTPServer/implementation-plan/20260525-133607/backlog.md:5).

P2: Python support cap needs a dated policy. Metadata is `<3.14` in [pyproject.toml](/home/user/PycharmProjects/ExperimentalHTTPServer/pyproject.toml:11), and README says it stays capped until CI checks Python 3.14 in [README.md](/home/user/PycharmProjects/ExperimentalHTTPServer/README.md:919).

## Concrete Recommendations
Ship now: fix docs mirror drift, update CHANGELOG/release notes, and document the intended profile-default migration. No feature expansion.

Short term: switch the new-user default from `lab` to `workspace` in a migration-visible release. Acceptance criteria: `exphttp` reports `profile: workspace`; ordinary upload/delete work; `advanced_upload`, `smuggle`, `note_http`, `websocket_notes`, and clears are false; `--profile lab` preserves old behavior; browser smoke covers default `workspace` and explicit `lab`; docs sync passes.

Medium term: harden the safe server path: module-specific test gates for parser/auth/CORS/storage/Notepad/WebSocket, Python 3.14 support decision, UI/a11y review for capability-disabled states, and explicit reverse-proxy stance.

Long term: choose one strategic expansion: durable secure workspace, public distribution/ops product, or stable API/client platform. Do not pursue all three at once.

Tradeoff: changing the default can break scripts relying on implicit advanced upload or Notepad. Mitigation: keep `--profile lab`, keep the deprecated `--advanced-upload` alias for now, and call the change out in README/API/CHANGELOG.

## Quick Wins
Regenerate docs mirrors with `tools/sync_docs.py --write` in a normal implementation pass.

Make README quick start show `--profile workspace` or explain the upcoming default explicitly.

Add a short profile decision table: `serve` for read-only sharing, `workspace` for normal file workspace, `lab` for experiments.

Move CHANGELOG out of the large `[Unreleased]` pile or add a dated migration section; it currently begins at [CHANGELOG.md](/home/user/PycharmProjects/ExperimentalHTTPServer/CHANGELOG.md:7).

## Deeper Improvements
Durable Notepad only after a product/security decision on recovery, re-keying, metadata privacy, and user authorization.

API/client platform only after normalizing error envelopes and versioning HTTP/WebSocket contracts.

Public PyPI/GHCR publishing only after deciding maintainer SLA, vulnerability response, Python support window, and rollback process.

Observability only if distribution/ops becomes real: current `/metrics` is useful locally, but not yet an operator-ready alerting story.

## Open Questions
Product owner: approve `workspace` as the next default, or require `lab` compatibility for one more release?

Maintainer/security: is untrusted internet exposure unsupported, proxy-only, or a first-class target?

Product owner + security/crypto: is Notepad an ephemeral encrypted scratchpad or durable secure notes?

Maintainer/devops: should release artifacts publish to PyPI/GHCR/GitHub Releases, or stay manual?

Maintainer: when to add Python 3.14 and when to deprecate 3.10/3.11?

Product/design: should the bundled UI become a real product surface with accessibility acceptance criteria, or remain a lab convenience?
