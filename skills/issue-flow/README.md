# issue-flow

Shared workflow namespace for issue investigation.

This directory is not a skill entrypoint. It is the shared home for:

- workflow docs
- knowledge docs
- artifact templates
- script contracts
- the product requirements doc

The entry skills are:

- `../issue-collect`
- `../issue-handoff`
- `../issue-resolve`

Design principles:

- The core object is a case workspace, not a one-shot handoff file.
- Artifacts are progressive and resumable.
- Dependencies indicate readiness, not rigid stage gates.
- Markdown, YAML, and XML are preferred over JSON.

Workspace target in user projects:

```text
<project-root>/
├── ISSUE_CONTEXT.md
└── .issue-flow/
    ├── case-index.yaml
    ├── active-case.yaml
    ├── exports/
    └── cases/
        └── <case-id>/
```
