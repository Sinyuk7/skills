---
name: issue-handoff
description: DEPRECATED - Compatibility shim for older issue-flow prompts. Use issue-investigate instead.
---

# Handoff

This compatibility shim is kept so older prompts and evals that still reference `issue-handoff` continue to resolve.

Use `issue-investigate` for new cases. Existing handoff cases should migrate their analysis to `investigation.md`, with next-step state tracked in `case.yaml`.

## Migration

- `handoff.xml` root cause analysis maps to `investigation.md`
- `next_step` recommendation now lives in `case.yaml`
- No data migration is required for old cases
