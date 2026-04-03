---
name: issue-collect
description: Create or update an issue-flow case by curating raw issue materials into `.issue-flow/cases/<case-id>/`. Use when a user provides logs, screenshots, archives, notes, or asks to start investigating a fresh issue. Do not use for synthesis, analysis, fixing, or syncing.
---

# Issue Collect

Thin entry skill for Stage 1 of the issue-flow system.

Workflow docs, templates, and scripts are defined in this skills repo.
At runtime inside the project, the only issue-flow working state lives under
`.issue-flow/cases/<case-id>/`, plus optional project-level `ISSUE_CONTEXT.md`.
Resolve the current git repository root first, then read workflow docs,
templates, and scripts from the installed skill directory.

## Step 1: Load Project Context (Required)

Before any case work, load and prove the project-level context:

<action tool="read_file">
<repo-root>/ISSUE_CONTEXT.md
</action>

If present, prove you read the key sections:

<proof file="ISSUE_CONTEXT.md" section="Common Issue Patterns" preview="### Recurring Problems..." />
<proof file="ISSUE_CONTEXT.md" section="Critical Areas" preview="Areas that require extra..." />
<proof file="ISSUE_CONTEXT.md" section="Architecture Notes" preview="### Key Components..." />

If `ISSUE_CONTEXT.md` does not exist, note this explicitly before proceeding.

## Step 2: Load Core Workflow Files

<action tool="read_file">
../issue-flow-core/workflows/collect/collect-workflow.md
</action>

<proof file="collect-workflow.md" lines="1-10" preview="# Collect Workflow..." />

<action tool="read_file">
../issue-flow-core/workflows/actions/lifecycle-management.md
</action>

<proof file="lifecycle-management.md" lines="1-10" preview="# Lifecycle and State..." />

<action tool="read_file">
../issue-flow-core/knowledge/issue-flow-principles.md
</action>

<proof file="issue-flow-principles.md" lines="1-10" preview="# Issue-Flow Principles..." />

<action tool="read_file">
../issue-flow-core/knowledge/case-id-policy.md
</action>

<proof file="case-id-policy.md" lines="1-10" preview="# case-id policy..." />

## Step 3: Load Templates and Scripts (When Needed)

- `../issue-flow-core/templates/case/`
- `../issue-flow-core/scripts/check_readiness.py`

## Prerequisites

- At least one non-repository issue input (logs, screenshots, archives, notes, etc.)
- OR existing case with incomplete evidence requiring additional collection

**Note**: The repository alone is insufficient to start a new case.

## Mission

Curate raw user-provided issue materials into a stable case workspace under:

```text
<project-root>/.issue-flow/cases/<case-id>/
```

## Non-Negotiables

- **Prove context loading**: You must provide `<proof>` tags showing you read `ISSUE_CONTEXT.md` and core workflow files before case work begins.
- Require at least one non-repository issue input before creating a case.
- Use the shared `.issue-flow/cases/<case-id>/` workspace. Do not invent stage-specific workspaces.
- Do not create or depend on a separate repo-local `.issue-flow-core/` directory.
- Read workflow docs, templates, and scripts from the installed skills directory.
- `ISSUE_CONTEXT.md` is a repo-level file and must not be copied into the case.
- If the write target is ambiguous, stop and ask the user which case should own the write.
- Keep repository exploration evidence-driven.
- Collect may modify user-provided issue-material roots in v1, but it must not modify the project repository.

## Exit

- If collect is complete and `collect_ready` passes, hand off to `issue-handoff`.
- If evidence is incomplete or ambiguous, keep the case in `collecting` or `blocked`.
