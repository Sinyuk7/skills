# Handoff Refinement Workflow

Use this workflow when a handoff already exists and the user wants to update it with new evidence.

## Prerequisites

Load:
- `knowledge/handoff-schema.md` - Output structure
- `knowledge/evidence-protocol.md` - Evidence referencing

Read the existing handoff to understand current state.

## Step 1: Identify New Materials

Determine what the user is adding:
- New log files or archives
- New comments or discussion
- Additional trace/request IDs
- Corrected version/environment info
- New hypothesis from team member

Record each addition with timestamp of when it was added to the investigation.

## Step 2: Validate Against Existing Handoff

Check for:

### 2.1 Confirmations
New evidence that confirms existing inferences:
- Promote `bounded_inferences` to `confirmed_facts` if now supported
- Update evidence refs

### 2.2 Contradictions
New evidence that contradicts existing conclusions:
- Flag the conflict explicitly
- Keep both pieces of evidence
- Move affected item to `open_questions` if resolution is unclear
- Do NOT silently overwrite

### 2.3 Extensions
New evidence that adds to the picture:
- New error types
- Earlier/later timeline events
- Additional affected components

## Step 3: Merge Protocol

### Timeline Merge
Insert new events into existing timeline, maintaining chronological order.

### Evidence Merge
Add new evidence entries with:
- Unique `evidence_id`
- Source marked as "supplemental material [date]"
- Cross-reference to original handoff evidence if related

### Code Mapping Merge
If new evidence points to new code locations:
- Add to code_mapping with new evidence refs
- If new evidence strengthens existing mapping, update confidence level
- If new evidence contradicts existing mapping, flag conflict

### Findings Merge
- Review each finding category
- Apply confirmation/contradiction/extension logic
- Update `open_questions` to remove answered ones, add new ones

## Step 4: Conflict Documentation

If any contradictions were found, add a `conflicts` section:

```json
{
  "conflicts": [
    {
      "description": "Timestamp of first error",
      "original": "10:15:03 based on log A",
      "new_evidence": "10:14:58 based on log B",
      "resolution": "pending" | "resolved to X because Y"
    }
  ]
}
```

## Step 5: Version Tracking

Update handoff metadata:
- Increment version number
- Add revision note explaining what changed
- Preserve original creation timestamp
- Update last_modified timestamp

## Step 6: Self-Check

Before delivering:
- [ ] New evidence integrated with proper refs
- [ ] Conflicts explicitly documented
- [ ] Promoted/demoted findings are justified
- [ ] Timeline remains coherent
- [ ] Version metadata updated

## Next Move

If user wants to evaluate the refined handoff, load `workflows/handoff-evaluation.md`.

If user has more materials to add, stay in this workflow.
