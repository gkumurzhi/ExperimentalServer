# ADR-001: Handler dispatch via registry, not mixin inheritance

- **Status:** accepted (2026-04-14)
- **Supersedes:** the original `class ExperimentalHTTPServer(HandlerMixin)` design

## Context

The server originally composed five mixin classes (`FileHandlersMixin`,
`InfoHandlersMixin`, `NotepadHandlersMixin`, `OpsecHandlersMixin`,
`SmuggleHandlersMixin`) into a single `HandlerMixin`, and the server
inherited from it. Adding a new handler meant creating a mixin, inserting it
into the MRO, and registering the method name in a plain `dict` inside the
server constructor.

Problems:

- Mixins share MRO with the server, so every handler implicitly depends on
  all server attributes (sockets, TLS, rate limiter). This complicates unit
  testing — you cannot instantiate a handler without a live server.
- OPSEC-mode random method names required special-cased lookup (`_get_opsec_handler`),
  because the static `method_handlers` dict could not be extended at runtime
  in a first-class way.
- No way to introspect which methods are available without reflection.

## Decision

Introduce `HandlerRegistry` (implements `Mapping[str, Callable]`) as the
single source of truth for method → handler resolution. The server keeps the
`HandlerMixin` inheritance for now — bound methods are registered into the
registry at construction time — but new handlers can be added from outside
the class via `server.method_handlers.register(...)`.

Full disentanglement of the mixin would require passing server state
(root_dir, locks, metrics) explicitly into each handler's constructor. That
is a larger change and is deferred.

## Consequences

### Positive

- Dynamic registration (OPSEC-mode methods, plugin handlers) is now
  ergonomic.
- `server.method_handlers` remains a `Mapping`, so existing tests and the
  INFO handler work unchanged.
- Routing becomes testable in isolation — pass a plain registry and dispatch
  without instantiating the server.

### Negative

- Handlers still rely on `self.root_dir`, `self.upload_dir`, etc., so full
  dependency injection remains a future step.
- One extra indirection (`registry.get_handler(method)` vs `dict.get(method)`).
