# devops-engineer Report
_Generated: 2026-05-05 20:04:30 Europe/Moscow_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260505-193249/analysis-plan.md_

## Summary

Operational boundary analyzed: GitHub Actions CI/security workflows, pre-commit, pinned CI constraints, Dependabot, docs sync/stale checks, Docker image/compose smoke, and local ignored artifacts.

Control plane: `.github/workflows/ci.yml`, `.github/workflows/security.yml`, `.pre-commit-config.yaml`, `.github/dependabot.yml`.
Data plane: package install, Docker runtime, browser/static UI smoke, TLS/ACME cert acquisition.
Dependency edge: `pyproject.toml` -> `constraints/ci.txt` -> CI/Docker/security; pre-commit is a separate isolated dependency edge.

No files were modified. Context7 was not needed; repo evidence was sufficient.

## Documentation Checks

`PYTHONDONTWRITEBYTECODE=1 python tools/sync_docs.py --check` passed: mirrors are in sync.

The release-smoke stale-doc grep currently fails: `.github/workflows/ci.yml:164-167` matches valid current text in `docs/changelog.md:38` for "advanced upload is enabled by default".

The stale-doc guard misses new runtime-dependency drift: `README.md:11` and `CLAUDE.md:7` still claim pure Python / zero external dependencies, while `pyproject.toml:37-40` declares `acme` and `cryptography`.

`tools/sync_docs.py:23-32` mirrors only `API.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, and `SECURITY.md`; it does not cover `README.md`, `docs/index.md`, `CLAUDE.md`, or bundled UI strings.

## Detailed Findings

1. **Release smoke is currently blocked by its own stale-doc grep.**
Evidence: `.github/workflows/ci.yml:157-167` exits nonzero on grep matches; running the exact pattern matched `docs/changelog.md:38`. This prevents browser and Docker smoke from running.

2. **Pre-commit mypy is stale relative to runtime dependencies.**
Evidence: `.pre-commit-config.yaml:21-28` installs only `cryptography==46.0.5`; `pyproject.toml:37-40` requires `acme>=5.5,<6` and `cryptography>=48.0`; `constraints/ci.txt:4,18,29` pins `acme==5.5.0`, `cryptography==48.0.0`, `josepy==2.2.0`; `src/security/tls.py:25-31` imports `acme`, `cryptography`, and `josepy`.

3. **Docs/UI/runtime errors still point users to the empty `[crypto]` extra.**
Evidence: `[crypto]` is empty in `pyproject.toml:49-50`, but `src/request_pipeline.py:208-212`, `src/handlers/notepad.py:38-40`, and `src/data/static/ui/core.js:257,277,552,572` still say to install or require `exphttp[crypto]`.

4. **Security audit covers current constraints but not installed-environment completeness.**
Evidence: `security.yml` runs weekly and on PRs (`.github/workflows/security.yml:3-9`) and audits only `constraints/ci.txt` (`.github/workflows/security.yml:34-35`). Current constraints include runtime direct/transitive deps, but there is no guard proving every package installed by `pip install -e ...` is pinned and audited.

5. **Docker normal install path is aligned, but TLS/ACME runtime paths are not smoked.**
Evidence: Docker installs the wheel with constrained runtime deps (`Dockerfile:44-49`), but CI Docker smoke only checks `--version` and plain HTTP PING (`.github/workflows/ci.yml:174-183`). No Docker TLS or ACME path is exercised.

6. **Compose ACME path likely fails under the documented hardened runtime.**
Evidence: compose uses `read_only: true`, only `/tmp` tmpfs, and exposes `8080:8080` (`examples/docker/docker-compose.yml:10-19`); ACME writes to `Path.home() / ".exphttp" / "acme"` (`src/security/tls.py:322`, `src/security/tls_manager.py:99`) and defaults HTTP-01 to port 80 (`src/security/tls.py:35-36`).

7. **Ignored local test/tool artifacts can skew local confidence.**
Evidence: `.gitignore:63-64` ignores `tools/close_plan_stages.py` and `tests/test_close_plan_stages.py`; both exist locally and are untracked. `pyproject.toml:96-99` tells pytest to collect `tests/test_*.py`, so local pytest can run tests CI never sees.

## Issues Found

- [HIGH] Release smoke fails before browser/Docker validation due grep false positive.
- [MEDIUM] Pre-commit mypy dependency isolation is inconsistent with CI/runtime deps.
- [MEDIUM] Stale dependency/TLS/ACME text remains outside docs mirror coverage.
- [MEDIUM] `pip-audit` audits constraints, not the resolved installed environment.
- [MEDIUM] Docker smoke does not validate the new TLS/crypto runtime path.
- [MEDIUM] Compose ACME mode lacks writable cert cache and port-80 exposure guidance.
- [LOW] Ignored local tests/tools are a process hazard for dirty-worktree audits.

## Concrete Recommendations

- Replace the inline grep with a small checked script that has explicit deny patterns and allowlists changelog/history text. This restores release-smoke signal without broad false positives.
- Update pre-commit mypy `additional_dependencies` to match constraints: `acme==5.5.0`, `josepy==2.2.0`, `cryptography==48.0.0`.
- Add a dependency completeness check after CI install: compare installed distributions against `constraints/ci.txt`, then run an installed-environment audit in addition to `pip-audit -r constraints/ci.txt`.
- Add Docker TLS smoke: run the image with `--tls` and verify `curl -k -X PING https://127.0.0.1:<port>/`.
- Document or add compose mounts for ACME cache plus port 80 forwarding before advertising `--letsencrypt`/`--sslip` in containers.
- Keep ignored agent-only tests outside `tests/`, or track them if they are meant to affect confidence.

## Quick Wins

- Fix `.github/workflows/ci.yml:164` grep pattern so release smoke can proceed.
- Update stale `exphttp[crypto]` messages in source/UI.
- Update `README.md:11`, `CLAUDE.md:7`, and `mkdocs.yml:57`.
- Add `permissions: contents: read` to workflows as low-risk token hardening.
- Add a read-only CI/preflight check for ignored files under `tests/` and `tools/`.

## Deeper Improvements

- Add a manual `workflow_dispatch` ACME staging smoke with a controlled domain, explicit ownership, no PR secrets exposure, and clear rollback/cleanup notes.
- Move constraints refresh to a documented clean-env process that produces a lock/completeness report.
- Consider SHA-pinning GitHub Actions and avoiding floating runner labels for release-critical jobs.
- Add Docker healthcheck variants or docs for TLS/auth modes; current image healthcheck is HTTP-only.

## Open Questions

- Should `[crypto]` remain user-visible anywhere, or only exist silently for backward-compatible installs?
- Should ACME cache location be configurable for containers, for example via CLI/env?
- Who owns a safe staging ACME domain and port-80 routing for live validation?
- Should `tools/close_plan_stages.py` and its tests be tracked, moved outside the repo, or excluded from local pytest explicitly?
