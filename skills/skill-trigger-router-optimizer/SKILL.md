---
name: skill-trigger-router-optimizer
description: |
  Analyze and refactor the routing surface of a SKILL collection.
  Use when auditing trigger overlap, missing boundaries, ambiguous delegation,
  subagent selection, dispatch policy design, hidden secondary intents, or why
  a skill is not triggering, is triggering too often, or should not participate
  in routing at all. Distinguish user-facing skills from shared cores, plugins,
  stance-driven mode skills, and non-routable references before proposing fixes.
  Do not use for execution-step refactors, evidence-chain grounding, generic
  prompt polishing, or direct code changes.
  Use proactively when a user is reorganizing a skill library or debugging
  routing quality across multiple skills.
---

# Skill Trigger Router Optimizer

Optimize which skill should run, when it should run, and how routing quality is evaluated.

## Intent Dispatch

| Intent | Workflow |
|--------|----------|
| Audit routing surface for a skill collection | `workflows/router-optimization.md` |
| Classify routable vs shared core vs reference vs stance-driven | `workflows/router-optimization.md` |
| Rewrite routing metadata and boundaries | `workflows/router-optimization.md` |
| Generate routing eval cases | `workflows/router-optimization.md` |

## Execution

1. Load the target skill set and inventory only routing-relevant signals first.
2. Classify each target as routable, shared core, plugin, non-routable reference, or stance-driven mode skill.
3. Find overlap, gaps, hidden secondary intents, and mode-switch boundaries.
4. Rewrite metadata only after routing ownership is stable.
5. Generate routing eval cases before declaring the design complete.

## Resources

- `knowledge/routing-patterns.md` - Routing modes and decision heuristics
- `knowledge/observability-hooks.md` - Routing traces, metrics, and iteration hooks
- `templates/routing-audit.md` - Audit report structure
- `templates/rewrite-proposals.md` - Metadata rewrite format
- `templates/routing-matrix.json` - Structured overlap and gap map
- `templates/routing-evals.json` - Trigger eval schema
- `templates/router-policy.md` - Global dispatch and arbitration rules
- `templates/conflict-register.md` - Ongoing overlap and tie-break record
- `evals/evals.json` - Regression prompts for router-optimizer quality
