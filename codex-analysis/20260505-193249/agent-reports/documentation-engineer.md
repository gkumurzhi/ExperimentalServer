# documentation-engineer Report
_Generated: 2026-05-05 20:06:30 Europe/Moscow_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260505-193249/analysis-plan.md_

## Summary

Read-only documentation-engineer pass completed for `/home/user/PycharmProjects/ExperimentalHTTPServer`. No repository files were modified.

Primary friction: the dependency-policy migration is only partially reflected. Generated mirrors are in sync, but root-only/docs-site docs and runtime/UI guidance still contain old zero-dependency and `exphttp[crypto]` assumptions.

## Documentation Checks

Boundary analyzed: `README.md`, `CLAUDE.md`, `API.md`, `SECURITY.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `docs/*`, `docs/ADR/*`, `examples/*`, `tools/sync_docs.py`, `mkdocs.yml`, plus runtime strings in `src/request_pipeline.py`, `src/handlers/notepad.py`, and `src/data/static/ui/core.js`.

Validations:
- `tools/sync_docs.py --check`: passed; generated mirrors are mechanically in sync.
- `.venv/bin/mkdocs build --strict --site-dir /tmp/...`: passed; no repo writes.
- `.venv/bin/python -m src --help`: rendered; ACME flags present.
- System `python -m src --help`: failed because global env lacks `acme`, consistent with current runtime dependency requirements.

Context7 was not used; no MkDocs/packaging behavior needed external confirmation.

## Detailed Findings

- Mirror sync is healthy, but it only covers `API.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, and `SECURITY.md` per [tools/sync_docs.py](/home/user/PycharmProjects/ExperimentalHTTPServer/tools/sync_docs.py:23). It will not catch drift in `README.md`, `CLAUDE.md`, `docs/index.md`, `docs/architecture.md`, ADR nav labels, examples, or UI/runtime strings.
- Zero-dependency wording remains in [README.md](/home/user/PycharmProjects/ExperimentalHTTPServer/README.md:11) and [CLAUDE.md](/home/user/PycharmProjects/ExperimentalHTTPServer/CLAUDE.md:7), while runtime deps are declared in [pyproject.toml](/home/user/PycharmProjects/ExperimentalHTTPServer/pyproject.toml:37). `docs/index.md` still says "pure Python" at [docs/index.md](/home/user/PycharmProjects/ExperimentalHTTPServer/docs/index.md:3), which is ambiguous after adding crypto/ACME runtime deps.
- `[crypto]` guidance remains in setup/runtime surfaces even though the extra is empty in [pyproject.toml](/home/user/PycharmProjects/ExperimentalHTTPServer/pyproject.toml:49). Examples: [CONTRIBUTING.md](/home/user/PycharmProjects/ExperimentalHTTPServer/CONTRIBUTING.md:13), [README.md](/home/user/PycharmProjects/ExperimentalHTTPServer/README.md:702), [src/handlers/notepad.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/notepad.py:38), [src/request_pipeline.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/request_pipeline.py:208), and UI strings in [core.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/core.js:552).
- ACME/sslip docs are improved but not operationally complete. [README.md](/home/user/PycharmProjects/ExperimentalHTTPServer/README.md:360) mentions public port 80 and [README.md](/home/user/PycharmProjects/ExperimentalHTTPServer/README.md:376) documents `~/.exphttp/acme/`, renewal, and legacy reads. Missing: sslip uses `api.ipify.org` auto-detection, requires a globally routable IPv4, container/NAT port-80 forwarding, and recovery steps for broken cert/key cache pairs. Code evidence: [tls.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/security/tls.py:386), [tls.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/security/tls.py:402), [tls_manager.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/security/tls_manager.py:99).
- Secure Notepad example HKDF parameters do not match server/browser. Server uses zero salt and `notepad-e2e-key` in [keys.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/security/keys.py:41); browser matches in [notepad.js](/home/user/PycharmProjects/ExperimentalHTTPServer/src/data/static/ui/notepad.js:501); example uses `salt=None` and `exphttp-notepad` in [examples/notepad_client.py](/home/user/PycharmProjects/ExperimentalHTTPServer/examples/notepad_client.py:118).
- Architecture/security docs omit persistence boundaries now relevant to operations: `<root>/notes/` from [server.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/server.py:183) and ACME material under `~/.exphttp/acme/` from [tls_manager.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/security/tls_manager.py:99). [docs/architecture.md](/home/user/PycharmProjects/ExperimentalHTTPServer/docs/architecture.md:66) only describes security layers and upload scope.
- MkDocs nav label is stale: [mkdocs.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/mkdocs.yml:57) says "Optional cryptography", while ADR title is "Runtime crypto and ACME dependencies" in [ADR-003](/home/user/PycharmProjects/ExperimentalHTTPServer/docs/ADR/ADR-003-cryptography-optional.md:1).
- CLI help remains a docs surface with method drift: [src/cli.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/cli.py:32) omits `NOTE`, `HEAD`, `PATCH`, and `DELETE`, while README/API include them.

## Issues Found

- [MEDIUM] Stale dependency story across README, CLAUDE, setup docs, runtime errors, and UI strings.
- [MEDIUM] Notepad example can create notes incompatible with the browser UI because HKDF parameters differ.
- [MEDIUM] ACME/sslip docs lack enough setup/recovery detail for Docker/NAT/public-IP failure paths.
- [LOW] Architecture/threat model docs do not name all persistence/security asset boundaries.
- [LOW] ADR nav and CLI help labels are stale.

## Concrete Recommendations

- Replace zero-dependency language with: default install includes `cryptography` and `acme`; `[crypto]` is a no-op compatibility extra only.
- Replace `install exphttp[crypto]` runtime/UI messages with "install or repair the default exphttp dependencies" or "cryptography backend unavailable in this environment."
- Remove `[crypto]` from recommended developer install commands, or keep one explicit CI compatibility smoke with a comment explaining why.
- Add stale-reference CI grep patterns for `exphttp[crypto]`, zero-dependency phrases, and `Optional cryptography`, with a narrow allowlist for ADR historical context and changelog notes.
- Add an ACME/sslip operations note covering port-80 forwarding, Docker port mapping, global IPv4 validation, `api.ipify.org`, no wildcard/DNS-01 support, fail-closed startup, and cache repair.
- Update API/example docs to state exact Notepad HKDF salt/info and fix `examples/notepad_client.py`.

## Quick Wins

- Fix `README.md:11`, `CLAUDE.md:7`, `docs/index.md:3`.
- Fix runtime/UI `exphttp[crypto]` strings.
- Change `mkdocs.yml` ADR-003 label.
- Add HKDF parameters to `API.md` near `NOTE /notes/exchange`.
- Update CLI help method list.

## Deeper Improvements

- Add an example interoperability test that derives the same notepad key as `src.security.keys`.
- Add a docs drift test for dependency-policy phrases outside approved historical files.
- Add an architecture "Persistence and secrets" section for `uploads/`, `notes/`, `~/.exphttp/acme/`, and legacy `~/.exphttp/letsencrypt/`.
- Add ACME recovery docs tied to actual cache paths and startup behavior.

## Open Questions

- Should CI keep installing `.[crypto,...]` to prove the empty compatibility extra still resolves, or should all active setup docs remove it?
- Should public docs disclose the `api.ipify.org` dependency/privacy implication for `--sslip` auto-detection?
- Should ACME be documented as a convenience mode, with reverse-proxy-managed TLS recommended for production-like deployments?
