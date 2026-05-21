# Implementation Plan Run

- Active plan: `implementation-plan/20260521-212008`
- Source analysis: `stash@{0}^3:codex-analysis/20260521-144908/project-analysis-report.md`
- Baseline plan status: `implementation-plan/20260505-205639/stage-status.md` with STAGE-010 through STAGE-013 closed
- Generated: 2026-05-21 21:20:08 MSK

## Usage

Close one stage at a time:

```text
$close-plan-stage STAGE-001
```

Run a dry-run first when using the multi-stage runner:

```text
$close-plan-stages --stages-dir implementation-plan/20260521-212008/stages --all-open --dry-run
```
