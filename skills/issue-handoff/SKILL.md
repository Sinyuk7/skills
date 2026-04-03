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

## Step 1: Load Core Workflow Files

<action tool="read_file">
../issue-flow-core/workflows/handoff/handoff-workflow.md
</action>

<proof file="handoff-workflow.md" lines="1-10" preview="# Handoff Workflow..." />

<action tool="read_file">
../issue-flow-core/workflows/actions/lifecycle-management.md
</action>

<proof file="lifecycle-management.md" lines="1-10" preview="# Lifecycle and State..." />

<action tool="read_file">
../issue-flow-core/knowledge/issue-flow-principles.md
</action>

<proof file="issue-flow-principles.md" lines="1-10" preview="# Issue-Flow Principles..." />

<action tool="read_file">
../issue-flow-core/knowledge/artifact-contracts.md
</action>

<proof file="artifact-contracts.md" lines="1-10" preview="# artifact contracts..." />

## Step 2: Load Templates and Scripts (When Needed)

- `../issue-flow-core/templates/analysis/`
- `../issue-flow-core/scripts/check_readiness.py`

## Mission

Work from the curated case workspace to produce:

- `analysis/investigation.xml`
- `analysis/handoff.xml`
- `analysis/next-step.yaml`

## Non-Negotiables

- **Prove workflow loading**: You must provide `<proof>` tags showing you read core workflow files before handoff work begins.
- Start from the shared `.issue-flow/cases/<case-id>/` workspace.
- Runtime assets live in `<repo-root>/.issue-flow-core/`, not in the installed skills directory.
- If `.issue-flow-core/` is missing, bootstrap it before workflow execution.
- Use curated evidence as the default working set. Reopen raw sources only when policy allows it.
- Keep repository reads evidence-driven and record them as direct repository references.
- Do not copy repository code into the case workspace in v1.
- Handoff is read-only against both issue-material roots and the repository.

## Exit

- If handoff is complete and `handoff_ready` passes, continue with `issue-resolve` or close externally based on `next-step.yaml`.
- If new evidence invalidates the handoff, move the case back to the appropriate earlier lifecycle state.
