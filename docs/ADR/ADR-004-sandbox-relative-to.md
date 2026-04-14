# ADR-004: Sandbox enforcement via `Path.relative_to`

- **Status:** accepted

## Context

Path traversal (`GET /../../etc/passwd`) is the single most common security
failure in file-serving HTTP code. Early drafts of the server used:

```python
resolved = (base / user_path).resolve()
if not str(resolved).startswith(str(base)):  # WRONG on Windows, symlinks
    raise Forbidden()
```

This has two failure modes:

1. **Prefix substring attack:** if `base = /srv/uploads` and an attacker
   mounts/resolves to `/srv/uploads-other`, the `startswith` check passes
   but the path escapes the intended directory.
2. **Case-insensitive filesystems** (macOS default, Windows) defeat naive
   string comparison.

## Decision

Use `Path.resolve().relative_to(base_dir.resolve())` and catch `ValueError`
to reject traversal:

```python
try:
    resolved.resolve().relative_to(base_dir.resolve())
except ValueError:
    raise Forbidden()
```

`relative_to` walks the path components symbolically and raises if
`resolved` is not a proper descendant of `base_dir`, which is exactly the
invariant we want.

Additionally:

- Symlinks are resolved *before* the check, so a symlink under `uploads/`
  pointing to `/etc/passwd` is rejected.
- Hidden files (`.opsec_config.json`, `.env`, …) are blocked by an explicit
  `HIDDEN_FILES` frozenset in `src/config.py`, independent of sandbox mode.
- The check is centralised in `BaseHandler._safe_join` so no handler
  implements its own path validation.

We considered chroot/container-level isolation but rejected it as
out-of-scope: the project is a library, not a runtime.

## Consequences

### Positive

- Works correctly on all filesystems Python supports.
- `ValueError` from `relative_to` is an unambiguous signal; no fragile
  string logic.
- Centralised so every handler inherits the same guarantee.

### Negative

- Every path check pays the cost of two `resolve()` calls (filesystem
  stat). For read-heavy workloads this is measurable but has not been a
  bottleneck in benchmarks.
- Does not defend against vulnerabilities in the Python `pathlib`
  implementation itself; we accept that risk and pin a modern Python.
