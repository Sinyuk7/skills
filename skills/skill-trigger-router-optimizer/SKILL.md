---
name: skill-trigger-router-optimizer
description: |
  Analyze and refactor the routing surface of a SKILL collection.
  Use when examining trigger overlap, missing boundaries, ambiguous delegation,
  subagent selection, dispatch policy design, or why a skill is not triggering
  or is triggering too often. Do not use for execution-step refactors,
  evidence-chain grounding, generic prompt polishing, or direct code changes.
  Use proactively when a user is reorganizing a skill library or debugging
  routing quality across multiple skills.
---

# Skill Trigger Router Optimizer

Optimize which skill should run, when it should run, and how routing quality is evaluated.

## Intent Dispatch

| Intent | Workflow |
|--------|----------|
| Audit routing surface for a skill collection | `workflows/router-optimization.md` |
| Rewrite routing metadata and boundaries | `workflows/router-optimization.md` |
| Generate routing eval cases | `workflows/router-optimization.md` |

## Execution

1. Load the target skill set and inventory only routing-relevant signals first.
2. Build the intent surface, overlap map, and routing pattern recommendations.
3. Rewrite metadata after the boundary analysis is stable.
4. Generate routing eval cases before declaring the design complete.

## Resources

- `knowledge/routing-patterns.md` - Routing modes and decision heuristics
- `knowledge/observability-hooks.md` - Routing traces, metrics, and iteration hooks
- `templates/routing-audit.md` - Audit report structure
- `templates/rewrite-proposals.md` - Metadata rewrite format
- `templates/routing-matrix.json` - Structured overlap and gap map
- `templates/routing-evals.json` - Trigger eval schema
- `templates/router-policy.md` - Global dispatch and arbitration rules
- `templates/conflict-register.md` - Ongoing overlap and tie-break record
