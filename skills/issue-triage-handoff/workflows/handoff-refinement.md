# Handoff Refinement Workflow

Update an existing handoff with new evidence.

## Prerequisites

Read these files:
- `knowledge/handoff-schema.md` - Output structure
- `knowledge/evidence-protocol.md` - Evidence referencing

Read the existing handoff to understand current state.

---

## Step 1: Identify New Materials (Deterministic)

Record what user is adding:
- New log files or archives
- New comments or discussion
- Additional trace/request IDs
- Corrected version/environment info
- New hypothesis from team member

Add timestamp for when each addition joined the investigation.

Output: List of new materials with addition timestamps

---

## Step 2: Evidence Integration (Deterministic)

For new log files, run collection script:

```
Script: ./scripts/collect-log-evidence.sh
Input: new log paths, existing key identifiers, time window
Output: new evidence entries
```

Assign new evidence IDs continuing from existing sequence.
- If existing: E001-E015
- New: E016, E017, ...

Output: `evidence_inventory[]` extended with new entries

---

## Step 3: Conflict Analysis (LLM)

Compare new evidence against existing handoff:

### 3.1 Confirmations
New evidence confirms existing inferences:
- Promote `bounded_inferences` → `confirmed_facts` if now supported
- Update evidence refs

### 3.2 Contradictions
New evidence contradicts existing conclusions:
- Flag conflict explicitly
- Keep both pieces of evidence
- Move affected item to `open_questions` if unresolved
- **Do not** silently overwrite

### 3.3 Extensions
New evidence adds to the picture:
- New error types
- Earlier/later timeline events
- Additional affected components

Output: Classification of each new evidence item

---

## Step 4: Merge Execution (Deterministic)

Apply merge rules:

### Timeline Merge
Insert new events chronologically.

### Evidence Merge
Add new entries with:
- Unique `evidence_id` (continuing sequence)
- Source marked as "supplemental material [date]"
- Cross-reference to related original evidence

### Code Mapping Merge
| Scenario | Action |
|----------|--------|
| New evidence → new code location | Add to `code_mapping[]` |
| New evidence strengthens existing | Update confidence level |
| New evidence contradicts existing | Flag conflict |

### Findings Merge
- Apply confirmation/contradiction/extension logic from Step 3
- Remove answered items from `open_questions`
- Add new open questions

Output: Updated handoff sections

---

## Step 5: Conflict Documentation (Deterministic)

If contradictions found, add `conflicts` section:

```json
{
  "conflicts": [
    {
      "description": "Timestamp of first error",
      "original": "10:15:03 based on log A",
      "original_ref": "E003",
      "contradicting": "10:14:58 based on log B",
      "contradicting_ref": "E018",
      "resolution": "pending"
    }
  ]
}
```

Output: `conflicts[]` populated (if any)

---

## Step 6: Version Update (Deterministic)

Update handoff metadata:
- Increment `version` number
- Add revision note explaining changes
- Preserve original `created_at`
- Update `last_modified` to now

Output: `case_meta` updated

---

## Step 7: Self-Check (Deterministic)

Verify:
- [ ] New evidence has unique IDs (no collisions)
- [ ] All new evidence integrated with proper refs
- [ ] Conflicts explicitly documented
- [ ] Promoted/demoted findings are justified
- [ ] Timeline remains chronologically coherent
- [ ] Version metadata updated
- [ ] Output passes schema validation

---

## Data Flow Summary

```
Existing Handoff ─────────────────────────────┐
                                              │
Step 1 (D): new_materials[] ──────────────────┤
Step 2 (D): new_evidence[] ───────────────────┤
Step 3 (L): conflict_analysis ────────────────┤
Step 4 (D): merged_sections ◄─────────────────┤
Step 5 (D): conflicts[] ◄─────────────────────┤
Step 6 (D): updated_metadata ◄────────────────┤
Step 7 (D): validation_result                 │
                                              ▼
                                    Updated Handoff
```

---

## Next Move

If user wants to evaluate the refined handoff: load `workflows/handoff-evaluation.md`
If user has more materials to add: stay in this workflow