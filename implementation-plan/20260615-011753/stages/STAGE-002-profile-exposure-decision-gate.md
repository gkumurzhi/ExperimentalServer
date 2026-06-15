# STAGE-002 - Profile and exposure decision gate

## Status
OPEN

## Priority
MEDIUM

## Source findings
- `codex-analysis/20260614-225437/project-analysis-report.md` - Executive Summary: recommended path is safe-by-default file workspace with `lab` as explicit opt-in.
- `codex-analysis/20260614-225437/agent-reports/product-manager.md` - P0/P1: `lab` default conflicts with safe new-user posture and product identity is split.
- `codex-analysis/20260614-225437/agent-reports/security-auditor.md` - F1/F2: `lab` default is risky for packaged/container exposure; reverse-proxy client identity is direct-peer only.
- `codex-analysis/20260614-225437/agent-reports/docker-expert.md` - Issues: raw Docker `docker run -p` can expose broad lab behavior.

## Goal
Record the supported profile/default, external exposure, reverse-proxy, Docker, and compatibility policy before changing defaults or promoting distribution/API tracks.

## Non-goals
- Do not flip the default profile in this stage.
- Do not add trusted-proxy header parsing.
- Do not publish artifacts or change release automation beyond docs required for the decision.

## Scope
### Likely files to inspect
- `docs/ADR/README.md` and existing `docs/ADR/ADR-*.md` - ADR naming and style.
- `README.md` - profile, quick-start, Docker, external exposure, and Python support wording.
- `SECURITY.md` and `docs/threat-model.md` - direct-peer auth throttling and reverse-proxy guidance.
- `Dockerfile` and `examples/docker/docker-compose.yml` - current profile/bind defaults.
- `src/features.py` and `src/cli.py` - current default profile evidence.

### Likely files to change
- `docs/ADR/ADR-006-profile-default-and-exposure.md` - record the chosen policy.
- `docs/ADR/README.md` - link the new ADR.
- `README.md` - add a first-path profile decision table for `serve`, `workspace`, and `lab`.
- `SECURITY.md` and `docs/security.md` - document direct-peer IP rate limiting and proxy-side per-client throttling.
- `docs/threat-model.md` - clarify reverse-proxy semantics if that document owns threat boundaries.

### Files that must not be changed
- `src/features.py` and `src/cli.py` - default migration is STAGE-004.
- `Dockerfile` and `examples/docker/docker-compose.yml` - Docker behavior changes are STAGE-008.
- `.github/workflows/**` - CI/release changes are later stages.
- `.env*`, credentials, keys, certificates - secrets are out of scope.

## Dependencies
- Depends on: STAGE-001
- Blocks: STAGE-003, STAGE-004, STAGE-008, STAGE-010

## Implementation steps
1. Draft an ADR using the analysis recommendation: new-user direction is `workspace`, `lab` remains explicit opt-in, and untrusted exposure is unsupported unless operators provide auth/TLS/firewall/proxy controls.
2. Record compatibility expectations for scripts relying on implicit `lab` behavior and the migration note required before STAGE-004.
3. Document direct-peer IP semantics for app-side Basic Auth throttling and state that proxied deployments require proxy-side per-client rate limiting.
4. Add or update a short profile decision table in README/docs: `serve` for read-only sharing, `workspace` for normal file workspace, `lab` for experiments.
5. State whether Docker is currently an example/operator convenience or a supported published artifact.
6. Run docs checks and update planning status/report.

## Acceptance criteria
- [ ] An ADR or equivalent decision document states the default-profile direction and compatibility plan.
- [ ] README/docs include a first-path profile table for `serve`, `workspace`, and `lab`.
- [ ] SECURITY/threat docs explicitly say app-side auth rate limiting keys on direct TCP peer IP.
- [ ] Proxied deployments require proxy-side per-client throttling unless a future trusted-proxy model is added.
- [ ] Docker status is documented as example/operator convenience or supported artifact.

## Verification plan
| Check | Command or method | Expected result |
|---|---|---|
| Docs mirror check | `python tools/sync_docs.py --check` | Exits 0. |
| Stale-doc check | `python tools/check_stale_docs.py` | Exits 0. |
| Optional docs build | `mkdocs build --strict` | Exits 0 if MkDocs dependencies are installed. |
| Manual/static review | Read ADR, README, SECURITY, threat model text | Policy is explicit and no runtime default changed. |

## Suggested subagents
- `explorer` - inspect existing ADR format and profile/security docs.
- `worker` - draft decision docs and sync mirrors.
- `security-reviewer` - review proxy/client-IP language if available.

## Risks and rollback
- Risk: maintainers may reject the recommended `workspace` default.
- Rollback: revise the ADR to preserve `lab` default and mark STAGE-004 as a no-default-flip hardening stage before closing dependent stages.

## Completion notes
Filled by `close-plan-stage`.
