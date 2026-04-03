# Canonical Example Case

This example demonstrates the golden path workflow from collect through handoff to resolve.

## Scenario

User reports: "Users with mixed-case usernames can't log in since the v2.3.0 deployment"

User provides:
- Error log file (`error.log`)
- Screenshot of the login failure (`login-error.png`)
- Short problem statement in text

## Stage 1: Collect

### Input

```bash
# User provides:
/tmp/issue-materials/
├── error.log
├── login-error.png
└── problem-statement.txt
```

**problem-statement.txt**:
```
Several users reported they can't log in after we deployed v2.3.0 yesterday.
All affected users have mixed-case usernames like "JohnDoe" or "SarahSmith".
Users with all-lowercase usernames like "admin" can log in fine.
```

### Collect Actions

1. **Create case**: `login-case-sensitivity-bug`
2. **Register sources**:
   - `error.log` → collected to `curated/logs/error.log`
   - `login-error.png` → collected to `curated/media/login-error.png`
   - `problem-statement.txt` → collected to `curated/notes/problem-statement.txt`
3. **Evidence-driven repo reads**:
   - Search for "validateCredentials" mentioned in error log
   - Find `src/auth/login.ts` with validation logic
   - Register as repository reference

### Result Structure

```text
<project-root>/
├── ISSUE_CONTEXT.md
└── .issue-flow/
    └── cases/
        └── login-case-sensitivity-bug/
            ├── status.yaml           # lifecycle: collected
            ├── activity.md           # Logs: case created, sources registered, collection complete
            ├── sources.yaml          # 3 issue materials + 1 repository ref
            └── curated/
                ├── logs/
                │   └── error.log
                ├── media/
                │   └── login-error.png
                └── notes/
                    └── problem-statement.txt
```

**status.yaml**:
```yaml
case_id: "login-case-sensitivity-bug"
lifecycle: collected
stage: collect
updated_at: "2026-04-02T10:00:00Z"
readiness:
  collect_ready: true
  handoff_ready: false
  resolve_ready: false
  close_ready: false
notes: ""
```

**sources.yaml**:
```yaml
case_id: "login-case-sensitivity-bug"
created_at: "2026-04-02T10:00:00Z"
sources:
  - id: "error-log"
    origin: issue_material
    kind: path
    location: "/tmp/issue-materials/error.log"
    collected: "curated/logs/error.log"
    note: "Contains validateCredentials errors"
    
  - id: "screenshot"
    origin: issue_material
    kind: media
    location: "/tmp/issue-materials/login-error.png"
    collected: "curated/media/login-error.png"
    note: "Shows 'Invalid credentials' error message"
    
  - id: "problem-statement"
    origin: issue_material
    kind: note
    location: "/tmp/issue-materials/problem-statement.txt"
    collected: "curated/notes/problem-statement.txt"
    note: "User description of the issue"
    
  - id: "repo-ref-1"
    origin: repository
    kind: file
    location: "src/auth/login.ts"
    note: "Contains validateCredentials function"

mutations: []
```

## Stage 2: Handoff

### Handoff Actions

1. **Load curated evidence**: Review logs, screenshot, problem statement
2. **Evidence-driven repo analysis**: Read `src/auth/login.ts` based on error log
3. **Create investigation.xml**: Evidence refs, confirmed facts, inferred conclusions
4. **Create handoff.xml**: Concise summary with code context and next_step recommendation

### Result Structure

```text
.issue-flow/cases/login-case-sensitivity-bug/
├── status.yaml           # lifecycle: handoff_ready
├── activity.md           # + handoff started, handoff ready
├── sources.yaml
├── curated/
│   └── [same as before]
 └── analysis/
    ├── investigation.xml
    └── handoff.xml
```

**investigation.xml**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<investigation case-id="login-case-sensitivity-bug" timestamp="2026-04-02T12:00:00Z">
  <evidence_refs>
    <issue_material id="error-log" path="curated/logs/error.log" type="log" />
    <issue_material id="screenshot" path="curated/media/login-error.png" type="image" />
    <issue_material id="problem-statement" path="curated/notes/problem-statement.txt" type="note" />
    
    <repository_ref type="file" path="src/auth/login.ts" />
    <repository_ref type="symbol" path="src/auth/login.ts" symbol="validateCredentials" line="42" />
    <repository_ref type="symbol" path="src/auth/login.ts" symbol="normalizeUsername" line="15" />
  </evidence_refs>

  <evidence_excerpts>
    <!-- REQUIRED: Actual log content proving logs were read -->
    <log_excerpt id="error-log-excerpt-1" source="curated/logs/error.log" lines="147-149" timestamp="2026-04-01T10:23:45Z">
[2026-04-01T10:23:45Z] [ERROR] validateCredentials: Authentication failed
Username provided: JohnDoe
Username stored: johndoe
Comparison result: false (case-sensitive mismatch)
    </log_excerpt>
    
    <log_excerpt id="error-log-excerpt-2" source="curated/logs/error.log" lines="203-204" timestamp="2026-04-01T10:31:12Z">
[2026-04-01T10:31:12Z] [ERROR] validateCredentials: Authentication failed for user: SarahSmith
[2026-04-01T10:31:12Z] [INFO] normalizeUsername function exists at line 15 but is not called in validation path
    </log_excerpt>
  </evidence_excerpts>

  <confirmed>
    <fact ref="error-log" source_excerpt="error-log-excerpt-1">Authentication fails with 401 status for mixed-case usernames</fact>
    <fact ref="screenshot">Error message displays "Invalid credentials"</fact>
    <fact ref="problem-statement">Issue started after v2.3.0 deployment</fact>
    <fact ref="problem-statement">All-lowercase usernames work fine</fact>
    <fact ref="repository_ref">validateCredentials does case-sensitive comparison</fact>
    <fact ref="repository_ref" source_excerpt="error-log-excerpt-2">normalizeUsername helper exists but is not called</fact>
  </confirmed>

  <inferred>
    <inference basis="error-log,repository_ref">Validation logic rejects valid credentials due to missing username normalization</inference>
    <inference basis="repository_ref">The normalizeUsername helper was intended for this purpose but wasn't integrated into validation path</inference>
  </inferred>

  <open_questions>
    <question>Does this affect other authentication methods (OAuth, SAML)?</question>
    <question>Why wasn't this caught during v2.3.0 testing?</question>
  </open_questions>

  <details>
    <section title="Timeline">
      Issue first reported on 2026-04-01, one day after v2.3.0 deployment.
      Affects users since v2.3.0 went live at 2026-03-31T14:00:00Z.
    </section>
    
    <section title="Impact">
      Based on error log analysis, approximately 15% of login attempts fail.
      All failures are for usernames containing uppercase characters.
      Blocks login completely for affected users - no workaround available.
    </section>
    
    <section title="Root Cause">
      The validateCredentials function performs direct string comparison between
      user input and stored credentials. Stored credentials are all lowercase,
      but user input is not normalized before comparison. The normalizeUsername
      helper exists at line 15 but is never called in the validation path.
    </section>
  </details>
</investigation>
```

**handoff.xml**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<handoff case-id="login-case-sensitivity-bug" timestamp="2026-04-02T13:00:00Z">
  <summary>
Users with mixed-case usernames cannot log in since v2.3.0 deployment. The validateCredentials function in src/auth/login.ts performs case-sensitive comparison against stored credentials, but user input is not normalized before validation.

The issue affects approximately 15% of login attempts based on error log analysis. Authentication succeeds for all-lowercase usernames but fails for any username containing uppercase characters.

Root cause is missing username normalization before the credential validation check. The normalizeUsername helper exists at line 15 but is not called in the validation path at line 42.

Fix requires calling normalizeUsername on user input before credential comparison. Should also add test coverage for mixed-case usernames to prevent regression.
  </summary>

  <code_context>
    <affected_files>
      <file path="src/auth/login.ts" reason="Contains validateCredentials with missing normalization" />
      <file path="test/auth/login.test.ts" reason="Needs test coverage for mixed-case usernames" />
    </affected_files>
    
    <key_symbols>
      <symbol path="src/auth/login.ts" name="validateCredentials" line="42" />
      <symbol path="src/auth/login.ts" name="normalizeUsername" line="15" />
    </key_symbols>
    
    <critical_sections>
      <section path="src/auth/login.ts" start="42" end="58" note="Validation logic missing normalization call" />
    </critical_sections>
  </code_context>

  <known>
    <item>Issue started after v2.3.0 deployment on 2026-03-31</item>
    <item>Affects only mixed-case usernames, not all-lowercase</item>
    <item>normalizeUsername helper already exists but is unused</item>
    <item>No test coverage exists for mixed-case username scenarios</item>
    <item>Approximately 15% of login attempts currently failing</item>
  </known>

  <next_step>
    <recommended_action>resolve</recommended_action>
    <confidence>high</confidence>
    <solution_approved>false</solution_approved>
    <reasoning>
      Root cause is clear and fix is straightforward. The normalizeUsername
      helper already exists and just needs to be called before validation.
      High confidence that adding the normalization call will resolve the issue.
    </reasoning>
    <prerequisites>
      <item>Access to test environment for verification</item>
      <item>Ability to verify with affected users before production deploy</item>
    </prerequisites>
    <notes>
      Should also add comprehensive test coverage for username normalization
      scenarios (mixed-case, all-uppercase, all-lowercase, special characters).
      Consider auditing other authentication paths (OAuth, SAML) for similar issues.
    </notes>
  </next_step>

  <investigation_ref>analysis/investigation.xml</investigation_ref>
</handoff>
```

The `next_step` section lives inside `analysis/handoff.xml`; there is no standalone YAML file.

**status.yaml** (updated):
```yaml
case_id: "login-case-sensitivity-bug"
lifecycle: handoff_ready
stage: handoff
updated_at: "2026-04-02T13:30:00Z"
readiness:
  collect_ready: true
  handoff_ready: true
  resolve_ready: true
  close_ready: false
notes: ""
```

## Stage 3: Resolve

### Resolve Actions

1. **Review handoff and project context**: Re-read `analysis/handoff.xml` (especially `next_step`) and `<project-root>/ISSUE_CONTEXT.md`
2. **Present proposal and get approval**: Summarize the fix, affected files, and verification plan; wait for explicit user approval
3. **Record approval**: Update `analysis/handoff.xml` with `<solution_approved>true</solution_approved>`
4. **Implement fix**: Add normalization call in validateCredentials
5. **Add tests**: Create test coverage for mixed-case usernames
6. **Verify fix**: Run automated tests and manual verification
7. **Create resolution.xml**: Document outcome and delivery
8. **Create verification.md**: Detail verification steps and results

### Result Structure

```text
.issue-flow/cases/login-case-sensitivity-bug/
├── status.yaml           # lifecycle: resolved_verified
├── activity.md           # + resolve started, resolved, closed
├── sources.yaml
├── curated/
│   └── [same as before]
├── analysis/
│   └── [same as before]
└── resolve/
    ├── resolution.xml
    └── verification.md
```

**resolution.xml**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<resolution case-id="login-case-sensitivity-bug" timestamp="2026-04-02T16:00:00Z">
  <summary>
Fixed case sensitivity bug in username validation by calling normalizeUsername
before credential comparison. Added comprehensive test coverage for mixed-case,
all-uppercase, and all-lowercase username scenarios.
  </summary>

  <outcome type="code_fix">
Modified validateCredentials function in src/auth/login.ts to normalize username
before validation (line 43). Added three test cases in test/auth/login.test.ts
covering mixed-case, all-uppercase, and all-lowercase username scenarios. All
tests pass. Manual verification with affected users confirms issue is resolved.
  </outcome>

  <delivery>
    <changes>
      <file path="src/auth/login.ts" action="modified" />
      <file path="test/auth/login.test.ts" action="modified" />
    </changes>
    
    <commit sha="a1b2c3d4e5f6" branch="fix/login-case-sensitivity" />
    <pr number="1234" url="https://github.com/example-org/example-repo/pull/1234" />
  </delivery>

  <verification status="verified">
    <summary>
All automated tests pass. Manual verification with 3 affected users confirms
the issue is resolved. No new authentication errors in test environment logs
after 24 hours of monitoring.
    </summary>
    <verification_ref>resolve/verification.md</verification_ref>
  </verification>

  <handoff_ref>analysis/handoff.xml</handoff_ref>
</resolution>
```

**verification.md**:
```markdown
# Verification: login-case-sensitivity-bug

Detailed verification steps and results for the resolution.

---

## Verification Plan

### Test Cases

1. **Mixed-case username login**
   - **Setup**: User account with username stored as "johndoe"
   - **Action**: Login with "JohnDoe" (mixed-case)
   - **Expected**: Authentication succeeds
   - **Status**: ✓ Pass

2. **All-uppercase username login**
   - **Setup**: User account with username stored as "admin"
   - **Action**: Login with "ADMIN" (all-uppercase)
   - **Expected**: Authentication succeeds
   - **Status**: ✓ Pass

3. **All-lowercase username login (regression)**
   - **Setup**: User account with username stored as "testuser"
   - **Action**: Login with "testuser" (all-lowercase)
   - **Expected**: Authentication succeeds
   - **Status**: ✓ Pass

### Manual Verification Steps

1. Deploy to test environment
2. Verify with affected users (JohnDoe, SarahSmith, TestUser123)
3. Monitor authentication logs for 24 hours
4. Check no new authentication errors occur

---

## Verification Results

### Automated Tests

```
✓ test/auth/login.test.ts
  ✓ validates credentials case-insensitively
  ✓ normalizes username before lookup (mixed-case)
  ✓ normalizes username before lookup (all-uppercase)
  ✓ normalizes username before lookup (all-lowercase)
  ✓ handles special characters in usernames
  
All tests passing. Total: 5 tests, 5 passed, 0 failed.
```

### Manual Checks

- [x] Deployed to test environment at 2026-04-02T14:00:00Z
- [x] Verified with 3 affected users - all can now log in successfully
- [x] Monitored logs for 24 hours - no authentication errors for previously affected users
- [x] Checked regression - all-lowercase usernames still work correctly

---

## Evidence

### Before Fix

Authentication failing for user "JohnDoe":

```
[2026-04-01T15:23:45Z] [ERROR] validateCredentials: Authentication failed
Username provided: JohnDoe
Username stored: johndoe
Comparison result: false (case-sensitive mismatch)
```

### After Fix

Authentication succeeding for user "JohnDoe":

```
[2026-04-02T15:30:12Z] [INFO] validateCredentials: Authentication successful
Username provided: JohnDoe
Username normalized: johndoe
Username stored: johndoe
Comparison result: true
```

---

## Verification Status

**Overall Status**: verified  
**Confidence**: high  
**Verified By**: Engineering team + 3 affected users  
**Verified At**: 2026-04-02T16:00:00Z

---

## Notes

Monitoring will continue for 7 days post-production deployment to ensure no
edge cases were missed. So far, all verification points pass with high confidence.
```

**status.yaml** (final):
```yaml
case_id: "login-case-sensitivity-bug"
lifecycle: closed
stage: resolve
updated_at: "2026-04-02T17:00:00Z"
readiness:
  collect_ready: true
  handoff_ready: true
  resolve_ready: true
  close_ready: true
notes: "Deployed to production on 2026-04-03. Monitoring for 7 days."
```

**activity.md** (final excerpt):
```markdown
## 2026-04-02T10:00:00Z

**Event**: Case created
**Lifecycle**: new → collecting
**Trigger**: User provided issue materials
**Details**: User reported login failures for mixed-case usernames after v2.3.0 deployment

---

## 2026-04-02T11:00:00Z

**Event**: Evidence collection complete
**Lifecycle**: collecting → collected
**Trigger**: Curated evidence set is sufficient for downstream work
**Details**: Registered 3 issue materials (log, screenshot, problem statement) and 1 repository reference

---

## 2026-04-02T12:00:00Z

**Event**: Handoff started
**Lifecycle**: collected → handoff_in_progress
**Trigger**: User requested investigation synthesis
**Details**: Beginning evidence analysis and handoff assembly

---

## 2026-04-02T13:30:00Z

**Event**: Handoff ready
**Lifecycle**: handoff_in_progress → handoff_ready
**Trigger**: All handoff artifacts complete and verified
**Details**: Investigation.xml, handoff.xml, and resolve outputs all created with full traceability

---

## 2026-04-02T14:00:00Z

**Event**: Resolution started
**Lifecycle**: handoff_ready → resolve_in_progress
**Trigger**: User requested fix implementation
**Details**: Implementing username normalization fix and adding test coverage

---

## 2026-04-02T16:00:00Z

**Event**: Resolution complete
**Lifecycle**: resolve_in_progress → resolved_verified
**Trigger**: Fix implemented and fully verified
**Details**: Added normalization call, created tests, verified with affected users. All verification passed.

---

## 2026-04-02T17:00:00Z

**Event**: Case closed
**Lifecycle**: resolved_verified → closed
**Trigger**: Resolution verified and complete, no further action needed
**Details**: Fix deployed to production. Monitoring for 7 days. Case complete.
```

## Summary

This canonical example demonstrates:

✓ **Collect**: Raw materials → curated evidence workspace  
✓ **Handoff**: Curated evidence → investigation + handoff artifacts  
✓ **Resolve**: Handoff → implementation + verification + closure  

All artifacts maintain full traceability from raw inputs through to final resolution.
