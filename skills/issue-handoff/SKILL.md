---
name: issue-handoff
description: Build a traceable investigation and downstream handoff from an existing issue-flow case. Use when curated evidence already exists and the user wants synthesis, analysis, or a handoff package for another engineer or later session.
---

# Issue Handoff

Thin entry skill for Stage 2 of the issue-flow system.

The design-time source for the shared workflow lives in this skills repo, but
the runtime workflow lives inside the current project. Resolve the current git
repository root first, then use or bootstrap `<repo-root>/.issue-flow-core/`
before proceeding.

## Load These Core Files First

- `../issue-flow-core/workflows/handoff/handoff-workflow.md`
- `../issue-flow-core/workflows/actions/lifecycle-management.md`
- `../issue-flow-core/knowledge/issue-flow-principles.md`
- `../issue-flow-core/knowledge/artifact-contracts.md`

Load templates and scripts only when needed:

- `../issue-flow-core/templates/analysis/`
- `../issue-flow-core/templates/ISSUE_CONTEXT.md` as the project-level file template only
- `../issue-flow-core/scripts/check_readiness.py`

## Mission

Work from the curated case workspace to produce:

- `analysis/investigation.xml`
- `analysis/handoff.xml`
- `analysis/next-step.yaml`

## Non-Negotiables

- Start from the shared `.issue-flow/cases/<case-id>/` workspace.
- Runtime assets live in `<repo-root>/.issue-flow-core/`, not in the installed skills directory.
- If `.issue-flow-core/` is missing, bootstrap it before workflow execution.
- Use curated evidence as the default working set. Reopen raw sources only when policy allows it.
- Read the repo-level `ISSUE_CONTEXT.md` directly when present; do not create a case-local copy.
- Keep repository reads evidence-driven and record them as direct repository references.
- Do not copy repository code into the case workspace in v1.
- Handoff is read-only against both issue-material roots and the repository.

## Exit

- If handoff is complete and `handoff_ready` passes, continue with `issue-resolve` or close externally based on `next-step.yaml`.
- If new evidence invalidates the handoff, move the case back to the appropriate earlier lifecycle state.
