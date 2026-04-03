# issue-flow-core

Design-time source for the issue-flow skill set.

This directory is not a user-facing skill entrypoint and not the runtime case
workspace. It is the source of truth for:

- workflow docs
- knowledge docs
- artifact templates
- script contracts
- the product requirements doc

At runtime, issue-flow operates inside the current repository, not inside the
installed skills tree:

```text
<project-root>/
├── ISSUE_CONTEXT.md
├── .issue-flow-core/
└── .issue-flow/
    └── cases/
        └── <case-id>/
```

`<project-root>/.issue-flow-core/` is the runtime core directory. Skills should
resolve the current git repository root first, bootstrap `.issue-flow-core/`
when missing, and only proceed once required runtime assets exist.

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

Plugin skills may read the same case workspace, but they should keep their own
traceability in plugin-owned sidecars such as:

```text
.issue-flow/cases/<case-id>/integrations/<plugin-name>/
```

They do not redefine the core lifecycle or become readiness requirements for
the three main stages.
