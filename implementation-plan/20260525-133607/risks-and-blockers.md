# Risks and Blockers

| Risk | Affected stages | Mitigation |
|---|---|---|
| Default profile may be backward-incompatible if changed from all-features lab behavior | STAGE-006, STAGE-007, STAGE-008 | Keep compatibility default only if required, but make safer profiles explicit in Docker/docs; record decision in docs/tests |
| Storage quota defaults are product decisions, not purely technical choices | STAGE-001, STAGE-002 | Add explicit CLI/config knobs and choose conservative documented defaults; avoid silent unlimited writes in service examples |
| Full streaming upload may exceed one focused stage | STAGE-003 | Minimum acceptance is process-wide in-flight memory reservation; deeper streaming can be follow-up if needed |
| Docker may not be available on every local runner | STAGE-008, STAGE-009 | Include Docker commands as required when Docker is available; if unavailable, record skipped commands and CI-equivalent checks |
| PyPI/GHCR publication intent is not confirmed | STAGE-009 | Build and attest artifacts without publishing by default; gate real publish on tags and explicit repository secrets/OIDC setup |
| Package rename can break downstream `from src` users | STAGE-010 | Keep a compatibility shim and stale-doc guard unless the owner explicitly accepts a breaking release |
| Context7 docs were used by the analysis report, but this planning run did not re-query external docs | All | Treat external docs claims as inherited from the cited analysis artifacts; re-check docs during implementation if API semantics are uncertain |

