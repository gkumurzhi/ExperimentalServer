# Preflight
_Generated: 2026-05-05 19:32:49 Europe/Moscow_

## Run Paths
- Repository root: `/home/user/PycharmProjects/ExperimentalHTTPServer`
- Output directory: `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260505-193249`
- Agent reports directory: `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260505-193249/agent-reports`

## Git Snapshot
- Branch: `main`
- HEAD: `44b9209`
- Working tree status: `dirty`
- Dirty files observed at preflight: `API.md`, `CHANGELOG.md`, `Dockerfile`, `README.md`, `SECURITY.md`, `constraints/ci.txt`, `docs/ADR/ADR-002-advanced-upload-xor-hmac.md`, `docs/ADR/ADR-003-cryptography-optional.md`, `docs/ADR/README.md`, `docs/api.md`, `docs/architecture.md`, `docs/changelog.md`, `docs/index.md`, `docs/security.md`, `examples/notepad_client.py`, `pyproject.toml`, `src/cli.py`, `src/security/tls.py`, `src/security/tls_manager.py`, `src/server.py`, `tests/test_cli.py`, `tests/test_security/test_tls.py`, `tests/test_security/test_tls_manager.py`.

## Tooling
- Context7 MCP: `available`
- Subagents: `available, not started in Phase 0/1`
- Notes: Context7 was discovered through `tool_search` and verified with successful documentation lookups for `/pyca/cryptography`, `/certbot/certbot`, and `/websites/pytest_en_stable`. No Context7 token, quota, or transport blocker was observed. The working tree already contained user-requested implementation changes before this audit run; this audit treats them as part of the current repository state and remains read-only except for files under this output directory.

## Safety Notes
- Secret-heavy files skipped: yes
- Generated/dependency directories excluded from exhaustive traversal: yes
- Source code, dependencies, tests, docs, configs, lockfiles, and infrastructure files were not modified by this audit workflow.
