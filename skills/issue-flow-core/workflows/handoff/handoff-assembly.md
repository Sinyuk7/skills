# handoff-assembly

Purpose:

- assemble a complete handoff from case artifacts
- capture recommended next actions without forcing a resolve stage

Expected outputs:

- `analysis/handoff.xml`
- `analysis/handoff.xml` includes the downstream `next_step` recommendation

Rules:

- dependencies indicate readiness, not mandatory advancement
- handoff should include project context, findings, and code map references
- refine and evaluate should operate on the same case workspace
