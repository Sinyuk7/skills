---
name: issue-collect
description: Curate user-provided issue materials (logs, screenshots, notes) into `.issue-flow/cases/case-id/evidence/`. Use when starting a fresh issue investigation.
---

# Collect

Copy relevant user-provided materials into a case workspace.

## Input

User provides:
- Logs, screenshots, videos, archives
- Issue descriptions, reproduction steps
- Error messages, stack traces

## Output

1. **evidence/** — Copy relevant files here:
   - `logs/` for log files
   - `media/` for screenshots/videos
   - `notes/` for text descriptions

2. **collect.md** — Document:
   - What was collected (file list)
   - What was skipped (and why)
   - Source locations (where materials came from)

3. **case.yaml** — Create/update:
   ```yaml
   case_id: "issue-123"
   status: collected
   next_step: 
     action: investigate
   evidence:
     - logs/app.log
     - media/screenshot.png
   ```

## Case ID

- Use bug tracker ID if available: `BUG-1234`
- Otherwise: short slug from issue title: `login-crash`
- Add timestamp only if collision: `login-crash-20260403`

## Rules

- Workspace: `<repo>/.issue-flow/cases/<case-id>/`
- Don't analyze evidence yet—just collect
- Don't read repository code yet—just materials
- If unclear which files are relevant, ask user

## Done When

- Relevant materials copied to `evidence/`
- `collect.md` documents what/why
- `case.yaml` has `status: collected`
