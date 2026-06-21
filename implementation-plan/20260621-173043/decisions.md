# Planning Decisions

| Decision | Rationale | Alternatives rejected |
|---|---|---|
| Create a fresh implementation-plan run instead of reopening `implementation-plan/20260615-011753` | The previous active plan is fully CLOSED, and the new analysis introduces a different body of work | Reusing the old plan would blur historical closure state and new work |
| Repair the SMUGGLE runtime path before UI simplification | The report confirms a real browser-visible defect under current CSP; UI polish on top of a broken artifact path would hide the main failure | Starting with button labels or broader layout cleanup first |
| Keep `lab` gating, `public_direct` rejection, and the global UI CSP as non-goals for the near-term stages | The analysis consistently treats these boundaries as strengths that must not be weakened to make the artifact flow easier | Expanding profile exposure, allowing `lab` under `public_direct`, or relaxing `script-src 'self'` across the UI |
| Split operator framing from plugin/config policy work | README/CLI/docs guardrails and plugin/config behavior touch different review surfaces and verification commands | One large mixed stage spanning docs, UI, plugin runtime, and config semantics |
| Defer broader request-panel density changes to backlog | The artifact flow, docs framing, and plugin/config boundaries are concrete and verifiable; the broader panel simplification is valid but less bounded | Promoting a subjective layout refactor to the same priority as the verified runtime defect |
