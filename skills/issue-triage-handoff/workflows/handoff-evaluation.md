# Handoff Evaluation Workflow

Use this workflow when the user wants to assess whether a handoff is ready for downstream agents or human reviewers.

## Prerequisites

Load:
- `knowledge/handoff-schema.md` - To check structural completeness
- `knowledge/triage-principles.md` - To check principle adherence

Read the handoff to evaluate.

## Step 1: Structural Completeness Check

Verify required fields are present and non-empty:

| Field | Required | Check |
|-------|----------|-------|
| case_meta | Yes | Has title, created_at, sources |
| context_summary | Yes | Has problem_statement, environment |
| evidence_inventory | Yes | At least one evidence item |
| timeline | No | If present, has at least one event |
| code_mapping | No | If present, entries have evidence_refs |
| findings.confirmed_facts | Yes | May be empty but must exist |
| findings.bounded_inferences | Yes | May be empty but must exist |
| findings.open_questions | Yes | Should have at least one item |
| handoff_summary | Yes | Has scope, confidence, gaps |

## Step 2: Evidence Quality Check

For each evidence item:
- [ ] Has unique `evidence_id`
- [ ] Has valid `source_ref` pointing to actual material
- [ ] Has `content` or `excerpt` field
- [ ] Timestamp is parseable (if present)

Flag issues:
- Orphan evidence (not referenced by any finding)
- Missing evidence (referenced but not in inventory)
- Duplicate evidence (same content, different IDs)

## Step 3: Traceability Check

For each finding in `confirmed_facts` and `bounded_inferences`:
- [ ] Has at least one `evidence_ref`
- [ ] Referenced evidence exists in inventory
- [ ] Inference logic is stated (for bounded_inferences)

Flag:
- Unsupported claims (no evidence ref)
- Weak support (evidence doesn't clearly support claim)

## Step 4: Code Mapping Quality Check

For each code location:
- [ ] File path is valid (exists in repo if repo is available)
- [ ] Line range is reasonable (not 0-0 or spanning thousands of lines)
- [ ] Confidence level matches match_type:
  - `stacktrace` → should be `high`
  - `symbol_search` with exact match → should be `medium` or `high`
  - `keyword` → should be `low` or `medium`
- [ ] Has evidence_ref

Flag:
- High confidence without stacktrace evidence
- Code locations without any evidence backing

## Step 5: Boundary Adherence Check

Verify the handoff does NOT contain:
- [ ] Root cause claims (should be in inferences at most)
- [ ] Patch suggestions
- [ ] Fix recommendations
- [ ] Blame attribution
- [ ] Performance recommendations

If found, flag as scope violation.

## Step 6: Downstream Readiness Assessment

Evaluate fitness for different downstream consumers:

### For RCA Agent
- Is timeline clear enough to trace causality?
- Are error signatures distinct?
- Are key identifiers extracted?

### For Patch Agent
- Are code locations specific enough?
- Is the mapping confidence reasonable?
- Are the relevant symbols identified?

### For Human Reviewer
- Is the summary comprehensible?
- Are gaps and uncertainties clear?
- Can evidence be followed back to sources?

## Step 7: Quality Score

Rate on 5-point scale:

| Dimension | 1 | 3 | 5 |
|-----------|---|---|---|
| Completeness | Major fields missing | Most fields present | All fields present with depth |
| Traceability | Few evidence refs | Most claims have refs | Full ref coverage |
| Precision | Vague locations | Some specific locations | Specific files/lines/symbols |
| Boundary | Contains fixes/RCA | Minor scope creep | Stays in triage lane |
| Clarity | Hard to follow | Mostly clear | Clear and organized |

Overall readiness:
- Score < 2.5: Not ready, needs significant work
- Score 2.5-3.5: Usable with caveats
- Score > 3.5: Ready for downstream

## Step 8: Improvement Recommendations

If score < 3.5, provide specific recommendations:

```
Priority | Issue | Recommendation
---------|-------|---------------
High     | 3 findings lack evidence refs | Add evidence_ref to items X, Y, Z
Medium   | Timeline has 2-hour gap | Search logs for 14:00-16:00 window
Low      | Code mapping confidence inconsistent | Review match_type assignments
```

## Output

Deliver evaluation as:

```json
{
  "evaluation_timestamp": "ISO timestamp",
  "handoff_version": "version being evaluated",
  "structural_completeness": {
    "missing_required": [],
    "missing_optional": [],
    "empty_required": []
  },
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

## Next Move

If evaluation reveals gaps, offer to load `workflows/handoff-refinement.md` to address them.

If starting fresh would be easier, offer to load `workflows/new-triage-handoff.md`.
