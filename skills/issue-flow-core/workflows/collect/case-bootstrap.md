# case-bootstrap

Purpose:

- initialize or resume a case directory
- establish `case-id`
- read `ISSUE_CONTEXT.md` early
- generate the first case-level artifacts

Expected outputs:

- `case.md`
- `status.yaml`
- `project-context.snapshot.md`
- `source-manifest.yaml`

Notes:

- `ISSUE_CONTEXT.md` is open-format input
- `project-context.snapshot.md` should preserve useful project context without
  forcing a fixed schema
