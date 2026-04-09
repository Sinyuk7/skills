---
name: issue-investigate
description: Build a traceable investigation from collected evidence. Use when a case has evidence collected and needs root cause analysis.
---

# Issue Investigate

Analyze collected evidence to find root cause with traceable evidence chains.

## Step 1: Locate Case Workspace

First resolve `PROJECT_ROOT` using the same rules as `/issue-collect`:

- Prefer an explicit repository path from the user
- Otherwise derive the repo root from a user-provided code path or evidence path:
  ```bash
  git -C "<file-directory-or-repo-path>" rev-parse --show-toplevel
  ```
- Use plain `git rev-parse --show-toplevel` only when the current working directory is already known to be the target repository
- If the target repository is ambiguous, stop and ask the user instead of guessing

Never default to the skill repository or any unrelated repo just because the command succeeds there.
Do not inline `git rev-parse --show-toplevel` again in later commands; reuse the already-resolved absolute `PROJECT_ROOT`.

Then find the case:

```
PROJECT_ROOT/.issue-flow/cases/<case-id>/
```

If user doesn't specify case-id, list available cases:

```bash
ls "$PROJECT_ROOT/.issue-flow/cases/"
```

If `"$PROJECT_ROOT/.issue-flow/cases/"` does not exist, report that the target repository has no local issue-flow cases yet. Do not silently switch to a different repository.

## Step 2: Load Case Context

Read these files in order:

1. `case.yaml` — Current state and user context
2. `collect.md` — What evidence was collected
3. `evidence/` — The actual materials

Verify `status: collected` before proceeding.

## Step 3: Analyze Evidence

For each piece of evidence, extract key information:

### Log Analysis Pattern

```markdown
### Evidence: `evidence/logs/filename.log`

**Relevant excerpts:**

Lines 234-236:
```
<exact log content>
```

**Observation:** <what this tells us>
**Timestamp:** <if available>
**Severity:** <error/warning/info>
```

### Media Analysis Pattern

```markdown
### Evidence: `evidence/media/screenshot.png`

**Shows:** <describe what's visible>
**Relevant UI state:** <what state the app is in>
**Anomaly:** <what looks wrong>
```

## Step 4: Read Repository Code

Now you MAY read repository code to correlate with evidence.

For each code reference from `case.yaml`:

1. Read the file
2. Understand the logic flow
3. Correlate with evidence timestamps/states

Document findings:

```markdown
### Code Analysis: `path/to/File.kt`

**Function:** `functionName()` (lines 42-68)
**Purpose:** <what it does>
**Relevant logic:**
```kotlin
// key code snippet
```
**Correlation with evidence:** <how this explains the logs/behavior>
```

## Step 5: Build Root Cause Chain

Connect evidence → code → root cause:

```markdown
## Root Cause Chain

1. **Trigger:** <what initiated the issue>
   - Evidence: `evidence/logs/xxx.log` line 123

2. **Failure point:** <where things went wrong>
   - Code: `path/to/File.kt:45` in `functionName()`
   - Evidence: <log/screenshot showing the failure>

3. **Root cause:** <why it failed>
   - <technical explanation>

4. **Impact:** <what the user experienced>
   - Evidence: <user description or screenshot>
```

## Step 6: Write investigation.md

Create `investigation.md` with this structure:

```markdown
# Investigation: <case-id>

## Summary
<2-3 sentence description of the issue and root cause>

## Evidence Analysis

### Logs
<analysis from Step 3>

### Media
<analysis from Step 3>

## Code Analysis
<analysis from Step 4>

## Root Cause Chain
<chain from Step 5>

## Root Cause Statement

**What:** <one sentence: what is broken>
**Why:** <one sentence: why it's broken>
**Where:** <file:line or component name>

## Proposed Fix

### Option A: <name>
- Change: <what to modify>
- File: `path/to/file.kt`
- Risk: <low/medium/high>
- Effort: <small/medium/large>

### Option B: <name> (if applicable)
- ...

## Recommendation
<which option and why>

## Verification Plan
- [ ] <how to verify the fix works>
- [ ] <edge cases to test>

## Status
Ready for resolution.
```

## Step 7: Update case.yaml

```yaml
status: investigated
updated: "<ISO-8601 timestamp>"
root_cause:
  summary: "<one-line root cause>"
  location: "path/to/file.kt:42"
  evidence_refs:
    - "evidence/logs/app.log:234-236"
next_step:
  action: resolve
  note: "Root cause identified, ready to fix"
```

## Rules

- **MUST** quote evidence with exact source and line numbers
- **MUST** correlate code with evidence—no speculation
- **DO NOT** modify any code during investigation
- If evidence is insufficient, keep status as `collected` but set next_step to blocked:
  ```yaml
  status: collected
  next_step:
    action: blocked
    note: "Need: <specific missing evidence>"
  ```
  When user provides additional evidence, update `next_step.action: investigate` and re-run `/issue-investigate`.

## Done When

- [ ] `investigation.md` created with complete analysis
- [ ] Root cause grounded in evidence (not guessed)
- [ ] Affected code identified with file:line references
- [ ] Proposed fix documented
- [ ] `case.yaml` has `status: investigated`

## Handoff

When complete, tell user:
> Investigation complete for case `<case-id>`. Root cause: <summary>. Run `/issue-resolve` to implement the fix.
