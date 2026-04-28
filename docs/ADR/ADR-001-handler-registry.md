# ADR-001: Handler dispatch via registry, not mixin inheritance

- **Status:** accepted (2026-04-14)
- **Supersedes:** the original `class ExperimentalHTTPServer(HandlerMixin)` design

## Context

The server originally composed five mixin classes (`FileHandlersMixin`,
`InfoHandlersMixin`, `NotepadHandlersMixin`, `AdvancedUploadHandlersMixin`,
`SmuggleHandlersMixin`) into a single `HandlerMixin`, and the server
inherited from it. Adding a new handler meant creating a mixin, inserting it
into the MRO, and registering the method name in a plain `dict` inside the
server constructor.

Problems:

- Mixins share MRO with the server, so every handler implicitly depends on
  all server attributes (sockets, TLS, rate limiter). This complicates unit
  testing — you cannot instantiate a handler without a live server.
- Experimental custom-method routing required special-cased lookup in early
  drafts because the static `method_handlers` dict could not be extended at
  runtime in a first-class way.
- No way to introspect which methods are available without reflection.

## Decision

Introduce `HandlerRegistry` (implements `Mapping[str, Callable]`) as the
single source of truth for method → handler resolution. The server keeps the
`HandlerMixin` inheritance for now, but the canonical registry is built by
`HandlerMixin.build_method_handlers()` so routing stays owned by the handler
layer instead of `ExperimentalHTTPServer.__init__`.

Full disentanglement of the mixin would require passing server state
(root_dir, locks, metrics) explicitly into each handler's constructor. That
is a larger change and is deferred.

## Consequences

### Positive

- `server.method_handlers` remains a `Mapping`, so existing tests and the
  INFO handler work unchanged.
- Routing becomes testable in isolation through small `HandlerMixin` stubs
  that use the same registry builder as the real server.

### Negative

- Handlers still rely on `self.root_dir`, `self.upload_dir`, etc., so full
  dependency injection remains a future step.
- One extra indirection (`registry.get_handler(method)` vs `dict.get(method)`).
