# Verification Matrix

| Stage | Required checks | Optional checks | Known blockers | Baseline needed? |
|---|---|---|---|---|
| STAGE-001 | Upload/file handler unit tests, upload method regression tests, ruff/mypy on touched modules | Manual repeated-write smoke in temp dir | Default quota values need product choice; choose conservative opt-in defaults if unclear | Yes: current tests should pass before edits |
| STAGE-002 | Notepad, WebSocket notepad, SMUGGLE/method tests, stale doc guard | Manual retention cleanup smoke | Need decision whether quotas are shared globally or per feature; stage may choose explicit per-feature knobs plus global root cap | Yes |
| STAGE-003 | HTTP receive/request pipeline/live admission tests, concurrent body-budget tests | Memory sampling under concurrent uploads | Full streaming refactor may be too large; minimum acceptable path is declared-length reservation | Yes |
| STAGE-004 | HTTP I/O timeout tests, live slow-client tests, metrics tests | Slow-download socket smoke | Read-rate thresholds may need local timing tolerance | Yes |
| STAGE-005 | CLI/auth/request pipeline tests, docs stale guard, compose config validation | Manual secret-file run with temp file | Canonical secret source choice unresolved; plan selects `--auth-file` as smallest container-safe path | Yes |
| STAGE-006 | Handler registry, server methods, browser smoke or targeted UI capability tests | `python tools/browser_smoke.py` after adding profile parameter | Default profile decision may affect backward compatibility; use explicit default decision in docs/tests | Yes |
| STAGE-007 | CORS/mutation/WebSocket origin tests and docs stale guard | Browser-origin smoke with wildcard read CORS | Requires profile-derived method list from STAGE-006 to avoid duplicate CORS sources | Yes |
| STAGE-008 | Compose config, Docker build, default health inspect, CI YAML lint by workflow parser if available | Auth/TLS container smoke | Docker may be unavailable in local environment; record if not run | No, but capture Docker availability |
| STAGE-009 | Build wheel/sdist, isolated wheel install smoke, release workflow syntax/static review | Container digest scan/provenance dry run | Public PyPI/GHCR intent may be undecided; produce artifact workflow without publish if needed | Yes |
| STAGE-010 | Import boundary tests, CLI smoke from installed wheel, docs stale guard | Compatibility shim deprecation warnings test | Whether `from src` must remain compatible is open; keep shim unless owner says breaking rename is acceptable | Yes |
| STAGE-011 | WebSocket unit/handler/live tests, CLI tests for new knobs, logging/metric assertions | Manual WS close-code probe | WebSocket specialist report was incomplete; keep changes focused on evidence from existing reports | Yes |

