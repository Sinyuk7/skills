# Resolution: {{case_id}}

## Fix Applied

Added null check in `AuthService.validateToken()`.

**Changed files**:
- `src/auth/AuthService.java`

**Commit**: `abc123def`

## Fix Details

```java
public boolean validateToken(String token) {
    TokenPayload payload = parseToken(token);
    if (payload == null || payload.user_id == null) {
        logger.warn("Invalid token payload");
        return false;
    }
    return userExists(payload.user_id);
}
```

## Verification Context

- Method: `开发自测` / `QA测试`
- Environment: `local` / `staging` / `production`
- Notes: add any extra context that matters for the sync step

## Verification

### Test: Expired token handling
- **Setup**: Create expired token with null user_id
- **Action**: Call `POST /api/login` with expired token
- **Expected**: Returns 401 with "Invalid token" message, no crash
- **Result**: ✓ PASS

### Test: Valid token handling
- **Setup**: Create valid token
- **Action**: Call `POST /api/login` with valid token
- **Expected**: Returns 200, login succeeds
- **Result**: ✓ PASS

### Test: Null token handling
- **Setup**: No token
- **Action**: Call `POST /api/login` without token
- **Expected**: Returns 401
- **Result**: ✓ PASS

## Verification Status

**VERIFIED** — All tests pass. No crash on expired tokens.

**Verified by**: claude-opus
**Verified at**: 2026-04-03T11:45:00Z

## Delivery

- Branch: `fix/auth-null-check`
- PR: #456 (https://github.com/org/repo/pull/456)
- Status: Ready to merge
