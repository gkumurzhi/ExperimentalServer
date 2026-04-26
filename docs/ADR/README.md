# Architecture Decision Records

Short, dated notes on design decisions that are not self-evident from the
code. Each ADR follows the format:

- **Status** — `proposed`, `accepted`, `deprecated`, or `superseded by ADR-NNN`
- **Context** — what forces are at play
- **Decision** — what we chose
- **Consequences** — trade-offs the decision accepts

New ADRs get the next available number. Once accepted, ADRs are **immutable**
except for status updates; to change direction, write a new ADR that
supersedes the old one.

## Index

| ID | Status | Title |
|----|--------|-------|
| [ADR-001](ADR-001-handler-registry.md) | accepted | Handler dispatch: registry over mixin inheritance |
| [ADR-002](ADR-002-advanced-upload-xor-hmac.md) | accepted | Advanced upload payload integrity: XOR + HMAC baseline |
| [ADR-003](ADR-003-cryptography-optional.md) | accepted | `cryptography` as an optional dependency |
| [ADR-004](ADR-004-uploads-relative-to.md) | accepted | Uploads-only enforcement via `Path.relative_to` |
| [ADR-005](ADR-005-threadpool-over-asyncio.md) | accepted | Concurrency model: ThreadPoolExecutor, not asyncio |
