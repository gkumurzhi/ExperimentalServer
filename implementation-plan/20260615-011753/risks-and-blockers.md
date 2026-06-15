# Risks and Blockers

| Risk | Affected stages | Mitigation |
|---|---|---|
| The default-profile decision can block the safe workspace train. | STAGE-002, STAGE-004, STAGE-006, STAGE-008 | Use the analysis recommendation as the default proposal: `workspace` for new users, `lab` as explicit opt-in. If maintainers reject it, update STAGE-004 into a no-default-flip hardening stage. |
| Changing the default from `lab` can break scripts relying on implicit advanced upload, SMUGGLE, NOTE, or WebSocket notes. | STAGE-004 | Preserve `--profile lab`, document migration notes, and verify old lab behavior explicitly. |
| Docker `docker run -p` can expose lab behavior if defaults remain broad. | STAGE-002, STAGE-008 | Make examples pass explicit safe profiles or clearly state image status and required auth/TLS/profile flags. |
| Reverse-proxy auth throttling can be misunderstood as per-client when the app only sees the proxy peer IP. | STAGE-002 | Document direct-peer semantics and require proxy-side per-client throttling unless a trusted-proxy feature is intentionally designed later. |
| Browser smoke and Playwright dependencies may not be available in every local environment. | STAGE-005, STAGE-006 | Keep static checks required, use browser smoke where dependencies exist, and make CI the authoritative profile-smoke gate. |
| Python 3.14 may reveal dependency, wheel, or tooling failures. | STAGE-007 | Add 3.14 to constrained CI before metadata changes; do not combine with dependency refresh or 3.10/3.11 deprecation. |
| Benchmark results may be noisy and machine-specific. | STAGE-009 | Record first-run baselines with environment notes and use benchmarks mainly to detect large regressions and validate no-limit quota-scan behavior. |
| API v1, durable Notepad, trusted proxy, and publishing work can expand beyond a single stage. | STAGE-010, STAGE-011, backlog | Keep STAGE-010/011 limited to legacy docs and bounded safety fixes; move strategic implementation into separate future plans. |
| This planning run did not perform fresh external documentation lookups. | All | Treat external-doc-sensitive implementation details as stage-time verification if a future stage depends on current platform behavior. |
