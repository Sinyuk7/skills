# Investigation: {{case_id}}

## Working Statement

Investigate `{{primary_question}}` around `{{primary_time_anchor}}`.

## Investigation Target

- **Primary question:** {{primary_question}}
- **Primary time anchor:** {{primary_time_anchor}}
- **Stakeholders:** {{named_stakeholders}}

## Troubleshooting Guide

- **Status:** {{troubleshooting_guide.status}}   <!-- preloaded_from_upstream | loaded_from_repo | none -->
- **Source:** {{troubleshooting_guide.source}}
- **Note:** {{troubleshooting_guide.note}}

## Excavation Plan

- **Hypothesis:** {{excavation_plan.hypothesis}}
- **Tasks:**
  - `{{task.id}}` ({{task.kind}} on `{{task.target_source}}`) — {{task.why}}
  <!-- repeat per task; one line each -->

## Findings

Cite each finding with `source + locator + interpretation + confidence`. Label speculation as hypothesis.

### Evidence

- `{{finding.source}}:{{finding.locator}}` — {{finding.interpretation}} *(confidence: {{finding.confidence}})*
  > {{finding.excerpt}}
<!-- repeat per consolidated finding -->

### Code Correlation

Include only when Phase 3.2 produced entries.

- `{{code_finding.source}}:{{code_finding.locator}}` — {{code_finding.interpretation}}
  > {{code_finding.excerpt}}
<!-- repeat per code finding, max 3 -->

## Disposition

- **Type:** {{disposition.type}}   <!-- root_caused | direction_only | blocked | wont_fix | duplicate | already_fixed | cannot_reproduce -->
- **Summary:** {{disposition.summary}}

<!-- The sub-sections below are selected based on disposition.type -->

### If `root_caused`
- **Location:** {{disposition.root_cause_location}}
- **Evidence refs:** {{disposition.evidence_refs}}

### If `direction_only`
Ranked investigation directions:
1. **{{direction.hypothesis}}** — next experiment: {{direction.next_experiment}}
<!-- repeat by rank -->

### If `blocked`
- **Reason kind:** {{disposition.blocked_reason.kind}}
- **Detail:** {{disposition.blocked_reason.detail}}

### If `duplicate`
- **Duplicate of:** {{disposition.duplicate_of}}

### If `already_fixed`
- **Reference:** {{disposition.reference}}

## Next Step

{{next_step.action}} — {{next_step.note}}
