# Handoff Evaluation Workflow

Assess whether a handoff is ready for downstream agents or human reviewers.

## Prerequisites

Read these files:
- `knowledge/handoff-schema.md` - Structural requirements
- `knowledge/triage-principles.md` - Principle adherence check

Read the handoff to evaluate.

---

## Step 1: Structural Completeness Check (Deterministic)

Validate against schema:

```
Schema: ./schemas/handoff.schema.json
```

Check required fields:

| Field | Required | Validation |
|-------|----------|------------|
| case_meta.title | Yes | Non-empty string |
| case_meta.created_at | Yes | ISO 8601 timestamp |
| case_meta.sources | Yes | At least one item |
| context_summary.problem_statement | Yes | Non-empty string |
| evidence_inventory | Yes | At least one item |
| findings.confirmed_facts | Yes | Array exists |
| findings.bounded_inferences | Yes | Array exists |
| findings.open_questions | Yes | Should have ≥1 item |
| handoff_summary.scope | Yes | Non-empty string |

Output: `structural_issues[]`

---

## Step 2: Evidence Quality Check (Deterministic)

For each evidence item, verify:
- [ ] Has unique `evidence_id`
- [ ] Has valid `source_ref` (path or URL exists)
- [ ] Has `content` or `excerpt` field
- [ ] Timestamp is parseable (if present)

Detect:
- Orphan evidence: not referenced by any finding
- Missing evidence: referenced but not in inventory
- Duplicate evidence: same content, different IDs

Output: `evidence_issues[]`

---

## Step 3: Traceability Check (Deterministic)

For each finding in `confirmed_facts` and `bounded_inferences`:
- [ ] Has at least one `evidence_ref`
- [ ] Referenced evidence exists in inventory

For each code_mapping entry:
- [ ] Has `evidence_refs`
- [ ] All referenced evidence exists

Output: `traceability_issues[]`

---

## Step 4: Code Mapping Quality Check (Deterministic)

For each code location:
- [ ] File path format is valid
- [ ] Line range is reasonable (not 0-0 or 10000+ span)
- [ ] Confidence matches match_type:

| match_type | Expected confidence |
|------------|---------------------|
| stacktrace | high |
| symbol_search | medium or high |
| route_mapping | medium |
| keyword | low or medium |

- [ ] Has evidence_ref

Output: `code_mapping_issues[]`

---

## Step 5: Boundary Adherence Check (LLM)

Verify handoff does NOT contain:
- Root cause claims (beyond bounded inference)
- Patch suggestions
- Fix recommendations
- Blame attribution
- Performance recommendations

If found, flag as scope violation.

Output: `boundary_violations[]`

---

## Step 6: Downstream Readiness Assessment (LLM)

Evaluate fitness for consumers:

### For RCA Agent
- Is timeline clear enough to trace causality?
- Are error signatures distinct?
- Are key identifiers extracted?

### For Patch Agent
- Are code locations specific enough?
- Is mapping confidence reasonable?
- Are relevant symbols identified?

### For Human Reviewer
- Is summary comprehensible?
- Are gaps and uncertainties clear?
- Can evidence be traced to sources?

### Context-Aware Checks

**If project-context.md exists**, verify:

1. **Team Role Alignment**:
   - If `team_role: provider` → Check that recommendations focus on internal code/config
   - If `team_role: consumer` → Check that recommendations focus on integration/external behavior
   - If `team_role: integration` → Check that recommendations balance upstream/downstream

2. **Ownership Boundary Validation**:
   - All code_mapping entries should reference files in `ownership.our_code` OR be marked as external
   - Recommended next steps should NOT suggest investigating code outside `ownership.our_code`

3. **Forbidden Assumptions Check**:
   - Scan `recommended_next_steps` and `handoff_summary.scope` for phrases in `forbidden_assumptions`
   - If found, flag as **attribution error**

**Example**:
```yaml
# If context says:
team_role: provider
ownership:
  our_code: ["openapi.music.163.com API server"]
forbidden_assumptions:
  - "Assume openapi.music.163.com is external"

# Then handoff should NOT say:
"Check if external server openapi.music.163.com is down"

# Instead should say:
"Investigate our API server openapi.music.163.com timeout configuration"
```

Output: `downstream_readiness` with status for each consumer + `context_validation_issues[]`

---

## Step 7: Quality Score (LLM)

Rate on 5-point scale:

| Dimension | 1 | 3 | 5 |
|-----------|---|---|---|
| Completeness | Major fields missing | Most present | All present with depth |
| Traceability | Few evidence refs | Most claims have refs | Full coverage |
| Precision | Vague locations | Some specific | Specific files/lines |
| Boundary | Contains fixes/RCA | Minor scope creep | Stays in triage lane |
| Clarity | Hard to follow | Mostly clear | Clear and organized |

Verdicts:
- Score < 2.5: **Not ready**, needs significant work
- Score 2.5-3.5: **Usable with caveats**
- Score > 3.5: **Ready** for downstream

Output: `scores{}` and `verdict`

---

## Step 8: Recommendations (LLM)

If score < 3.5, generate specific recommendations:

```
Priority | Issue | Recommendation
---------|-------|---------------
High     | 3 findings lack refs | Add evidence_ref to X, Y, Z
Medium   | Timeline has 2hr gap | Search logs for 14:00-16:00
Low      | Confidence inconsistent | Review match_type assignments
```

Output: `recommendations[]`

---

## Step 9: Output Generation (Deterministic)

Generate evaluation JSON:

```
Schema: ./schemas/evaluation.schema.json
```

```json
{
  "evaluation_timestamp": "ISO timestamp",
  "handoff_version": "version evaluated",
  "structural_issues": [],
  "evidence_issues": [],
  "traceability_issues": [],
  "code_mapping_issues": [],
  "boundary_violations": [],
  "downstream_readiness": {
    "rca_agent": "ready|usable|not_ready",
    "patch_agent": "ready|usable|not_ready",
    "human_reviewer": "ready|usable|not_ready"
  },
  "scores": {
    "completeness": 1-5,
    "traceability": 1-5,
    "precision": 1-5,
    "boundary": 1-5,
    "clarity": 1-5,
    "overall": 1-5
  },
  "verdict": "ready|usable_with_caveats|needs_work",
  "recommendations": []
}
```

---

## Data Flow Summary

```
Handoff to Evaluate ─────────────────────────────────────┐
                                                         │
Step 1 (D): structural_issues[] ─────────────────────────┤
Step 2 (D): evidence_issues[] ───────────────────────────┤
Step 3 (D): traceability_issues[] ───────────────────────┤
Step 4 (D): code_mapping_issues[] ───────────────────────┤
Step 5 (L): boundary_violations[] ───────────────────────┤
Step 6 (L): downstream_readiness{} ──────────────────────┤
Step 7 (L): scores{}, verdict ───────────────────────────┤
Step 8 (L): recommendations[] ───────────────────────────┤
Step 9 (D): evaluation.json ◄────────────────────────────┘
```

---

## Next Move

If evaluation reveals gaps: load `workflows/handoff-refinement.md`
If starting fresh is easier: load `workflows/new-triage-handoff.md`
