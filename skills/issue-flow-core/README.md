# issue-flow-core

Shared core for the issue-flow skill set.

This directory is not a user-facing skill entrypoint. It is the shared home for:

- workflow docs
- knowledge docs
- artifact templates
- script contracts
- the product requirements doc

The user-facing entry skills are:

- `../issue-collect`
- `../issue-handoff`
- `../issue-resolve`

Design principles:

- The core object is a case workspace, not a one-shot handoff file.
- Artifacts are progressive and resumable.
- Dependencies indicate readiness, not rigid stage gates.
- Markdown, YAML, and XML are preferred over JSON.

All three skills operate on the same workspace in user projects:

```text
<project-root>/
├── ISSUE_CONTEXT.md
└── .issue-flow/
    └── cases/
        └── <case-id>/
```
