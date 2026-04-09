# Investigation: {{case_id}}

## Summary

User reports crash on login. Logs show NullPointerException in `AuthService.validateToken()`.

## Evidence Analysis

### Error Pattern

From `/tmp/auth-bug/app.log` lines 234-236:
```
2026-04-03 10:15:32 ERROR [AuthService] NullPointerException at validateToken:42
2026-04-03 10:15:32 ERROR [AuthService] Token validation failed for user_id=null
2026-04-03 10:15:32 ERROR [Server] Request failed: /api/login
```

### Root Cause

`AuthService.validateToken()` assumes `user_id` is always present in token payload. When token is expired, `user_id` field is null, causing NPE.

**Code location**: `src/auth/AuthService.java:42`

```java
public boolean validateToken(String token) {
    TokenPayload payload = parseToken(token);
    return userExists(payload.user_id);
}
```

### Affected Code

- `src/auth/AuthService.java:42` — Crash site
- `src/auth/TokenParser.java:18` — Returns payload with null fields on expiration
- `src/api/LoginController.java:67` — Calls validateToken without null check

### Proposed Fix

Add null check before accessing `payload.user_id`:

```java
if (payload == null || payload.user_id == null) {
    return false;
}
```

## Next

Root cause identified. Ready for resolution.
