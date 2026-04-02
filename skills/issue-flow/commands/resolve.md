# Resolve Command

Optionally continue from handoff into fix or final disposition.

## Purpose

Record implementation, verification, and closure artifacts for a case with an existing handoff.

## When to Use

- Case is `handoff_ready`
- User asks to fix the issue
- User asks to resolve the case
- User wants to verify a resolution
- User wants to close a case with non-code conclusion

## Prerequisites

Case must be `resolve_ready`. Verify with:

```bash
python scripts/check_readiness.py <case-path> resolve_ready
```

If `handoff.xml` is missing, STOP and direct user back to `commands/handoff.md`.

## Step 1: Handoff Review

Read `analysis/handoff.xml` to understand:
- Issue summary
- Affected code areas
- Key symbols and critical sections
- What is definitively known

Read `analysis/next-step.yaml` for:
- Recommended action
- Confidence level
- Prerequisites

## Step 2: Resolution Path Selection

Based on next-step recommendation and user intent:

### Code Fix

Implement changes to project repository:
- **Resolve MAY modify project repository** (only resolve has write permission)
- Follow existing codebase patterns
- Test changes appropriately
- Track all modified files for delivery metadata

### Config Change

Update configuration files:
- Document changes
- Track modified files

### Non-Code Conclusion

Issue resolved without code changes:

Valid non-code resolutions:
- **Already Fixed**: No longer reproduces, fixed elsewhere
- **Won't Fix**: Intended behavior or out of scope
- **External**: Requires action outside current scope
- **Duplicate**: Duplicate of another case
- **Cannot Reproduce**: Insufficient information

### External

Resolution requires action outside current scope:
- Document handoff target
- Document expectations

## Step 3: Implementation (if code changes)

**Permission**:
- Resolve MAY modify project repository when needed
- Collect and handoff are read-only
- Only resolve can write to repository

**Implementation Rules**:
- Follow existing codebase patterns
- Test changes appropriately
- Track all modified files
- Make atomic, focused changes

**Example for case sensitivity bug**:

```typescript
// src/auth/login.ts
export async function validateCredentials(username: string, password: string) {
  const normalizedUsername = normalizeUsername(username);  // Add this line
  const user = await findUser(normalizedUsername);
  // ... rest of validation
}
```

## Step 4: Verification

Create `resolve/verification.md` using template from `templates/resolve/verification.md`.

### Verification Plan

```markdown
## Verification Plan

### Test Cases

1. **Mixed-case username login**
   - **Setup**: User account with username "JohnDoe"
   - **Action**: Login with "johndoe" (lowercase)
   - **Expected**: Authentication succeeds
   - **Status**: ✓ Pass

2. **All-uppercase username login**
   - **Setup**: User account with username "ADMIN"
   - **Action**: Login with "admin" (lowercase)
   - **Expected**: Authentication succeeds
   - **Status**: ✓ Pass

### Manual Verification Steps

1. Deploy to test environment
2. Verify with affected users
3. Check logs for authentication errors
```

### Verification Results

```markdown
## Verification Results

### Automated Tests

```
✓ test/auth/login.test.ts
  ✓ validates credentials case-insensitively
  ✓ normalizes username before lookup
  ✓ handles mixed-case usernames
  
All tests passing.
```

### Manual Checks

- [x] Deployed to test environment
- [x] Verified with 3 affected users - all can now log in
- [x] No new authentication errors in logs
```

### Evidence

```markdown
## Evidence

### Before

Authentication failing for user "JohnDoe":

```
[ERROR] validateCredentials: User not found
Username: JohnDoe
Stored: johndoe
```

### After

Authentication succeeding:

```
[INFO] validateCredentials: User authenticated
Username: JohnDoe (normalized to johndoe)
```
```

### Verification Status

```markdown
## Verification Status

**Overall Status**: verified
**Confidence**: high
**Verified By**: Engineering team
**Verified At**: 2026-04-02T16:00:00Z
```

## Step 5: Resolution Record

Create `resolve/resolution.xml` using template from `templates/resolve/resolution.xml`.

### Summary

```xml
<summary>
Fixed case sensitivity bug in username validation by calling normalizeUsername
before credential comparison. Added test coverage for mixed-case usernames.
</summary>
```

### Outcome

```xml
<outcome type="code_fix">
Modified validateCredentials function to normalize username before validation.
Added three test cases covering mixed-case, all-uppercase, and all-lowercase
username scenarios.
</outcome>
```

**Outcome types**:
- `code_fix` - Code changes implemented
- `config_change` - Configuration updated
- `non_code_conclusion` - No code changes needed
- `external` - Handed off externally

### Delivery (if code changes)

```xml
<delivery>
  <changes>
    <file path="src/auth/login.ts" action="modified" />
    <file path="test/auth/login.test.ts" action="modified" />
  </changes>
  
  <commit sha="a1b2c3d4" branch="fix/login-case-sensitivity" />
  <pr number="1234" url="https://github.com/org/repo/pull/1234" />
</delivery>
```

### Verification

```xml
<verification status="verified">
  <summary>
All automated tests pass. Manual verification with affected users confirms
the issue is resolved. No new authentication errors in test environment logs.
  </summary>
  <verification_ref>resolve/verification.md</verification_ref>
</verification>
```

**Verification status**:
- `verified` - Full verification complete
- `partial` - Some verification done, some blocked
- `unavailable` - Verification impossible in current context

### References

```xml
<handoff_ref>analysis/handoff.xml</handoff_ref>
```

## Step 6: Lifecycle Update

Update `status.yaml`:

**If verified**:
```yaml
lifecycle: resolve_in_progress → resolved_verified
readiness:
  collect_ready: true
  handoff_ready: true
  resolve_ready: true
```

**If partial/unavailable verification**:
```yaml
lifecycle: resolve_in_progress → resolved_unverified
```

Document why verification is partial in `verification.md`.

Log transition in `activity.md`.

## Step 7: Closure Decision

**Ready to close** when:
- Resolution is recorded
- Verification state is explicit
- Next action is `none` or `external`

Run closure check:

```bash
python scripts/check_readiness.py <case-path> close_ready
```

If ready and user confirms:

```yaml
lifecycle: resolved_verified → closed
```

Log closure in `activity.md`:

```markdown
## 2026-04-02T17:00:00Z

**Event**: Case closed
**Lifecycle**: resolved_verified → closed
**Trigger**: Resolution verified and complete
**Details**: Fix deployed to production. No further action needed.
```

## Verification Levels

### Verified

- Automated tests pass
- Manual checks confirm fix
- Before/after evidence shows resolution
- High confidence

### Partial

- Some verification possible but not complete
- Document what was verified and what wasn't
- May be blocked by environment or access
- Medium confidence

### Unavailable

- Verification impossible in current context
- Common for non-code conclusions
- Document why verification unavailable
- Low to medium confidence

## Non-Code Resolutions

For non-code conclusions:

- Create `resolution.xml` with outcome type `non_code_conclusion`
- Document reasoning in summary
- Verification may be `unavailable` - document why
- Still record in `verification.md` what was checked

Example for "Already Fixed":

```xml
<resolution case-id="example-case">
  <summary>
  Issue no longer reproduces in latest version. Appears to have been fixed
  by commit a9f8e7d in unrelated refactoring.
  </summary>
  
  <outcome type="non_code_conclusion">
  Tested with original reproduction steps. Issue does not occur. Reviewing
  commit history shows validation logic was refactored in v2.4.0 and
  normalization was added as part of that work.
  </outcome>
  
  <verification status="verified">
    <summary>Confirmed issue does not reproduce with original steps</summary>
    <verification_ref>resolve/verification.md</verification_ref>
  </verification>
</resolution>
```

## Reopening

Closed cases may be reopened when user explicitly targets that case:

- Move lifecycle back to appropriate working state
- Log reopen reason in `activity.md`
- Do NOT force brand-new case

Example reopen:

```markdown
## 2026-04-10T10:00:00Z

**Event**: Case reopened
**Lifecycle**: closed → resolve_in_progress
**Trigger**: User reported issue still occurs in edge case
**Reason**: Original fix didn't handle email-based usernames
**Details**: Reopening to address email login path
```

## Boundaries

### Must Do

- Require existing `handoff.xml` (stop without it)
- Record implementation and verification
- Support non-code conclusions
- May modify project repository when resolution requires code changes
- Explicitly document verification state

### Must Not Do

- Rewrite prior evidence artifacts from collect/handoff
- Rewrite prior issue-material roots as substitute for case artifacts
- Force every case through resolution (optional stage)
- Silently skip verification without documenting why

## Exit Conditions

- **Resolved & Verified**: `lifecycle: resolved_verified`, ready to close
- **Resolved & Unverified**: `lifecycle: resolved_unverified`, ready to close with caveats
- **Closed**: `lifecycle: closed`, case complete
- **Blocked**: `lifecycle: blocked` with reason documented

## Completion

A resolved case is complete when:

✓ `resolution.xml` exists with explicit outcome  
✓ `verification.md` documents verification attempts  
✓ Delivery metadata recorded (if code changes)  
✓ User confirms closure or next action is clear  

## Workflow Reference

For detailed resolve workflow, see `workflows/resolve/resolve-workflow.md`.
