# Backlog and Needs-Investigation Items

| Item | Source | Why not staged now | Suggested next step |
|---|---|---|---|
| Re-group request methods or make a simpler first-run request view | `implementation-plan/20260621-173043/findings.md` F-007; `implementation-plan/20260621-173043/backlog.md` | Lower priority than product/security boundary decisions, and still partly subjective after the closed SMUGGLE UI fixes. | Revisit only if maintainers explicitly want a static-UI simplification track. |
| Frontend build pipeline | `implementation-plan/20260615-011753/backlog.md` | The static no-build UI is still adequate for the current product scope. | Reconsider only if a future UI roadmap exceeds capability-driven static controls. |
| Image vulnerability scan, image SBOM/provenance, digest rollback | `implementation-plan/20260615-011753/backlog.md` | These depend on Docker becoming a supported published artifact surface. | Replan after STAGE-001 if public image support is accepted. |
| Streaming uploads and cached quota accounting | `implementation-plan/20260615-011753/backlog.md` | Benchmark evidence does not currently justify another performance plan. | Revisit after a future benchmark or workload report shows real pressure. |
| Cursor-style large directory listing | `implementation-plan/20260615-011753/backlog.md` | Depends on product/API semantics for exact totals and listing promises. | Revisit only after API/listing semantics change. |
| Local ignored `uv.lock` drift policy | `implementation-plan/20260615-011753/backlog.md` | Lower priority than the strategic support-surface decisions. | Document or enforce only if drift keeps confusing reviews. |
