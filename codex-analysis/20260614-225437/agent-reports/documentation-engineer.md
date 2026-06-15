# documentation-engineer Report
_Generated: 2026-06-15 00:11:11 Europe/Moscow_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260614-225437/analysis-plan.md_

## Summary
Read-only documentation-engineering audit completed. Boundary analyzed: root-canonical docs (`API.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`) -> generated MkDocs mirrors under `docs/` via `tools/sync_docs.py` -> stale-doc guard -> CI/MkDocs docs job. No files modified.

Primary friction: generated docs drift. `python tools/sync_docs.py --check` fails for `API.md -> docs/api.md` and `CONTRIBUTING.md -> docs/contributing.md`. `python tools/check_stale_docs.py` passes.

## Documentation Checks
- Read the source plan and completed product/API/security/architecture/QA reports.
- Read canonical docs, MkDocs pages, sync/stale tooling, CI docs workflow, PR template, release workflow, and closed implementation-plan artifacts.
- Validated failure path: `python tools/sync_docs.py --check` fails.
- Validated normal stale-contract path: `python tools/check_stale_docs.py` passes.
- Did not use Context7; recommendations are repo-local and do not depend on current external platform docs.
- Did not run `mkdocs build --strict` because it writes build output; run it after mirror regeneration.

## Detailed Findings
The immediate regeneration targets are `docs/api.md` and `docs/contributing.md`. The mirror mapping is defined in [tools/sync_docs.py](/home/user/PycharmProjects/ExperimentalHTTPServer/tools/sync_docs.py:23), and the check reports only those two pairs.

`docs/api.md` is missing newer WebSocket docs that exist in canonical [API.md](/home/user/PycharmProjects/ExperimentalHTTPServer/API.md:55), including WebSocket admission/frame timeout behavior and internal-error close semantics at [API.md](/home/user/PycharmProjects/ExperimentalHTTPServer/API.md:739).

`docs/contributing.md` has stale installed-package wording: canonical [CONTRIBUTING.md](/home/user/PycharmProjects/ExperimentalHTTPServer/CONTRIBUTING.md:117) now says installed-package smoke fails if package imports resolve to the checkout.

Safe/lab/production separation is mostly present but unevenly surfaced. README documents `--profile` defaulting to `lab` at [README.md](/home/user/PycharmProjects/ExperimentalHTTPServer/README.md:184), profile meanings at [README.md](/home/user/PycharmProjects/ExperimentalHTTPServer/README.md:203), and operating modes at [README.md](/home/user/PycharmProjects/ExperimentalHTTPServer/README.md:242). SECURITY is clearer: it says the project is not for untrusted internet exposure at [SECURITY.md](/home/user/PycharmProjects/ExperimentalHTTPServer/SECURITY.md:5), warns to avoid `lab` externally at [SECURITY.md](/home/user/PycharmProjects/ExperimentalHTTPServer/SECURITY.md:98), and defines an external baseline at [SECURITY.md](/home/user/PycharmProjects/ExperimentalHTTPServer/SECURITY.md:108).

The first-path docs still lead with full experimental capabilities. `docs/index.md` highlights `NOTE`, `SMUGGLE`, WebSocket, and advanced upload before profile context at [docs/index.md](/home/user/PycharmProjects/ExperimentalHTTPServer/docs/index.md:13). Code confirms the default is still `lab` in [src/features.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/features.py:23) and CLI help in [src/cli.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/cli.py:140).

Release docs are operationally useful but not release-note ready. The closed plan confirms all 11 stages are `CLOSED` in [stage-status.md](/home/user/PycharmProjects/ExperimentalHTTPServer/implementation-plan/20260525-133607/stage-status.md:5), but [CHANGELOG.md](/home/user/PycharmProjects/ExperimentalHTTPServer/CHANGELOG.md:7) still keeps the post-remediation body under `[Unreleased]` rather than a dated release/migration boundary.

Distribution docs have an unresolved product decision. `docs/index.md` says `pip install exphttp` at [docs/index.md](/home/user/PycharmProjects/ExperimentalHTTPServer/docs/index.md:28), while README and CONTRIBUTING say the release lane does not publish to PyPI/GHCR at [README.md](/home/user/PycharmProjects/ExperimentalHTTPServer/README.md:973) and [CONTRIBUTING.md](/home/user/PycharmProjects/ExperimentalHTTPServer/CONTRIBUTING.md:113). If external publishing is manual and intentional, docs should say that.

## Issues Found
- **P0: Generated mirror drift blocks docs CI.** Evidence: `sync_docs.py --check` fails for `API.md` and `CONTRIBUTING.md`; CI runs that check at [.github/workflows/ci.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/.github/workflows/ci.yml:95).
- **P1: Changelog/release notes are not ready for the closed plan.** The remediation work is closed, but still stored under `[Unreleased]`.
- **P1: Safe-profile guidance exists, but first-path docs still feel lab-first.** This matches the product/security reports' default-profile concern.
- **P2: Local workflow lets drift happen before CI.** CONTRIBUTING requires sync/stale checks at [CONTRIBUTING.md](/home/user/PycharmProjects/ExperimentalHTTPServer/CONTRIBUTING.md:155), but `.pre-commit-config.yaml` has no docs sync hook at [.pre-commit-config.yaml](/home/user/PycharmProjects/ExperimentalHTTPServer/.pre-commit-config.yaml:33).
- **P2: API contract docs need a stability boundary before clients/v1.** API report recommends declaring current behavior legacy v0 and adding v1 docs later.
- **P2: Architecture docs lag profile/storage boundaries.** Architect report notes `features.py` and `storage.py` are missing from `docs/architecture.md`.

## Concrete Recommendations
1. Regenerate only the drifted mirrors with `python tools/sync_docs.py --write`, then verify `python tools/sync_docs.py --check`.
2. Convert the current `[Unreleased]` changelog block into a dated release section for the closed plan, with a short migration note for profiles, artifact-only releases, package identity, WebSocket knobs, and docs sync.
3. Add a small "choose a profile" first-path block to README/docs index: `serve` for read-only, `workspace` for normal files, `lab` for experiments.
4. Add docs-sync/stale-doc local enforcement to pre-commit or make the PR template explicitly require both commands.
5. Add API "Contract Stability" docs: current API is v0/legacy, `PING` fields are discovery, v1 is future work.

## Quick Wins
- Run `python tools/sync_docs.py --write`.
- Add docs sync/stale checks to `.pre-commit-config.yaml`.
- Update `.github/PULL_REQUEST_TEMPLATE.md` to require mirror regeneration and stale-doc checks.
- Add a dated changelog heading for the completed implementation-plan work.
- Clarify `docs/index.md` install guidance against the artifact-only release policy.

## Deeper Improvements
- Write a profile/default ADR before changing `lab` default.
- Add a `SECURITY.md` "Client IP and proxies" section; code rate-limits direct peer IPs in [src/server.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/server.py:798).
- Add `docs/architecture.md` coverage for `src/features.py`, `src/storage.py`, and capability flow.
- Add API v0/v1 docs before SDK/client work.
- Decide whether distribution means PyPI/GHCR publishing or artifact-only promotion.

## Open Questions
- Should new-user default remain `lab`, or migrate to `workspace`?
- Is PyPI publishing already handled outside this repo, or should docs avoid `pip install exphttp` as the primary path?
- Is reverse-proxy deployment officially app-supported, or should rate limiting remain proxy-owned?
- Is Secure Notepad an ephemeral encrypted scratchpad or future durable secure notes?
