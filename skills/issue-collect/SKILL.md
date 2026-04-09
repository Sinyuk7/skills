---
name: issue-collect
description: Create or update an issue-flow case by registering user-provided issue materials as references in `.issue-flow/cases/<case-id>/`. Use when a user provides logs, screenshots, archives, notes, or asks to start investigating a fresh issue.
---

# Issue Collect

Register user-provided issue materials into a lightweight case workspace.

## Capability Contract

```yaml
type: routable_skill
owns: Register user-provided issue materials (logs, screenshots, archives, notes, code references) into a case workspace; create and update case.yaml and collect.md
does_not_own: Evidence analysis, root cause investigation, code reading, code modification, bug tracker sync
delegate_to: /issue-investigate (after collection complete)
refuses_when: User asks to diagnose or fix the issue during collection
requires_evidence: User-provided materials or references to register
primary_outputs:
  - case.yaml (case state with evidence_sources)
  - collect.md (collection summary)
allowed_tools: [bash (git rev-parse only), read, write, glob]
forbidden_tools: [edit (no code modification), lsp_* (no code analysis)]
eval_set: evals/evals.json
```

## Step 1: Resolve Target Project Root
<!-- validation_step -->

Resolve the repository that owns this issue before doing anything else.

Set `PROJECT_ROOT` using this priority order:

1. If the user explicitly gives a repository path, use that path.
2. If the user gives a code path, log path, screenshot path, or archive path that lives inside a repository, derive the repo root from that path:
   ```bash
   git -C "<file-directory-or-repo-path>" rev-parse --show-toplevel
   ```
3. Only if the conversation is already clearly operating inside the target repository may you use:
   ```bash
   git rev-parse --show-toplevel
   ```
4. If multiple repositories are plausible or the target repo is still unclear, stop and ask the user which repository should own the case.

Rules:

- Never assume the current working directory is the correct project.
- Never default to the skill repository or some unrelated parent repository just because `git rev-parse --show-toplevel` succeeds there.
- After resolving `PROJECT_ROOT`, use absolute paths rooted at `PROJECT_ROOT` for the rest of this skill, or run later shell commands from `PROJECT_ROOT` explicitly.
- Do not inline `git rev-parse --show-toplevel` again in later commands; reuse the already-resolved absolute `PROJECT_ROOT`.

## Step 2: Derive Case ID
<!-- transform_step -->

Priority order:
1. Bug tracker ID if provided: `BUG-1234`, `ISSUE-567`
2. Short slug from issue description: `audio-focus-not-restored`
3. Add date suffix only if collision: `audio-focus-not-restored-20260407`

## Step 3: Create or Update Case Workspace
<!-- mutation_step -->

Create this directory structure if it does not already exist:

```
PROJECT_ROOT/.issue-flow/cases/<case-id>/
├── case.yaml          # Case state (create now)
└── collect.md         # Collection summary (create after registering sources)
```

Later stages add:

- `investigation.md`
- `resolution.md`

## Step 4: Initialize or Merge case.yaml
<!-- mutation_step -->

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
  note: "Gathering evidence references"
```

If `case.yaml` already exists, read it first and update it in place:

- Preserve existing fields such as `created`, `blockers`, `root_cause`, `resolution`, and any unknown keys
- Preserve existing `evidence_sources` entries and append new ones instead of replacing the list
- Keep the original `summary` and `user_context`; put follow-up user notes in `collect.md` unless the user explicitly wants the summary rewritten
- Update `updated` to the current timestamp
- Only fill in missing keys; do not recreate the file from scratch

## Step 5: Register Evidence References
<!-- transform_step + mutation_step -->

For each user-provided material, record it in `evidence_sources` instead of copying it into the case workspace:

| Material Type | Record As | Action |
|---------------|-----------|--------|
| Log files (`.log`, `.txt`) | `kind: log` | Record the original file path only |
| Archives (`.rar`, `.zip`) | `kind: archive` | Record the original archive path only |
| Screenshots (`.png`, `.jpg`) | `kind: screenshot` | Record the original file path only |
| Videos (`.mp4`, `.mov`) | `kind: video` | Record the original file path only |
| Text files | `kind: note` | Record the original file path only |
| Text descriptions in the conversation | `user_context` / `collect.md` | Preserve the text directly in case documentation |
| Code file references | `kind: code_reference` | Record the path only |

Use these path rules:

- External files should use absolute paths.
- Repository code references should use repository-relative paths when possible.
- Preserve the original filename and location exactly as provided when possible.

Archive handling:

- Do not copy archives into the case workspace.
- Do not extract archives during `/issue-collect`.
- If a later stage needs archive contents, inspect or extract them in the archive's original directory, never in `.issue-flow/cases/<case-id>/`.

Update `evidence_sources` in `case.yaml` as you register materials:

```yaml
evidence_sources:
  - kind: log
    path: "/tmp/audio-focus-bug/player.log"
    note: "Playback failure log from the repro run"
  - kind: screenshot
    path: "/tmp/audio-focus-bug/screenshot.png"
    note: "UI state when playback did not recover"
  - kind: archive
    path: "/Users/shenyeke01/Downloads/bug-report.zip"
    note: "Original archive provided by the user"
  - kind: code_reference
    path: "biz/player/src/.../CarAudioFocusManager.kt"
    note: "User identified as relevant"
```

## Step 6: Write collect.md
<!-- mutation_step -->

Create `collect.md` summarizing what was registered:

```markdown
# Collection Summary

## Issue Context
<user's description in their words>

## Evidence References

- `/tmp/audio-focus-bug/player.log` — Playback failure log
- `/tmp/audio-focus-bug/screenshot.png` — UI screenshot during the failure
- `/Users/shenyeke01/Downloads/bug-report.zip` — Original archive; inspect or extract in place if needed

## Code References
- `biz/player/src/.../CarAudioFocusManager.kt` — User suspects this area

## What's Missing
- <anything needed but not provided>

## Collection Status
Evidence references registered. Ready for investigation.
```

## Step 7: Update case.yaml Status
<!-- mutation_step -->

```yaml
updated: "<ISO-8601 timestamp>"
status: collected
next_step:
  action: investigate
  note: "Evidence references ready for analysis"
```

When updating an existing case:

- Keep appended `evidence_sources` entries and any existing investigation or resolution metadata
- Move `status` back to `collected` only when the new evidence means the case should be investigated again
- If the case was already `investigated` or `resolved` and the new material is only supplemental, preserve that status and add a note describing the additional evidence

## Rules

- **DO NOT** read or analyze repository code during collect
- **DO NOT** attempt to diagnose the issue yet
- **DO NOT** copy logs, screenshots, videos, or archives into the case workspace
- **DO NOT** extract archives during collect
- **DO** ask the user if it is unclear which files are relevant or which repository owns the case
- **DO** preserve original file paths in the recorded references
- **DO** keep the case workspace lightweight and traceable

## Done When

- [ ] Case directory created at `PROJECT_ROOT/.issue-flow/cases/<case-id>/`
- [ ] All user-provided materials recorded in `case.yaml.evidence_sources`
- [ ] No raw evidence copied into the case workspace
- [ ] `case.yaml` updated without losing existing state
- [ ] `case.yaml` has the correct post-collection status (`collected` for new/reopened cases, otherwise the preserved existing status)
- [ ] `collect.md` documents the evidence references and missing pieces

## Handoff

When complete, tell user:
> Case `<case-id>` updated with evidence references. If the case needs analysis, run `/issue-investigate` to analyze evidence and find root cause.
