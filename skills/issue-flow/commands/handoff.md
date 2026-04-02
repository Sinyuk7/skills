# Handoff Command

Synthesize curated evidence into investigation record and traceable handoff.

## Purpose

Transform curated evidence into:
1. Pure investigation record with evidence refs and expanded details
2. Concise downstream handoff with summary and code context
3. Recommended next action

## When to Use

- Evidence has been curated and case is in `collected` state
- User asks to build a handoff or analyze the evidence
- User wants investigation summary or case handoff
- Ready to synthesize findings into structured artifacts

## Prerequisites

Case must be `collect_ready`. Verify with:

```bash
python scripts/check_readiness.py <case-path> collect_ready
```

If not ready, direct user back to `commands/collect.md`.

## Step 1: Context Loading

Load case context:
- Read `status.yaml` for current lifecycle state
- Read `sources.yaml` for evidence inventory
- Review curated materials in `curated/`
- Check for `ISSUE_CONTEXT.md` in project root

If `ISSUE_CONTEXT.md` exists, incorporate:
- Common issue patterns
- Critical areas
- Architecture notes
- Investigation priorities

## Step 2: Investigation Synthesis

Create `analysis/investigation.xml` using template from `templates/analysis/investigation.xml`.

### Evidence Refs

Point to curated materials and repository evidence:

```xml
<evidence_refs>
  <!-- User-provided issue materials -->
  <issue_material id="log-1" path="curated/logs/error.log" type="log" />
  <issue_material id="screenshot-1" path="curated/media/screenshot.png" type="image" />
  
  <!-- Repository evidence as direct references -->
  <repository_ref type="file" path="src/auth/login.ts" />
  <repository_ref type="symbol" path="src/auth/login.ts" symbol="validateCredentials" line="42" />
  <repository_ref type="line_range" path="src/api/handler.ts" start="120" end="135" />
</evidence_refs>
```

**All refs must resolve to actual artifacts.**

### Confirmed Facts

Facts verified from evidence:

```xml
<confirmed>
  <fact ref="log-1">Authentication fails with 401 status</fact>
  <fact ref="screenshot-1">Error message displays "Invalid credentials"</fact>
  <fact ref="repository_ref">validateCredentials throws exception on line 47</fact>
</confirmed>
```

### Inferred Conclusions

Conclusions drawn from evidence:

```xml
<inferred>
  <inference basis="log-1,repository_ref">Validation logic rejects valid credentials due to case sensitivity bug</inference>
</inferred>
```

### Open Questions

Unresolved questions:

```xml
<open_questions>
  <question>Does this affect all authentication methods or only username/password?</question>
  <question>How long has this issue existed?</question>
</open_questions>
```

### Details

Expanded analysis organized into sections:

```xml
<details>
  <section title="Timeline">
    Issue first reported on 2026-04-01. Affects users since v2.3.0 deployment.
  </section>
  
  <section title="Impact">
    Blocks login for approximately 15% of users with mixed-case usernames.
  </section>
</details>
```

## Step 3: Repository Code Context

**Evidence-Driven Repository Reads**:

Reads must be driven by case evidence:
- Paths mentioned in logs/errors
- Symbols from stack traces
- Module clues from issue materials

Record as **direct repository references** (file paths, symbols, line numbers).

**DO NOT**:
- Copy code excerpts into case workspace (v1 uses direct refs)
- Do unrestricted whole-repo exploration
- Browse unrelated modules

### Code Context Structure

```xml
<code_context>
  <affected_files>
    <file path="src/auth/login.ts" reason="Contains validateCredentials with case sensitivity bug" />
    <file path="src/api/handler.ts" reason="Calls login validation" />
  </affected_files>
  
  <key_symbols>
    <symbol path="src/auth/login.ts" name="validateCredentials" line="42" />
    <symbol path="src/auth/login.ts" name="normalizeUsername" line="15" />
  </key_symbols>
  
  <critical_sections>
    <section path="src/auth/login.ts" start="42" end="58" note="Validation logic with case sensitivity issue" />
  </critical_sections>
</code_context>
```

## Step 4: Handoff Assembly

Create `analysis/handoff.xml` using template from `templates/analysis/handoff.xml`.

### Summary (2-4 paragraphs)

Concise description for downstream consumer:

```xml
<summary>
Users with mixed-case usernames cannot log in since v2.3.0 deployment. The validateCredentials function in src/auth/login.ts performs case-sensitive comparison against stored credentials, but user input is not normalized before validation.

The issue affects approximately 15% of users based on error log analysis. Authentication succeeds for all-lowercase usernames but fails for any username containing uppercase characters.

Root cause is missing username normalization before the credential validation check. The normalizeUsername helper exists but is not called in the validation path.

Fix requires calling normalizeUsername on user input before credential comparison. Should also add test coverage for mixed-case usernames.
</summary>
```

### Code Context

```xml
<code_context>
  <affected_files>
    <file path="src/auth/login.ts" reason="Contains bug" />
  </affected_files>
  
  <key_symbols>
    <symbol path="src/auth/login.ts" name="validateCredentials" line="42" />
  </key_symbols>
  
  <critical_sections>
    <section path="src/auth/login.ts" start="42" end="58" note="Missing normalization call" />
  </critical_sections>
</code_context>
```

### Known Items

```xml
<known>
  <item>Issue started after v2.3.0 deployment</item>
  <item>Affects only mixed-case usernames</item>
  <item>normalizeUsername helper already exists but unused</item>
  <item>No test coverage for mixed-case usernames</item>
</known>
```

### References

```xml
<investigation_ref>analysis/investigation.xml</investigation_ref>
<issue_context_ref>ISSUE_CONTEXT.md</issue_context_ref>
```

## Step 5: Next Action Recommendation

Create `analysis/next-step.yaml` using template from `templates/analysis/next-step.yaml`.

```yaml
case_id: "login-case-sensitivity-bug"
timestamp: "2026-04-02T14:30:00Z"

recommended_action: resolve

confidence: high

reasoning: |
  Root cause is clear and fix is straightforward. The normalizeUsername
  helper already exists and just needs to be called before validation.
  High confidence that fix will resolve the issue.

prerequisites:
  - Access to test environment
  - Ability to verify with affected users

notes: |
  Should also add test coverage for mixed-case usernames to prevent
  regression. Consider auditing other authentication paths for similar issues.
```

**Action options**:
- `resolve` - Fix or final disposition needed
- `external_handoff` - Hand to external team
- `close_as_non_actionable` - No action needed
- `blocked` - Cannot proceed without input

## Step 6: Traceability Verification

Verify all references resolve:

✓ Evidence refs in `investigation.xml` point to existing curated materials  
✓ Repository refs point to actual files/symbols/lines  
✓ `handoff.xml` references `investigation.xml`  
✓ No broken links  

## Step 7: Readiness Verification

Run readiness checker:

```bash
python scripts/check_readiness.py <case-path> handoff_ready
```

**Pass conditions**:
- `investigation.xml` exists
- `handoff.xml` exists
- `next-step.yaml` exists
- Traceability intact across artifacts
- All references resolve

**If check fails**: Address blocking issues before declaring handoff ready.

## Step 8: Lifecycle Update

Update `status.yaml`:

```yaml
lifecycle: handoff_in_progress → handoff_ready
readiness:
  collect_ready: true
  handoff_ready: true
```

Log transition in `activity.md`.

## Refinement and Evaluation

Refinement and evaluation are actions on the same case, not separate modes.

If handoff needs improvement:
- Update artifacts in place within case
- Preserve traceability
- Log refinement reason in `activity.md`
- `lifecycle` stays `handoff_in_progress` until ready

## Post-Handoff Contradictions

If new evidence invalidates or materially contradicts `handoff_ready` case:

- Case must leave `handoff_ready`
- If resolvable from curated materials → move to `handoff_in_progress`
- If requires revisiting raw sources → move back to `collecting`
- Log reason in `activity.md`

## Boundaries

### Must Do

- Work from curated case workspace
- Synthesize investigation with evidence refs and expanded details
- Assemble traceable handoff with concise summary and code context
- Declare next recommended action
- Read `ISSUE_CONTEXT.md` when present
- Ensure traceability across all artifacts

### Must Not Do

- Force mandatory fixing (resolve is optional)
- Copy code excerpts into case workspace (use direct refs in v1)
- Create multiple per-problem handoff structures (one case = one handoff)
- Modify source roots (read-only against both issue materials and repository)
- Do unrestricted whole-repo exploration

## Exit Conditions

- **Success**: `lifecycle: handoff_ready`, ready for resolve or external handoff
- **Need Recollect**: `lifecycle: collecting` with reason documented
- **Blocked**: `lifecycle: blocked` with reason in `activity.md`

## Next Move

When handoff is ready:

- If `next-step.yaml` recommends `resolve` → load `commands/resolve.md`
- If recommends `external_handoff` → case ready for external use
- If recommends `close_as_non_actionable` → may close directly
- If `blocked` → document blocker and wait for resolution

## Workflow Reference

For detailed handoff workflow, see `workflows/handoff/handoff-workflow.md`.
