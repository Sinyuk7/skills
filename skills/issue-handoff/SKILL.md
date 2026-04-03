---
name: issue-handoff
description: Build a traceable investigation and downstream handoff from an existing issue-flow case. Use when curated evidence already exists and the user wants synthesis, analysis, or a handoff package for another engineer or later session. Do not use for fresh issue intake, collecting raw materials, implementing fixes, or syncing to trackers.
---

# Issue Handoff

Thin entry skill for Stage 2 of the issue-flow system.

Workflow docs, templates, and scripts are defined in this skills repo.
At runtime inside the project, the only issue-flow working state lives under
`.issue-flow/cases/<case-id>/`, plus optional project-level `ISSUE_CONTEXT.md`.
Resolve the current git repository root first, then read workflow docs,
templates, and scripts from the installed skill directory.

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
- **Prove log reading** (CRITICAL): For each curated log file, investigation.xml MUST contain 1-2 representative lines extracted from that log as `<log_excerpt>` elements. Each `log_excerpt` must include `id`, `source`, and `lines`; `timestamp` is optional but recommended. This is mandatory evidence-chain proof that logs were actually read and analyzed, not just referenced.
- **Bind facts to log evidence** (CRITICAL): Any fact derived from log evidence must include `source_excerpt`, and that excerpt must come from the same log file referenced by the fact's `ref`.
- Start from the shared `.issue-flow/cases/<case-id>/` workspace.
- Do not create or depend on a separate repo-local `.issue-flow-core/` directory.
- Read workflow docs, templates, and scripts from the installed skills directory.
- Use curated evidence as the default working set. Reopen raw sources only when policy allows it.
- Keep repository reads evidence-driven and record them as direct repository references.
- Use repository references rather than copying code into case workspace.
- Handoff is read-only against both issue-material roots and the repository.

## Exit

- If handoff is complete and `handoff_ready` passes, continue with `issue-resolve` or close externally based on `next-step.yaml`.
- If new evidence invalidates the handoff, move the case back to the appropriate earlier lifecycle state.
