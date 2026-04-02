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

Optional plugin-style follow-up skills may also exist outside the core stages.
Example:

- `../issue-overmind-sync` for external Overmind submission after resolve

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

Plugin skills may read the same case workspace, but they should keep their own
traceability in plugin-owned sidecars such as:

```text
.issue-flow/cases/<case-id>/integrations/<plugin-name>/
```

They do not redefine the core lifecycle or become readiness requirements for
the three main stages.
