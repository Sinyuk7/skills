# scripts

Planned script contracts:

- `init-case.sh`
- `build-source-manifest.sh`
- `build-inventory.sh`
- `collect-log-window.sh`
- `collect-media-evidence.sh`
- `build-code-map.sh`
- `package-evidence.sh`

This directory is intentionally skeletal in the first pass. Script behavior will
be added after the workflow and artifact contracts are finalized.

---

## Runtime Usage

Scripts in this directory are design-time utilities referenced directly from
the installed skills tree.

Runtime assumptions:

- Project-level context lives at `<repo-root>/ISSUE_CONTEXT.md`
- Case state lives under `<repo-root>/.issue-flow/cases/<case-id>/`
- Scripts should operate against the repository and case paths directly
- Scripts should not require or bootstrap a repo-local `.issue-flow-core/`
  directory
