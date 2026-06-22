# Safe Lab-Only SMUGGLE Builder Design

## Goal

Add a safe `lab`-only artifact builder on top of the existing `SMUGGLE`
workflow so operators can generate neutral internal test artifacts with:

- a curated output filename extension
- a small set of safe delivery presets
- bounded text and timing overrides
- the existing one-shot artifact and optional XOR flow

This is not a general HTML builder and not a deceptive delivery framework.

## Current State

Today the UI exposes a narrow SMUGGLE flow:

- the source must already exist in `uploads/`
- the operator can only choose whether XOR protection is enabled
- the server generates a one-shot `smuggle_*.html` file
- the result dialog exposes the artifact URL plus open/copy/save actions

The API contract is also narrow:

- `SMUGGLE /uploads/<file>`
- optional `?encrypt=1`
- JSON response with `url`, `file`, `encrypted`, and optional `password`

## Desired Outcome

The new builder keeps the same source model and one-shot artifact model, but
adds a safe, structured configuration layer for:

- output display name
- output extension from a curated allowlist
- a safe delivery preset
- bounded text overrides
- bounded delay control
- explicit test-artifact labeling

The result remains a temporary same-origin `smuggle_*.html` artifact.

## Non-Goals

The first version explicitly does not support:

- arbitrary HTML, CSS, or JavaScript authoring
- user-provided templates
- deceptive or impersonating copy
- fake viewers, update prompts, login prompts, or spoofed chrome
- external redirects
- hidden or unlabeled auto-download behavior
- configuration-driven extension policy
- a new endpoint separate from `SMUGGLE`

## Safety Boundary

The builder is limited to the `lab` profile and must be positioned as an
internal operator test tool.

Required safety rules:

- source file must already exist in `uploads/`
- all generated pages must contain a visible test-artifact marker
- text fields are escaped, length-bounded, and never treated as HTML
- extension changes are limited to a fixed server-side allowlist
- presets are fixed and server-rendered
- same-origin one-shot artifact semantics remain unchanged

## Allowed Extension Policy

The first version uses a fixed curated allowlist:

- `.txt`
- `.bin`
- `.dat`
- `.zip`
- `.pdf`

The UI may show these as labels, but the server is the authority. Any extension
outside this allowlist returns `400`.

The selected extension only affects the download-facing name shown by the
generated artifact. It does not rewrite the underlying bytes.

## UX Design

The builder replaces the narrow SMUGGLE modal with an expanded modal while
preserving the same entry point in the files browser.

The modal has five sections.

### 1. Source

Read-only metadata:

- source path
- source filename
- source size
- explicit `Lab-only test artifact` badge

### 2. Delivery Name

Editable fields:

- `Base name`
- `Extension`

The UI shows a live combined preview such as `Quarterly-Report.pdf`.

### 3. Safe Preset

The first version supports three safe presets:

- `direct`
  Immediate download on page load with visible test-artifact labeling.
- `card_manual`
  A neutral info card plus an explicit download button.
- `card_auto`
  A neutral info card plus a visible countdown before auto-download.

### 4. Advanced Options

Safe bounded overrides:

- `Title`
- `Body text`
- `Primary button label`
- `Auto-download delay`
- `Show explicit test-artifact notice`
- `XOR`

These options are only enabled where the selected preset can use them.

### 5. Preview And Generate

The modal includes:

- a live safe-page preview
- a structured summary of the request contract
- a single `Generate artifact` action

## Generated Page Rules

Every generated page must:

- remain same-origin
- remain one-shot
- include a visible test-artifact banner or notice
- use only server-owned safe templates
- trigger download through the existing embedded-payload mechanism

If XOR is enabled, the current server-generated password contract stays in
place.

## Server Contract

The builder extends the existing `SMUGGLE /uploads/<file>` request rather than
introducing a new endpoint.

Recommended query parameters:

- `encrypt=1`
- `download_name=<base name>`
- `download_ext=<allowlisted extension without dot>`
- `preset=direct|card_manual|card_auto`
- `title=<escaped text>`
- `message=<escaped text>`
- `cta_label=<escaped text>`
- `delay_ms=<integer>`
- `show_notice=1`

Validation rules:

- `download_ext` must be allowlisted
- `preset` must be known
- `download_name`, `title`, `message`, and `cta_label` must be length-bounded
- `delay_ms` must stay within a safe range such as `0..10000`
- `card_auto` must still render visible test-artifact labeling

Invalid builder parameters return `400` JSON with explicit validation details.

Successful responses remain backward-compatible:

- `url`
- `file`
- `encrypted`
- optional `password`
- `X-Smuggle-URL`

## Rendering Strategy

Server-side rendering remains authoritative.

The server:

1. validates the source file and builder parameters
2. resolves the effective preset and safe text model
3. calls a server-owned template generator
4. writes the resulting one-shot HTML as `smuggle_*.html`
5. returns the same JSON structure used today

This keeps the builder deterministic, testable, and safe from arbitrary markup
injection.

## Compatibility

Backward compatibility requirements:

- legacy `SMUGGLE` requests without builder parameters continue to work
- current result dialog semantics remain valid
- current temp-retention and one-shot cleanup behavior remain valid
- current XOR behavior remains valid

## Testing Strategy

### Server Tests

Add coverage for:

- allowlisted extension acceptance
- non-allowlisted extension rejection
- invalid preset rejection
- invalid `delay_ms` rejection
- oversized text field rejection
- legacy SMUGGLE compatibility
- generated HTML visible test-artifact marker
- preset-specific behavior rendering
- builder parameters combined with `encrypt=1`

### Browser Smoke

Add coverage for:

- expanded builder modal opens from the current files action
- extension and preset selectors update the preview
- generated result dialog reflects the chosen download-facing name
- a safe preset creates a working artifact
- focus and accessibility contracts remain intact

### Documentation

Update:

- `docs/api.md`
- `docs/security.md`
- stale-doc guards if builder terminology becomes part of supported guidance

## Rollout

The first version ships only for `lab`.

Rollout expectations:

- preserve the legacy SMUGGLE contract
- expose the safe builder as the default UI over the current artifact action
- keep the server contract backward-compatible
- document the feature as an internal test-artifact generator, not a delivery
  workflow

## Open Items Deferred To Later Versions

These are intentionally postponed:

- config-driven extension allowlists
- additional safe presets
- richer preview fidelity
- request-panel integration beyond the current demo flow
- policy-controlled builder enablement outside the current `lab` boundary
