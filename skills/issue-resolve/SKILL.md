---
name: issue-resolve
description: Continue an issue-flow case from handoff into implementation, verification, or a final non-code disposition. Use when a case already has `handoff.xml` and the user wants to fix, verify, or close it.
---

# Issue Resolve

Thin entry skill for Stage 3 of the issue-flow system.

The design-time source for the shared workflow lives in this skills repo, but
the runtime workflow lives inside the current project. Resolve the current git
repository root first, then use or bootstrap `<repo-root>/.issue-flow-core/`
before proceeding.

## Step 1: Load Project Context (Required)

Before resolve work, re-read and prove the project-level context:

<action tool="read_file">
<repo-root>/ISSUE_CONTEXT.md
</action>

If present, prove you read the key sections relevant to resolution:

<proof file="ISSUE_CONTEXT.md" section="Common Issue Patterns" preview="### Recurring Problems..." />
<proof file="ISSUE_CONTEXT.md" section="Critical Areas" preview="Areas that require extra..." />
<proof file="ISSUE_CONTEXT.md" section="Architecture Notes" preview="### Key Components..." />
<proof file="ISSUE_CONTEXT.md" section="Environment Context" preview="### Development..." />

If `ISSUE_CONTEXT.md` does not exist, note this explicitly before proceeding.

## Step 2: Load Core Workflow Files

<action tool="read_file">
../issue-flow-core/workflows/resolve/resolve-workflow.md
</action>

<proof file="resolve-workflow.md" lines="1-10" preview="# Resolve Workflow..." />

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

## Step 3: Load Templates and Scripts (When Needed)

- `../issue-flow-core/templates/resolve/`
- `../issue-flow-core/scripts/check_readiness.py`

## Mission

Optionally continue from `analysis/handoff.xml` into:

- a code or config change
- a verified non-code conclusion
- an external disposition

Record the result in:

- `resolve/resolution.xml`
- `resolve/verification.md`

## Non-Negotiables

- **Prove context loading**: You must provide `<proof>` tags showing you read `ISSUE_CONTEXT.md` and core workflow files before resolve work begins.
- Require an existing handoff before resolve work starts.
- Runtime assets live in `<repo-root>/.issue-flow-core/`, not in the installed skills directory.
- If `.issue-flow-core/` is missing, bootstrap it before workflow execution.
- Re-read the repo-level `ISSUE_CONTEXT.md` when present before implementation.
- Present the proposed solution and obtain explicit user approval before any repository change.
- Only resolve may modify the project repository.
- Do not rewrite prior collect or handoff artifacts as a substitute for resolution output.
- Record verification state explicitly for every outcome.
- Do not make external tracker sync a prerequisite for finishing resolve. External submission belongs to optional follow-up skills.

## Exit

- Move to `resolved_verified` or `resolved_unverified` when the outcome is explicit.
- Close the case only when `close_ready` passes and the next action is explicit.
- If the user wants to sync the resolved case into Overmind, hand off to the optional plugin skill `../issue-overmind-sync` after resolve artifacts are complete.
