# case-bootstrap

Purpose:

- initialize or resume a case directory
- establish `case-id`
- read `ISSUE_CONTEXT.md` early
- generate the first canonical case artifacts

Expected outputs:

- `status.yaml`
- `activity.md`
- `sources.yaml`

Notes:

- `ISSUE_CONTEXT.md` is a project-level input at `<repo-root>/ISSUE_CONTEXT.md`
- do not copy `ISSUE_CONTEXT.md` into the case directory
- do not create `case.md` or `project-context.snapshot.md`
