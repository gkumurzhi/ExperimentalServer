# documentation-engineer Report
_Generated: 2026-04-28 12:45:30 MSK_
_Source plan: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260428-113859/analysis-plan.md_

**Summary**
Read-only documentation audit only. I analyzed `README.md`, `API.md`, `SECURITY.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `CLAUDE.md`, `docs/**/*.md`, `mkdocs.yml`, `tools/sync_docs.py`, and the focused source/test files needed to verify documented behavior. No source, docs, config, tests, lockfiles, or runtime data were modified; I did not read `uploads/`, `notes/`, `.env*`, keys, certs, or credentials.

Primary friction: mirror generation is working, but several root-canonical docs and `CLAUDE.md` still carry stale operational contracts, especially OPSEC/sandbox flags, advanced-upload defaults, security threat-model details, and API examples.

**Documentation Checks**
- Generated mirrors: `python3 tools/sync_docs.py --check` returned `Documentation mirrors are in sync.`
- CLI defaults checked against `src.cli.create_parser()`: host `127.0.0.1`, port `8080`, dir `.`, max size `100`, workers `10`, CORS disabled, advanced upload `False`.
- Failure path checked: `python3 -m src --opsec` exits with argparse error, confirming OPSEC flags are removed.
- MkDocs integration check blocked: `mkdocs` is not installed in this environment.
- No Context7 or external documentation lookup was used; findings are repository-evidence based.

**Issues Found**
- **HIGH: `CLAUDE.md` documents removed and unsafe workflow contracts.**
  Evidence: [CLAUDE.md](/home/user/PycharmProjects/ExperimentalHTTPServer/CLAUDE.md:7) mentions OPSEC mode and sandbox restrictions; [CLAUDE.md](/home/user/PycharmProjects/ExperimentalHTTPServer/CLAUDE.md:22) recommends `--opsec --sandbox`; [CLAUDE.md](/home/user/PycharmProjects/ExperimentalHTTPServer/CLAUDE.md:95) recommends `str(...).startswith(...)` path checks. Current CLI only exposes `--advanced-upload` in [src/cli.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/cli.py:64), and tests reject removed flags in [tests/test_cli.py](/home/user/PycharmProjects/ExperimentalHTTPServer/tests/test_cli.py:69). Confidence: high.

- **MEDIUM: `CHANGELOG.md` contradicts current advanced-upload default.**
  Evidence: [CHANGELOG.md](/home/user/PycharmProjects/ExperimentalHTTPServer/CHANGELOG.md:35) says advanced upload is enabled by default, while [src/cli.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/cli.py:64) sets it opt-in and [tests/test_cli.py](/home/user/PycharmProjects/ExperimentalHTTPServer/tests/test_cli.py:61) asserts `False`. Confidence: high.

- **MEDIUM: threat model still treats Transfer-Encoding smuggling as an unfixed limitation.**
  Evidence: [docs/threat-model.md](/home/user/PycharmProjects/ExperimentalHTTPServer/docs/threat-model.md:37) says to deploy behind a proxy that rejects `Transfer-Encoding` until fixed; code now rejects any `Transfer-Encoding` in [src/http/io.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/http/io.py:40) and [src/http/io.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/http/io.py:109). Confidence: high.

- **MEDIUM: advanced-upload generated filename workflow is under-documented.**
  Evidence: [README.md](/home/user/PycharmProjects/ExperimentalHTTPServer/README.md:254) says omitted names become `<sha256[:12]>.bin`; code does that in [src/handlers/advanced_upload.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/advanced_upload.py:229), but the response in [src/handlers/advanced_upload.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/advanced_upload.py:258) returns only `ok`, `id`, `sz`, and `transport`, not the saved filename/path. Collision suffixing at [src/handlers/advanced_upload.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/advanced_upload.py:237) makes prediction unreliable. Confidence: high.

- **MEDIUM: ADR/security language overstates HMAC coverage.**
  Evidence: [docs/ADR/ADR-002-advanced-upload-xor-hmac.md](/home/user/PycharmProjects/ExperimentalHTTPServer/docs/ADR/ADR-002-advanced-upload-xor-hmac.md:21) says HMAC covers ciphertext plus metadata; implementation verifies HMAC only over decoded payload bytes in [src/handlers/advanced_upload.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/advanced_upload.py:217) and [src/security/crypto.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/security/crypto.py:223). Confidence: high.

- **LOW: `API.md` INFO directory example does not match response shape.**
  Evidence: [API.md](/home/user/PycharmProjects/ExperimentalHTTPServer/API.md:171) shows item fields like `type`, `size`, and `modified`; implementation returns directory entries as `{"name": ..., "is_dir": ...}` in [src/handlers/info.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/info.py:69). Confidence: high.

- **LOW: OPTIONS wording implies CORS headers are always included.**
  Evidence: [API.md](/home/user/PycharmProjects/ExperimentalHTTPServer/API.md:466) says `Access-Control-Allow-Methods` is included; `handle_options()` returns bare `204` when CORS is disabled in [src/handlers/files.py](/home/user/PycharmProjects/ExperimentalHTTPServer/src/handlers/files.py:311), matching the top-level CORS caveat in [API.md](/home/user/PycharmProjects/ExperimentalHTTPServer/API.md:6). Confidence: high.

- **LOW: contributor checklist says `--check` regenerates mirrors.**
  Evidence: [CONTRIBUTING.md](/home/user/PycharmProjects/ExperimentalHTTPServer/CONTRIBUTING.md:107) says root-canonical docs are regenerated with `--check`; [tools/sync_docs.py](/home/user/PycharmProjects/ExperimentalHTTPServer/tools/sync_docs.py:62) only reports drift in check mode, while [tools/sync_docs.py](/home/user/PycharmProjects/ExperimentalHTTPServer/tools/sync_docs.py:66) writes only outside check mode. Confidence: high.

- **LOW: generated mirror edit path can send contributors to the wrong source.**
  Evidence: [mkdocs.yml](/home/user/PycharmProjects/ExperimentalHTTPServer/mkdocs.yml:4) sets edit links under `docs/`; generated pages tell contributors to edit root files via banner in [tools/sync_docs.py](/home/user/PycharmProjects/ExperimentalHTTPServer/tools/sync_docs.py:42). Confidence: medium.

**Recommendations**
Smallest safe intervention: update root-canonical docs first, then run `python tools/sync_docs.py --write` once and commit root plus generated mirror changes. Prioritize `CLAUDE.md`, `CHANGELOG.md`, `docs/threat-model.md`, `API.md`, `CONTRIBUTING.md`, and ADR-002.

Key tradeoff: documentation-only fixes are safest and unblock contributors quickly. Adding `filename`/`path` to advanced-upload responses would better solve the workflow, but it is an API behavior change and should be tested.

**Quick Wins**
- Replace `CLAUDE.md` OPSEC/sandbox guidance with a short pointer to `README.md`, `CONTRIBUTING.md`, and `API.md`, or fully align it with current `--advanced-upload` behavior.
- Change `CHANGELOG.md` line 35 to “disabled by default; enabled with `--advanced-upload`.”
- Update INFO and OPTIONS examples in `API.md`.
- Fix `CONTRIBUTING.md` checklist wording to “mirrors checked with `--check` after regeneration with `--write`.”
- Extend the CI stale-doc grep to catch `--opsec`, `--sandbox`, `OPSEC_*`, `handle_opsec_upload`, `startswith(str(base))`, and `--max-workers`.

**Open Questions**
- Should advanced-upload responses include the actual saved `filename` and `/uploads/...` path?
- Should HMAC be expanded to cover metadata, or should ADR/threat-model language be narrowed to payload bytes only?
- Is `CLAUDE.md` intended to remain a maintained AI guide, or should it become a minimal redirect to canonical docs?
- Should MkDocs edit links be disabled or customized for generated mirror pages?
