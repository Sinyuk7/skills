---
name: issue-collect
description: Create or update an issue-flow case by curating raw issue materials into `.issue-flow/cases/<case-id>/`. Use when a user provides logs, screenshots, archives, notes, or asks to start investigating a fresh issue.
---

# Issue Collect

Thin entry skill for Stage 1 of the issue-flow system.

The design-time source for the shared workflow lives in this skills repo, but
the runtime workflow lives inside the current project. Resolve the current git
repository root first, then use or bootstrap `<repo-root>/.issue-flow-core/`
before proceeding.

## Load These Core Files First

- `../issue-flow-core/workflows/collect/collect-workflow.md`
- `../issue-flow-core/workflows/actions/lifecycle-management.md`
- `../issue-flow-core/knowledge/issue-flow-principles.md`
- `../issue-flow-core/knowledge/case-id-policy.md`

Load templates and scripts only when needed:

- `../issue-flow-core/templates/case/`
- `../issue-flow-core/templates/ISSUE_CONTEXT.md` as the project-level file template only
- `../issue-flow-core/scripts/check_readiness.py`

## Mission

Curate raw user-provided issue materials into a stable case workspace under:

```text
<project-root>/.issue-flow/cases/<case-id>/
```

## Non-Negotiables

- Require at least one non-repository issue input before creating a case.
- Use the shared `.issue-flow/cases/<case-id>/` workspace. Do not invent stage-specific workspaces.
- Runtime assets live in `<repo-root>/.issue-flow-core/`, not in the installed skills directory.
- If `.issue-flow-core/` is missing, bootstrap it before workflow execution.
- `ISSUE_CONTEXT.md` is a repo-level file and must not be copied into the case.
- If the write target is ambiguous, stop and ask the user which case should own the write.
- Keep repository exploration evidence-driven.
- Collect may modify user-provided issue-material roots in v1, but it must not modify the project repository.

## Exit

- If collect is complete and `collect_ready` passes, hand off to `issue-handoff`.
- If evidence is incomplete or ambiguous, keep the case in `collecting` or `blocked`.
