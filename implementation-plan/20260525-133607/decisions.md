# Planning Decisions

| Decision | Rationale | Alternatives rejected |
|---|---|---|
| Split resource safety into storage, body memory, and slow-transfer stages | These risks have different code paths and verification methods; each can be closed independently | One large "resource safety" epic would be too broad for `close-plan-stage` |
| Put auth secret handling before feature profiles | Profiles reduce blast radius, but service credentials must stop leaking through argv before container examples are promoted | Deferring secrets until Docker stage would leave auth examples unsafe |
| Use `--auth-file` as the primary planned secret source | It maps cleanly to Docker secrets and avoids environment/argv leakage | `--auth-env` may still leak through env inspection; stdin is awkward for services |
| Keep wildcard CORS as read CORS only | Analysis evidence shows wildcard should not be treated as trust for browser mutations or WebSocket upgrades | Continuing current wildcard write/WS behavior was rejected as unsafe for service deployments |
| Keep Docker image binding to `0.0.0.0` inside the container | The Docker report notes this is correct for container port publishing | Changing image CMD to `127.0.0.1` would break normal Docker usage |
| Make Compose safer with host-loopback publishing and explicit external profiles | This reduces accidental broad exposure without breaking the image | Publishing plain HTTP on all host interfaces by default was rejected |
| Plan release artifacts before package rename | Installed-wheel smoke and release workflow make package migration failures easier to catch | Renaming first would increase debugging surface |
| Preserve prior implementation-plan directories | Existing plans and reports are traceability artifacts | Overwriting older plan runs was rejected |

