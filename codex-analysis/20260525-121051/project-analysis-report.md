# Project Analysis Report
_Generated: 2026-05-25 13:26:20 MSK_
_Agents used: 8 completed reports, 5 incomplete attempts recorded_
_Output directory: /home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260525-121051_

## Executive Summary

Проект уже выглядит сильным для экспериментального Python HTTP/WebSocket сервера: есть собственные parser/handler boundaries, Basic Auth с PBKDF2 и constant-time comparison, защита от path traversal, лимиты заголовков и WebSocket frame size, TLS/ACME, CI matrix, security workflow, browser smoke, Dockerfile с non-root runtime и pinned base digest.

Главный ответ на вопрос аудита: перед дальнейшей разработкой и эксплуатацией нужно сначала закрыть эксплуатационные границы ресурса и поверхности возможностей. Сейчас сервер можно использовать в локальном/лабораторном режиме, но для более широкой эксплуатации не хватает aggregate storage quota/retention, потоковой или бюджетированной обработки uploads, защиты от slow-body worker starvation, безопасного источника Basic Auth секретов, feature profiles для отключения рискованных возможностей, и более строгой политики wildcard CORS.

Критических подтвержденных дефектов уровня immediate exploit/auth bypass не найдено. Но есть несколько HIGH-рисков, которые в сумме делают внешний или долгоживущий deployment преждевременным:

- повторные валидные uploads/notes/SMUGGLE artifacts могут заполнить диск, потому что `--max-size` ограничивает запрос, а не накопленный объем;
- стандартные uploads полностью буферизуются в память, так что дефолтные `10 workers * 100 MB` дают примерно 1 GB request-body pressure до Python overhead;
- slow/incomplete request bodies могут занять все workers примерно до 330 секунд;
- Basic Auth секреты для service/container deployment передаются только через argv/config examples;
- `SMUGGLE`, advanced upload, `NOTE`, destructive `DELETE/clear` включены как единая глобальная поверхность за одним Basic Auth решением.

Рекомендованный порядок: сначала ресурсные лимиты и storage policy, затем безопасные секреты, затем feature profiles/capability gates, затем CORS/write/WebSocket policy, затем Docker/ACME/healthcheck readiness и release supply-chain. Переименование публичного import package с `src` на `exphttp` важно сделать до расширения публичного API, чтобы не закреплять неудобный контракт.

## Scope & Coverage

Аудит был read-only для исходного проекта. Изменения созданы только в `codex-analysis/20260525-121051/`.

Проверено:

- Python package/CLI/server code under `src/`;
- HTTP receive/parser pipeline, handler registry, uploads, advanced upload, Notepad, WebSocket, TLS/ACME, Basic Auth, CORS;
- tests, tools, browser smoke scripts, CI/security workflows;
- Dockerfile, Compose examples, docs (`README.md`, `API.md`, `SECURITY.md`, `docs/threat-model.md`, architecture docs);
- package/dependency/release configuration.

Context7 был доступен и использован. Документация проверялась для Setuptools, pytest, CPython/Python stdlib, cryptography, Docker, GitHub Actions, Python Packaging User Guide, mypy и browser/CORS/WebSocket guidance. В Docker review Context7 `/docker/docs` отработал, а запрос к compose-spec завершился `TypeError: fetch failed`; Docker official docs были использованы как fallback.

Ограничения:

- `websocket-engineer`, `dependency-manager`, `frontend-developer`, `documentation-engineer`, `api-documenter` не вернули структурированные отчеты после ожидания; это зафиксировано error reports.
- `python-pro` subagent столкнулся с локальной `bwrap` проблемой, но Python/package audit был выполнен в parent session и сохранен как отчет.
- Было запущено 53 focused pytest tests в Python/package review; полный pytest/mypy/ruff/browser/Docker/ACME прогон не выполнялся в рамках итогового read-only аудита. `mypy` не удалось проверить из-за `ModuleNotFoundError: mypy`.

## Agents Used

| Agent | Role | Report | Status |
|---|---|---|---|
| security-auditor | Security/auth/CORS/TLS/crypto/handler surface review | `agent-reports/security-auditor.md` | completed |
| architect-reviewer | Package/API boundaries, feature profiles, handler architecture | `agent-reports/architect-reviewer.md` | completed |
| python-pro | Python packaging/runtime edge cases/tests | `agent-reports/python-pro.md` | completed with subagent sandbox caveat |
| devops-engineer | CI/release/artifacts/workflow review | `agent-reports/devops-engineer.md` | completed |
| performance-engineer | Resource, memory, worker, streaming and listing review | `agent-reports/performance-engineer.md` | completed |
| qa-expert | Test strategy and risk coverage review | `agent-reports/qa-expert.md` | completed |
| docker-expert | Dockerfile/Compose/container operations review | `agent-reports/docker-expert.md` | completed |
| reviewer | Final dedupe/severity/priority pass | `agent-reports/reviewer.md` | completed |
| websocket-engineer | WebSocket specialist review | `agent-reports/websocket-engineer-error.md` | incomplete: timeout/empty structured output |
| dependency-manager | Dependency/SBOM/package graph specialist review | `agent-reports/dependency-manager-error.md` | incomplete: timeout/empty structured output |
| frontend-developer | Static UI/browser UX specialist review | `agent-reports/frontend-developer-error.md` | incomplete: timeout/empty structured output |
| documentation-engineer | Documentation accuracy/operator guide review | `agent-reports/documentation-engineer-error.md` | incomplete: timeout/empty structured output |
| api-documenter | API contract/docs review | `agent-reports/api-documenter-error.md` | incomplete: timeout/empty structured output |

## Critical & High Issues

No confirmed CRITICAL issues were found.

| # | Severity | Issue | Source Agent(s) | File / Area | Recommended Fix |
|---|---|---|---|---|---|
| 1 | HIGH | No aggregate disk quota, retention, or storage backpressure | security-auditor, architect-reviewer, python-pro, performance-engineer, qa-expert, docker-expert, reviewer | `src/server.py:84`, `src/server.py:206-212`, `src/handlers/files.py:418-420`, `src/handlers/advanced_upload.py:385-387`, `src/notepad_service.py:313-337`, `src/notepad_service.py:390-401`, `docs/threat-model.md:61-62` | Add shared `StoragePolicy`/storage service with total bytes, file/note count, retention, free-space reservation, and pre-write rejection (`413`/`507`) for uploads, notes, and SMUGGLE temp artifacts. |
| 2 | HIGH | Standard uploads are fully buffered in memory | performance-engineer, python-pro, reviewer | `src/http/io.py:102-201`, `src/http/request.py:39-40`, `src/handlers/files.py:418-419`, `src/cli.py:97-119` | Stream request bodies to same-directory temp files with atomic publish, or at minimum add a process-wide in-flight body memory budget based on declared `Content-Length`. |
| 3 | HIGH | Slow/incomplete request bodies can occupy all workers for about 330 seconds | performance-engineer, reviewer | `src/http/io.py:17-19`, `src/http/io.py:114-123`, `src/http/io.py:196-199`, `src/server.py:530-540` | Add configurable body idle/deadline controls, minimum read-rate or shorter body timeout, slow-body metrics, and admission protection that accounts for slow readers. |
| 4 | HIGH | Basic Auth service/container secrets are argv-only | security-auditor, devops-engineer, docker-expert, qa-expert, reviewer | `src/cli.py:171-177`, `src/cli.py:264`, `src/server.py:225-245`, `README.md:192-199`, `examples/docker/docker-compose.yml:29-40` | Add `--auth-file` or equivalent mounted secret source, define precedence/failure/redaction behavior, and update README/Compose examples away from inline credentials. |
| 5 | HIGH | No capability boundary between safe serving and risky demo/destructive features | architect-reviewer, security-auditor, qa-expert, docker-expert, reviewer | `src/server.py:148`, `src/cli.py:89-93`, `src/handlers/__init__.py:36-77`, `src/handlers/files.py:206-210`, `src/handlers/notepad.py:87-90` | Introduce `FeatureSet`/`ServerProfile` and derive handler registry, CORS methods, PING capabilities, WebSocket availability, UI affordances, and tests from that single source. |

## Architecture & Design

The current architecture is coherent for one all-features lab server. `RequestPipeline` owns parse/auth/origin/size/dispatch/send order, and `HandlerRegistry` gives a clear method map. That foundation is useful and should be kept.

The architecture needs a capability boundary before more features are added. Today `ExperimentalHTTPServer` owns auth, TLS views, metrics, locks, upload/notes dirs, ECDH state, WebSocket limits, SMUGGLE temp files, and feature flags. `advanced_upload_enabled = True` is unconditional at `src/server.py:148`, `--advanced-upload` is a deprecated no-op at `src/cli.py:89-93`, and `DELETE`, `NOTE`, `SMUGGLE`, advanced unknown-method upload are always registered in `src/handlers/__init__.py:36-77`.

Recommended architecture:

- `serve` profile: static/file read paths, PING/INFO as appropriate, no destructive methods.
- `workspace` profile: ordinary upload/delete where explicitly intended.
- `lab` profile: NOTE, SMUGGLE, advanced upload and unknown-method upload.

Build the registry, CORS method list, browser mutation guard, WebSocket availability, UI capability discovery, and docs from that profile object.

The documented programmatic custom-auth example also mutates `server.authenticator` after construction (`README.md:489-491`), while `_rate_limiter` is initialized in `__init__` based on the authenticator state (`src/server.py:200-201`). Replace this with constructor injection or `set_authenticator()` that preserves rate-limiter invariants.

## Security & Compliance

Positive controls:

- Basic Auth uses PBKDF2-SHA256 and constant-time comparison.
- Path containment and traversal defenses are covered well.
- Transfer-Encoding / Content-Length smuggling defenses are present in receive layer.
- AES-GCM/HMAC/ECDH choices are generally sound for the stated Notepad model.
- WebSocket masks, frame caps, and admission limits exist.
- TLS context choices are modern.

Main security work before operation:

- Add non-argv secret injection. Inline `--auth user:pass` is unsuitable for systemd, Docker, CI, or orchestration because argv and Compose snippets are commonly observable.
- Make wildcard CORS read-only. `parse_cors_origins("*")` returns `("*",)` (`src/http/cors.py:83-86`), read CORS emits `*` (`src/http/cors.py:95-99`), and mutation/WebSocket guards allow wildcard (`src/server.py:804-805`, `src/server.py:840-841`). Require exact origins for browser mutations and WebSocket upgrades.
- Treat Basic Auth rate limiting as local-only unless proxy behavior is designed. It is in-memory and keyed by `client_address[0]` via `AuthRateLimiter` (`src/security/auth.py:183-215`), so reverse-proxy deployments need external rate limiting or a strict `--trusted-proxy` model.
- Decide whether Notepad is an ephemeral encrypted scratchpad or durable secure notes. `API.md:405` explicitly says keys are session-bound and not durably recoverable; metadata remains plaintext (`API.md:401-405`).

## Performance & Reliability

The highest operational risk is resource exhaustion through valid traffic:

- Disk: per-request caps exist, but accumulated `uploads/`, `notes/`, and SMUGGLE temp artifacts are unbounded.
- Memory: `receive_request()` accumulates chunks and returns `b"".join(chunks)` (`src/http/io.py:102-201`); `HTTPRequest` stores `body`; upload writes `request.body`.
- Workers: a client can send headers with an allowed `Content-Length` and then stall body transfer until `HEADER_TIMEOUT + BODY_TIMEOUT` (`30 + 300` seconds).
- Listings: `INFO` and Notepad list paths scan/sort broad directory state before limiting output; Notepad has no pagination.
- WebSocket: resource knobs exist in constructor but are not exposed in CLI; unexpected internal failures log at debug level and close as normal `1000` (`src/server.py:1007-1011`).

Before long-running deployment, add:

- aggregate storage accounting and periodic cleanup;
- streaming upload temp-file commit or global in-flight memory budget;
- slow-body and slow-download limits/metrics;
- bounded listing/pagination;
- CLI knobs for WebSocket connection count and incomplete-frame timeout.

## Code Quality & Maintainability

The codebase has useful separation in parser, pipeline, handlers, security helpers, TLS manager, and tests. The main maintainability issue is public package identity.

The distribution is named `exphttp` (`pyproject.toml:6`), but the import package and console script use `src` (`pyproject.toml:48`, `pyproject.toml:75`, `pyproject.toml:77-83`). README documents `from src import ...` and `python -m src`. This is acceptable as an early internal layout, but it is a poor public API and migration cost grows with every release.

Recommended path:

- short term: add `namespaces = false` under `[tool.setuptools.packages.find]` and test package discovery;
- medium term: migrate import package to `exphttp`, update console script to `exphttp.cli:main`, and keep a deprecated `src` compatibility shim if existing users matter;
- update docs/tests/tools to prefer `from exphttp import ...`.

Also improve file commit semantics: `write_unique_file_exclusive()` opens the final path directly and writes bytes there, so a crash or concurrent read can observe a partial file. Use hidden temp files plus atomic rename.

## DevOps & Infrastructure

CI is stronger than average for a small Python server: matrix tests, lint, type check, docs checks, browser smoke, Docker smoke, pip-audit, Bandit, Dependabot, and static UI package-data checks exist.

Gaps before production distribution:

- no tag-gated release/publish workflow;
- no artifact-of-record for wheel/sdist/container;
- no SBOM/provenance/attestation/signing/scanning release lane;
- browser smoke runs from source tree, not the exact installed wheel/container UI runtime;
- coverage gate is global and low (`--cov-fail-under=65` at `.github/workflows/ci.yml:61-62`).

Docker baseline is good: pinned slim digest, multi-stage wheel build, non-root user, exec-form entrypoint, Compose hardening with `read_only`, `tmpfs`, `cap_drop`, `no-new-privileges`.

Docker operational gaps:

- default Compose publishes plain HTTP on all host interfaces (`examples/docker/docker-compose.yml:18-19`);
- container healthcheck probes unauthenticated plain HTTP `PING` (`Dockerfile:61-64`), while auth/TLS/ACME modes need protocol/credential-aware probes;
- ACME profile disables healthcheck (`examples/docker/docker-compose.yml:96-99`);
- no container resource envelope or volume quota examples.

## Frontend & UX

Frontend specialist coverage is limited because `frontend-developer` did not return a structured report. Existing browser smoke appears broad for the unauthenticated local UI and covers static assets, inspector APIs, method matrix, opsec transport switching, and Notepad normal/unavailable states.

Before turning the embedded UI into a product surface:

- review accessibility and error states with a frontend/browser specialist;
- ensure UI capability display comes from `FeatureSet`/`ServerProfile`;
- ensure disabled destructive/lab features are hidden or clearly unavailable;
- add browser smoke for safe profile and auth/TLS deployment modes.

## Data & ML

No database, queue, ML, or analytics layer was found. Persistent data is filesystem-based:

- `<root>/uploads/`;
- `<root>/notes/`;
- `~/.exphttp/acme`.

The main data work is storage policy, quota, retention, backup/recovery expectations, and Notepad durability semantics.

## Product & Growth

The project straddles two products:

- a convenient file/static server;
- a lab server with custom methods, advanced upload, SMUGGLE, and encrypted Notepad experiments.

This needs an explicit product decision before development continues. Without profiles, every deployment inherits the lab surface. Profiles let docs, Docker examples, UI, tests, and support posture describe what the server is for in each mode.

## Documentation & Process

Docs are generally strong, but several examples normalize risky usage:

- README examples use literal `--auth admin:secretpassword` and `--auth admin:pass` (`README.md:192-199`);
- Compose examples show inline `admin:replace-with-a-strong-secret` (`examples/docker/docker-compose.yml:29-40`);
- `docs/threat-model.md:61-62` says large upload disk-fill is mitigated by `--max-size`, but that is only a per-request cap.

Update docs alongside code changes, then add stale-doc guards for:

- `from src`, `import src`, `python -m src` after package migration;
- inline auth secret examples after `--auth-file`;
- profile capability tables after `FeatureSet` lands;
- wildcard CORS wording after policy change.

## Quick Wins Backlog

| Priority | Task | Source Agent(s) | Area | Estimated Effort |
|---|---|---|---|---|
| P0 | Correct `docs/threat-model.md` so `--max-size` is described as per-request only | security-auditor, qa-expert | docs/security | S |
| P0 | Add warning in help/docs that `--auth USER:PASS` leaks through process arguments | security-auditor, devops-engineer | auth/docs | S |
| P0 | Change wildcard CORS tests and code so `*` no longer authorizes mutations/WS upgrades | security-auditor, qa-expert, reviewer | security | M |
| P0 | Add storage quota tests as pending/xfail until implementation exists | qa-expert | tests | S |
| P1 | Add `namespaces = false` and package discovery test | python-pro | packaging | S |
| P1 | Make `advanced_upload_enabled` actually gate unknown-method advanced upload and PING reporting | architect-reviewer | architecture | S-M |
| P1 | Make Compose default port loopback-only or clearly profile-gated | docker-expert, reviewer | Docker | S |
| P1 | Add `stop_grace_period` and commented resource-limit examples to Compose | docker-expert | Docker | S |
| P1 | Add CLI flags for WebSocket capacity/incomplete-frame timeout | performance-engineer | ops/runtime | S-M |
| P1 | Add isolated wheel install smoke: `exphttp --help`, `--version`, import probe | qa-expert, devops-engineer | CI/release | S-M |

## Deeper Improvements Roadmap

1. Resource safety:
   - shared storage service for uploads, notes, SMUGGLE temp artifacts;
   - total byte/count quotas and retention;
   - streaming upload commit with temp files;
   - load tests for concurrent max-size uploads, stalled bodies, slow downloads, large directories and notes.

2. Capability model:
   - `FeatureSet`/`ServerProfile`;
   - registry/CORS/PING/UI/WebSocket derived from profile;
   - tests for safe profile negative paths;
   - method-level authorization only after coarse profiles exist.

3. Operational auth:
   - `--auth-file` or equivalent secret source;
   - Compose secrets example;
   - redaction tests and missing/unreadable/invalid secret tests;
   - reverse-proxy rate-limit guidance or trusted-proxy CIDR support.

4. Release and supply chain:
   - tag-gated wheel/sdist workflow with PyPI trusted publishing if public;
   - installed-wheel browser smoke;
   - container build by digest with SBOM/provenance, scan and attestation;
   - documented rollback/promotion by digest.

5. Package/API evolution:
   - move public imports to `exphttp`;
   - compatibility shim for `src` if needed;
   - public API tests and docs migration guard.

## Full Recommended Action Plan

### Immediate

- Do not treat the current project as production-ready for public or long-running external operation.
- Implement aggregate storage limits or enforce equivalent host/container quotas before any deployment that allows writes.
- Add in-flight upload memory control or start the streaming-upload refactor before raising workers/max-size or supporting larger deployments.
- Add slow-body timeout/read-rate protection to prevent worker starvation.
- Add a safe non-argv Basic Auth secret source and update service/container examples.
- Introduce the first `FeatureSet`/`ServerProfile` slice or, at minimum, make advanced upload/SMUGGLE/NOTE/destructive clear operations explicitly disable-able.

### Short Term

- Change wildcard CORS policy: keep `Access-Control-Allow-Origin: *` for read-only responses only; require exact origins for mutations and WebSocket.
- Update tests that currently assert wildcard mutation/WebSocket allow.
- Make Docker examples safer: loopback default, resource-limit examples, mode-aware healthcheck guidance.
- Fix docs that overstate `--max-size` as disk-fill mitigation.
- Add package discovery guard and `namespaces = false`.
- Add WebSocket error close semantics (`1011` or explicit error frame) and non-debug exception logging.

### Medium Term

- Build `StoragePolicy` and use it across uploads, advanced upload, Notepad, and SMUGGLE.
- Stream standard uploads to temp files and atomically publish final files.
- Add risk-targeted test gates for parser, CORS, upload storage, Notepad, WebSocket, TLS/ACME, Docker and CLI auth.
- Add release smoke from installed wheel and container UI runtime.
- Define Notepad as either ephemeral scratchpad or durable encrypted storage, then align UX, docs, and tests.
- Plan migration from `src` package to `exphttp`.

### Long Term

- Add release artifact provenance, SBOM, signing/attestation and image scanning if public distribution is planned.
- Add ACME renewal/reload or explicit restart-before-expiry operational policy with tests/docs.
- Add trusted reverse-proxy model if app-level client IP attribution is required.
- Consider per-role/method authorization after coarse profiles are stable.
- Run focused follow-up audits for WebSocket lifecycle, dependency/SBOM, frontend/browser UX, documentation accuracy, and API contract completeness.

## Open Questions for the Team

- Is internet-facing operation a supported target, or only localhost/trusted lab?
- Which profile should become the default: backward-compatible `lab`, safer `workspace`, or read-only `serve`?
- Should storage quotas be global across uploads/notes/SMUGGLE or separately configurable per feature?
- Which secret source should be canonical for services: file, env var, stdin, or orchestrator-native secret?
- Should `--cors-origin *` ever permit writes, or must wildcard be read-only?
- Is Notepad intentionally ephemeral, or should recovery/re-keying become a product requirement?
- Is public PyPI/GHCR/Docker distribution planned?
- Must `from src` remain compatible after the package rename?

## Appendix: Source Reports

- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260525-121051/preflight.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260525-121051/agents-inventory.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260525-121051/analysis-plan.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260525-121051/agent-reports/security-auditor.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260525-121051/agent-reports/architect-reviewer.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260525-121051/agent-reports/python-pro.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260525-121051/agent-reports/devops-engineer.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260525-121051/agent-reports/performance-engineer.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260525-121051/agent-reports/qa-expert.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260525-121051/agent-reports/docker-expert.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260525-121051/agent-reports/reviewer.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260525-121051/agent-reports/websocket-engineer-error.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260525-121051/agent-reports/dependency-manager-error.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260525-121051/agent-reports/frontend-developer-error.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260525-121051/agent-reports/documentation-engineer-error.md`
- `/home/user/PycharmProjects/ExperimentalHTTPServer/codex-analysis/20260525-121051/agent-reports/api-documenter-error.md`
