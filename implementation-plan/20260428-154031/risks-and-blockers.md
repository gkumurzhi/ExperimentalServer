# Risks and Blockers

| Risk | Affected stages | Mitigation |
|---|---|---|
| Dirty worktree contains many existing modifications | All stages | Before closing a stage, inspect touched files and preserve user-owned changes; avoid broad reverts. |
| Context7 quota was limited in late analysis | Docs/framework-specific stages | Use official docs or retry Context7 only when stage behavior depends on external current guidance. |
| Some verification tools may be unavailable locally | CI, Docker, browser smoke, MkDocs stages | Record unavailable commands in closure reports and use static review plus CI-targeted commands. |
| Runtime data must not be read | STAGE-007, STAGE-025 and any storage tests | Use dummy fixture paths/temp directories only; never inspect actual `uploads/` or `notes/` contents. |
| Dependency policy requires a team decision | STAGE-020, STAGE-021 | Default to constraints-first unless user explicitly chooses uv-first. |
| Protocol hardening can break non-compliant clients | STAGE-004, STAGE-016, STAGE-017 | Add clear tests and document behavior; rollback individual protocol stages if compatibility risk is unacceptable. |
