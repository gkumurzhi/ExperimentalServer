# Verification Matrix

| Stage | Required checks | Optional checks | Known blockers | Baseline needed? |
|---|---|---|---|---|
| STAGE-001 | `python tools/check_stale_docs.py` | `python tools/sync_docs.py --check` | Public-support stance may intentionally stay narrow; that is acceptable if docs/ADR are explicit. | No |
| STAGE-002 | `python tools/check_stale_docs.py` | `python tools/sync_docs.py --check` | Direct-peer semantics may remain the final supported stance. | No |
| STAGE-003 | `python tools/check_stale_docs.py` | `python tools/sync_docs.py --check` | Recovery may be deferred instead of approved if no safe model is accepted. | No |
| STAGE-004 | `python tools/sync_docs.py --check` | `python tools/check_stale_docs.py` | API/client strategy may remain legacy-v0-only if public-client support is not chosen. | No |
