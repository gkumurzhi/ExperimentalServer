# ADR-007: Published artifact surfaces and operator-owned deployment boundary

- **Status:** accepted

## Context

The repository now has a tagged release workflow that builds verified wheel and
sdist artifacts, publishes the `exphttp` Python package to PyPI through Trusted
Publishing/OIDC, and publishes the `ghcr.io/gkumurzhi/exphttp` container image
with provenance/SBOM metadata. At the same time, several top-level docs still
describe the release lane as artifact-only or imply that public publication is
not configured.

That drift creates two risks:

1. operators and contributors cannot tell which acquisition surfaces are
   actually supported;
2. readers may incorrectly infer that a published package or image implies a
   managed or internet-safe deployment story.

The project already separates safe-default exposure policy from artifact
distribution in ADR-006. This ADR makes the artifact boundary explicit.

## Decision

The supported artifact surfaces are:

1. local development installs from a checkout (`pip install -e .`);
2. tagged PyPI releases of the `exphttp` package;
3. signed wheel/sdist/SBOM artifacts uploaded by the `Release Artifacts`
   workflow;
4. tagged GHCR images at `ghcr.io/gkumurzhi/exphttp`.

Manual `workflow_dispatch` runs of `Release Artifacts` are verification lanes:
they build and attest the same wheel/sdist/SBOM outputs, but they do not
publish PyPI or GHCR artifacts unless the run is associated with a release tag.

Published artifacts do **not** change the operator-owned deployment boundary.
They are supported ways to acquire the software, not a statement that exposed
internet deployment is safe by default. Profile selection, TLS, authentication,
proxy controls, resource limits, and rollback remain operator responsibilities
as described in `SECURITY.md` and ADR-006.

Rollback expectations are:

- Python package rollbacks pin a previous verified version and, when needed,
  use preserved wheel/sdist artifacts outside the GitHub Actions retention
  window.
- Container rollbacks pin a previous verified GHCR digest, not a floating tag.

## Consequences

### Positive

- README, SECURITY, CONTRIBUTING, and docs-site install guidance can align to
  the real release workflow.
- Future API, proxy, and publishing decisions start from one explicit artifact
  boundary instead of repeating backlog prose.
- Operators can distinguish “supported distribution surface” from “supported
  internet deployment posture”.

### Negative

- Maintainers now explicitly own the health of tagged PyPI and GHCR publishing
  as supported distribution surfaces.
- Docs must stay careful not to equate publication with hosted-service support
  or safe public exposure.

### Follow-up

- Trusted-proxy and public-client decisions should reference this ADR instead
  of restating distribution support assumptions.
- If release topology changes again, update this ADR or supersede it with a new
  artifact-policy ADR rather than letting docs drift silently.
