# Resolve Workflow

This workflow governs the `issue-resolve` stage.

## Purpose

Optionally continue from handoff into a fix or final disposition, recording implementation, verification, and closure artifacts.

## Inputs

- Case with `handoff_ready` status
- `analysis/handoff.xml` with issue summary and code context
- `analysis/next-step.yaml` with recommended action
- Optional: `<repo-root>/ISSUE_CONTEXT.md` for project context
- Repository with write access (when resolution requires code changes)

## Outputs

- `resolve/resolution.xml` - outcome, delivery metadata, verification summary
- `resolve/verification.md` - detailed verification steps and evidence

## Workflow Steps

### 1. Prerequisites Check

Verify case is ready for resolve:

```bash
python scripts/check_readiness.py <case-path> resolve_ready
```

If `handoff.xml` is missing, STOP and direct user back to `issue-handoff`.

### 2. Handoff Review

Read `analysis/handoff.xml` to understand:
- Issue summary
- Affected code areas
- Key symbols and critical sections
- What is definitively known

Read `analysis/next-step.yaml` for:
- Recommended action
- Confidence level
- Prerequisites
- Whether `solution_approved` is already recorded

Read `<repo-root>/ISSUE_CONTEXT.md` if present to refresh project-level
constraints, conventions, and verification expectations before proposing or
implementing a fix.

### 3. Resolution Path Selection

Before any repository change:

- Summarize the proposed resolution path, affected areas, and verification plan
- Ask the user to explicitly approve the current solution
- Record or update `solution_approved: true|false` in `analysis/next-step.yaml`
  when the workflow is maintaining that field

Without explicit user approval, resolve may analyze, summarize, and refine the
proposal, but it must not modify the project repository.

After approval, choose the resolution path:

**Code Fix**:
- Implement changes to project repository
- Track changed files

**Config Change**:
- Update configuration files
- Document changes

**Non-Code Conclusion**:
- Issue resolved without code changes
- Document why and what conclusion was reached

**External**:
- Resolution requires action outside current scope
- Document handoff target and expectations

### 4. Implementation (if code changes)

**Permission**:
- Resolve MAY modify project repository only after the user approves the current solution
- Collect and handoff are read-only, only resolve can write to repo

**Implementation Rules**:
- Follow existing codebase patterns
- Test changes appropriately
- Track all modified files for delivery metadata

### 5. Verification

Create `resolve/verification.md` with:

**Verification Plan**:
- Test cases with setup, action, expected, status
- Manual verification steps

**Verification Results**:
- Automated test output
- Manual check results

**Evidence**:
- Before/after comparisons
- Relevant snippets or outputs

**Verification Status**:
- Overall status: verified, partial, unavailable
- Confidence level
- Verifier and timestamp

### 6. Resolution Record

Create `resolve/resolution.xml`:

**Summary**:
- Brief description of resolution

**Outcome**:
- Type: code_fix, config_change, non_code_conclusion, external
- Description of what was done

**Delivery** (if code changes):
- Changed files and actions
- Commit SHA and branch
- PR number and URL

**Verification**:
- Status: verified, partial, unavailable
- Summary of verification
- Reference to verification.md

**References**:
- Pointer to handoff.xml

### 7. Lifecycle Update

Update `status.yaml`:

**If verified**:
- `lifecycle: resolve_in_progress` → `resolved_verified`
- `readiness.resolve_ready: true`

**If partial/unavailable verification**:
- `lifecycle: resolve_in_progress` → `resolved_unverified`
- `readiness.resolve_ready: true`
- Document why verification is partial

Log transition in `activity.md`.

Update `analysis/next-step.yaml` in place so closure state is explicit:
- Set `recommended_action: none` when no further action is needed
- Set `recommended_action: external` when follow-up leaves the current scope
- Set `verification_status` to `verified`, `partial`, or `unavailable`

### 8. Closure Decision

**Ready to close** when:
- Resolution is recorded
- Verification state is explicit
- Next action is `none` or `external`

Run closure check:

```bash
python scripts/check_readiness.py <case-path> close_ready
```

If ready and user confirms:
- `lifecycle: resolved_verified` → `closed`
- Log closure in `activity.md`

## Boundaries

### Must Do

- Require existing handoff.xml (stop without it)
- Re-read the project-level `ISSUE_CONTEXT.md` when present
- Present the proposed solution and obtain explicit user approval before
  modifying the repository
- Record implementation and verification
- Support non-code conclusions
- May modify project repository when resolution requires code changes
- Explicitly document verification state (verified/partial/unavailable)

### Must Not Do

- Rewrite prior evidence artifacts from collect/handoff
- Rewrite prior issue-material roots as substitute for case artifacts
- Force every case through resolution (optional stage)
- Treat closure confirmation as a substitute for implementation approval
- Silently skip verification without documenting why

## Non-Code Resolutions

Valid non-code resolutions:

- **Already Fixed**: Issue no longer reproduces, fixed elsewhere
- **Won't Fix**: Issue is intended behavior or out of scope
- **External**: Resolution requires action outside current scope
- **Duplicate**: Issue is duplicate of another case
- **Cannot Reproduce**: Insufficient information to reproduce

For non-code conclusions:
- Still create resolution.xml with outcome type `non_code_conclusion`
- Document reasoning in summary
- Verification may be `unavailable` - document why

## Verification Levels

**Verified**:
- Automated tests pass
- Manual checks confirm fix
- Before/after evidence shows resolution

**Partial**:
- Some verification possible but not complete
- Document what was verified and what wasn't
- May be blocked by environment or access

**Unavailable**:
- Verification impossible in current context
- Common for non-code conclusions
- Document why verification unavailable

## Reopening

Closed cases may be reopened when user explicitly targets that case:
- Move lifecycle back to appropriate working state
- Log reopen reason in `activity.md`
- Do NOT force brand-new case

## Exit Conditions

- **Resolved & Verified**: `lifecycle: resolved_verified`, ready to close
- **Resolved & Unverified**: `lifecycle: resolved_unverified`, ready to close with caveats
- **Closed**: `lifecycle: closed`, case complete
- **Blocked**: `lifecycle: blocked` with reason documented

## Completion

A resolved case is complete when:
- `resolution.xml` exists with explicit outcome
- `verification.md` documents verification attempts
- Delivery metadata recorded (if code changes)
- User confirms closure or next action is clear
