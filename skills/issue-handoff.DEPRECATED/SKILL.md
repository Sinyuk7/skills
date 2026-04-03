---
name: issue-handoff-deprecated
description: Historical migration note for the retired issue-handoff stage. Use issue-investigate instead.
---

# DEPRECATED

This skill has been replaced by `issue-investigate`.

The old 3-stage workflow (Collect → Handoff → Resolve) has been simplified to a 2-stage workflow (Collect → Investigate → Resolve).

**Use `issue-investigate` instead.**

## Migration

If you have existing cases with `handoff.xml`:
- The root cause analysis in `handoff.xml` maps to `investigation.md`
- The next_step recommendation is now in `case.yaml`
- No data migration needed—just use new skills for new cases
