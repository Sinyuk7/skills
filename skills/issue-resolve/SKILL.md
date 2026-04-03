---
name: issue-resolve
description: Implement fix, verify, and document resolution. Use when investigation complete.
---

# Resolve

Fix the issue and verify the fix works.

## Input

- `investigation.md` — Root cause and proposed fix
- `case.yaml` — Current status
- Repository code (read-write)

## Output

**resolution.md** containing:

1. **Fix Applied** — What changed
2. **Fix Details** — Code diff or description
3. **Verification Context** — Method, environment, and any useful tester notes
4. **Verification** — Test cases with results
5. **Verification Status** — VERIFIED | PARTIAL | UNVERIFIED
6. **Delivery** — Commit SHA, branch, PR

## Rules

- ASK USER BEFORE MODIFYING CODE
- Follow investigation's proposed fix
- Test before marking verified
- Capture verification method and environment in `resolution.md` when they are known
- If fix doesn't work, update `investigation.md` with new findings
- Update `case.yaml` when done:
  ```yaml
  status: resolved
  next_step:
    action: close
  ```

## Verification Levels

- **VERIFIED**: Tests pass, issue fixed
- **PARTIAL**: Some verification, not complete
- **UNVERIFIED**: Fix applied but not tested (document why)

## Non-Code Resolutions

If no code change needed:
- **Already Fixed**: Issue fixed elsewhere
- **Won't Fix**: Working as intended
- **Cannot Reproduce**: Insufficient info
- **Duplicate**: Same as another case

Still create `resolution.md` documenting why.

## Done When

- Fix applied (if needed)
- Verification attempted
- `resolution.md` complete
- `case.yaml` has `status: resolved`
