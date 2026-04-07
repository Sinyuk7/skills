---
name: issue-collect
description: Create or update an issue-flow case by curating raw issue materials into `.issue-flow/cases/<case-id>/`. Use when a user provides logs, screenshots, archives, notes, or asks to start investigating a fresh issue.
---

# Issue Collect

Curate user-provided issue materials into a structured case workspace.

## Step 1: Resolve Project Root

Execute this command to get the project root:

```bash
git rev-parse --show-toplevel
```

All paths below are relative to this PROJECT_ROOT.

## Step 2: Determine Case ID

Priority order:
1. Bug tracker ID if provided: `BUG-1234`, `ISSUE-567`
2. Short slug from issue description: `audio-focus-not-restored`
3. Add date suffix only if collision: `audio-focus-not-restored-20260407`

## Step 3: Create or Update Case Workspace

Create this directory structure if it does not already exist. If the case already exists, reuse the current directory and only add any missing subdirectories:

```
PROJECT_ROOT/.issue-flow/cases/<case-id>/
├── case.yaml          # Case state (create now)
├── evidence/          # Raw materials (create now)
│   ├── logs/          # Log files
│   ├── media/         # Screenshots, videos
│   └── notes/         # Text descriptions
└── collect.md         # Collection summary (create after collecting)
```

## Step 4: Initialize or Merge case.yaml

If `case.yaml` does not exist, create it with this structure:

```yaml
case_id: "<case-id>"
created: "<ISO-8601 timestamp>"
updated: "<ISO-8601 timestamp>"
status: collecting
summary: "<one-line issue description>"
user_context: |
  <paste user's original issue description here>
evidence_sources: []
next_step:
  action: collect
  note: "Gathering materials"
```

If `case.yaml` already exists, read it first and update it in place:

- Preserve existing fields such as `created`, `blockers`, `root_cause`, `resolution`, and any unknown keys
- Preserve existing `evidence_sources` entries and append new ones instead of replacing the list
- Keep the original `summary` and `user_context`; put follow-up user notes in `evidence/notes/` unless the user explicitly wants the summary rewritten
- Update `updated` to the current timestamp
- Only fill in missing keys; do **not** recreate the file from scratch

## Step 5: Collect Evidence

For each user-provided material:

| Material Type            | Target Location      | Action                                                                              |
|--------------------------|----------------------|-------------------------------------------------------------------------------------|
| Log files (.log, .txt)   | `evidence/logs/`     | Copy file                                                                           |
| Archives (.rar, .zip)    | `evidence/staging/`  | Copy archive into staging, extract there, sort contents by type, then delete only the copied archive and temporary staging files |
| Screenshots (.png, .jpg) | `evidence/media/`    | Copy file                                                                           |
| Videos (.mp4, .mov)      | `evidence/media/`    | Copy file                                                                           |
| Text descriptions        | `evidence/notes/`    | Save each note with a specific filename such as `user-description.md`, `repro-steps.md`, or `<original-name>.md`; add a suffix on collision |
| Code file references     | DO NOT COPY          | Record path in case.yaml only                                                       |

**Archive handling:** Copy the archive into `evidence/staging/`, extract it there, then move files to appropriate folders based on content type (logs -> `logs/`, images -> `media/`, text -> `notes/`). Delete the copied archive and staging directory after sorting. Never delete or modify the original user-provided archive outside the case workspace.

Update `evidence_sources` in case.yaml as you collect:

```yaml
evidence_sources:
  - type: log_archive
    original: "/path/to/user/provided.rar"
    extracted_to: "evidence/logs/"
  - type: code_reference  
    path: "biz/player/src/.../CarAudioFocusManager.kt"
    note: "User identified as relevant"
```

## Step 6: Write collect.md

Create `collect.md` summarizing what was collected:

```markdown
# Collection Summary

## Issue Context
<user's description in their words>

## Materials Collected

### Logs
- `evidence/logs/xxx.log` — <description>

### Media  
- `evidence/media/screenshot.png` — <description>

### Notes
- `evidence/notes/user-description.md` — Original issue report

## Code References (not collected, just noted)
- `path/to/File.kt` — <why user mentioned it>

## What's Missing
- <anything needed but not provided>

## Collection Status
Ready for investigation.
```

## Step 7: Update case.yaml Status

```yaml
updated: "<ISO-8601 timestamp>"
status: collected
next_step:
  action: investigate
  note: "Evidence ready for analysis"
```

When updating an existing case:

- Keep appended `evidence_sources` entries and any existing investigation or resolution metadata
- Move `status` back to `collected` only when the new evidence means the case should be investigated again
- If the case was already `investigated` or `resolved` and the new material is only supplemental, preserve that status and add a note describing the additional evidence

## Rules

- **DO NOT** read or analyze repository code during collect
- **DO NOT** attempt to diagnose the issue yet
- **DO** ask user if unclear which files are relevant
- **DO** preserve original filenames when possible
- **DO** extract archives to access log contents

## Done When

- [ ] Case directory created at `PROJECT_ROOT/.issue-flow/cases/<case-id>/`
- [ ] All user-provided materials copied to `evidence/`
- [ ] `case.yaml` updated without losing existing state
- [ ] `case.yaml` has the correct post-collection status (`collected` for new/reopened cases, otherwise the preserved existing status)
- [ ] `collect.md` documents what was collected and from where

## Handoff

When complete, tell user:
> Case `<case-id>` updated with collected evidence. If the case needs analysis, run `/issue-investigate` to analyze evidence and find root cause.
