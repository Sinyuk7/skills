---
name: issue-collect
description: Create or update an issue-flow case by curating raw issue materials into `.issue-flow/cases/<case-id>/`. Use when a user provides logs, screenshots, archives, notes, or asks to start investigating a fresh issue.
---

# Issue Collect

Thin entry skill for Stage 1 of the issue-flow system.

Shared logic lives in `../issue-flow-core/`. Use this skill as the user-facing entrypoint, then load the shared core files you need.

## Load These Core Files First

- `../issue-flow-core/workflows/collect/collect-workflow.md`
- `../issue-flow-core/workflows/actions/lifecycle-management.md`
- `../issue-flow-core/knowledge/issue-flow-principles.md`
- `../issue-flow-core/knowledge/case-id-policy.md`

Load templates and scripts only when needed:

- `../issue-flow-core/templates/case/`
- `../issue-flow-core/templates/ISSUE_CONTEXT.md`
- `../issue-flow-core/scripts/check_readiness.py`

## Mission

Curate raw user-provided issue materials into a stable case workspace under:

```text
<project-root>/.issue-flow/cases/<case-id>/
```

## Non-Negotiables

- Require at least one non-repository issue input before creating a case.
- Use the shared `.issue-flow/cases/<case-id>/` workspace. Do not invent stage-specific workspaces.
- If the write target is ambiguous, stop and ask the user which case should own the write.
- Keep repository exploration evidence-driven.
- Collect may modify user-provided issue-material roots in v1, but it must not modify the project repository.

## Exit

- If collect is complete and `collect_ready` passes, hand off to `issue-handoff`.
- If evidence is incomplete or ambiguous, keep the case in `collecting` or `blocked`.
