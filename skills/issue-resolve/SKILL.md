---
name: issue-resolve
description: Continue an issue-flow case from /issue-investigate into implementation, verification, or a final non-code disposition. Use when a case has `status: investigated` and the user wants to fix, verify, or close it.
---

# Issue Resolve

Implement the fix, verify it works, and document the resolution.

## Capability Contract

```yaml
type: routable_skill
owns: Implement investigated fix, verify the fix, document resolution in resolution.md, update case.yaml to resolved; handle non-code dispositions (already_fixed, wont_fix, cannot_reproduce, duplicate)
does_not_own: Intake, evidence registration, root cause investigation, bug tracker sync
delegate_to: /issue-overmind-sync (optional, after resolution complete)
refuses_when: Case has no investigation (status != investigated); no user confirmation for code changes
requires_evidence: case.yaml with status investigated from /issue-investigate; investigation.md with root cause and proposed fix
primary_outputs:
  - resolution.md (fix details, verification results, delivery info)
  - case.yaml updated with resolution and status resolved
allowed_tools: [bash, read, write, edit, grep, glob, lsp_*]
forbidden_tools: []
eval_set: evals/evals.json
```

## Step 1: Locate Case Workspace
<!-- validation_step -->

Resolve `PROJECT_ROOT` before doing anything else.

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

## Step 2: Load Investigation Context
<!-- retrieval_step -->

Read these files:

1. `case.yaml` — Verify `status: investigated`
2. `investigation.md` — Get root cause and proposed fix

If the case is still `investigating` or `blocked`, stop and send the user back to `/issue-investigate`.

Extract from investigation.md:
- Root cause location (file:line)
- Recommended fix option
- Verification plan checklist

## Step 3: Confirm Fix Approach with User
<!-- validation_step -->

Before modifying code, present the fix plan:

```
📋 **Fix Plan for case `<case-id>`**

**Root Cause:** <summary from investigation>
**Location:** `path/to/file.kt:42`

**Proposed Change:**
<description of what will be modified>

**Files to modify:**
- `path/to/file.kt` — <change description>

Proceed with this fix? (yes/no/modify)
```

**WAIT FOR USER CONFIRMATION** before proceeding.

## Step 4: Implement Fix
<!-- mutation_step -->

After user confirms:

1. Apply the verified patch to the target file(s)
2. Restrict changes to the root cause location only
3. Follow project coding conventions

Document each change:

```markdown
### Change 1: `path/to/file.kt`

**Lines modified:** 42-48

**Before:**
```kotlin
// old code
```

**After:**
```kotlin
// new code
```

**Rationale:** <why this fixes the root cause>
```

## Step 5: Verify Fix
<!-- validation_step -->

Follow the verification plan from investigation.md:

### Verification Methods

| Method      | When to Use        | How                              |
|-------------|--------------------|----------------------------------|
| Unit test   | Logic change       | Run existing tests or write new one |
| Build       | Any code change    | `./gradlew build` or equivalent  |
| Manual test | UI/behavior change | Steps to reproduce and verify    |
| Code review | Complex change     | Walk through logic               |

Document results:

```markdown
## Verification Results

### Test 1: <test name>
- **Method:** <unit test / build / manual>
- **Command:** `<command run>`
- **Result:** ✅ PASS / ❌ FAIL
- **Evidence:** <output or screenshot>

### Test 2: ...
```

## Step 6: Write resolution.md
<!-- mutation_step -->

Create `resolution.md`:

```markdown
# Resolution: <case-id>

## Summary
<one paragraph: what was fixed and how>

## Fix Applied

### Change 1: `path/to/file.kt`
<from Step 4>

## Verification

### Environment
- Branch: `<branch-name>`
- Build: `<build command>`
- Device/Emulator: `<if applicable>`

### Results
<from Step 5>

## Verification Status

**Status:** VERIFIED | PARTIAL | UNVERIFIED

<if PARTIAL or UNVERIFIED, explain why>

## Delivery

- [ ] Commit: `<SHA>` — `<commit message>`
- [ ] Branch: `<branch-name>`
- [ ] PR: `<PR link if created>`

## Remaining Items
- <any follow-up tasks>
- <any related issues discovered>

## Lessons Learned
- <what could prevent similar issues>
```

## Step 7: Update case.yaml
<!-- mutation_step -->

```yaml
status: resolved
updated: "<ISO-8601 timestamp>"
resolution:
  type: code_fix  # or: already_fixed, wont_fix, cannot_reproduce, duplicate
  summary: "<one-line resolution summary>"
  commit: "<SHA if applicable>"
  verification: VERIFIED  # or: PARTIAL, UNVERIFIED
next_step:
  action: complete
  note: "Resolution complete, PR ready"
closed: "<ISO-8601 timestamp>"
```

## Non-Code Resolutions

If investigation reveals no code change is needed:

### Already Fixed
```yaml
resolution:
  type: already_fixed
  summary: "Fixed in commit <SHA> / PR #123"
  reference: "<link or commit>"
```

### Won't Fix
```yaml
resolution:
  type: wont_fix
  summary: "Working as intended because <reason>"
  rationale: "<detailed explanation>"
```

### Cannot Reproduce
```yaml
resolution:
  type: cannot_reproduce
  summary: "Unable to reproduce with provided evidence"
  attempts: "<what was tried>"
```

### Duplicate
```yaml
resolution:
  type: duplicate
  summary: "Duplicate of case <other-case-id>"
  duplicate_of: "<case-id>"
```

Still create `resolution.md` documenting the disposition.

## Rules

- **MUST** get user confirmation before modifying code
- **MUST** follow the fix recommended in investigation.md (or discuss deviation)
- **MUST** attempt verification before marking resolved
- If fix doesn't work, update `investigation.md` with new findings and re-investigate
- Keep fixes minimal—don't refactor unrelated code

## Done When

- [ ] User confirmed fix approach
- [ ] Code changes applied (if needed)
- [ ] Verification attempted and documented
- [ ] `resolution.md` created
- [ ] `case.yaml` has `status: resolved`

## Handoff

When complete, tell user:
> Case `<case-id>` resolved. <summary of fix>. Verification: <status>. 
> Commit ready on branch `<branch>`. Create PR when ready.
> 
> Optional: Run `/issue-overmind-sync` to sync resolution to Overmind bug tracker.
