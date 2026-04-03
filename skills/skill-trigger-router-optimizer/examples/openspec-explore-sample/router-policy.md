# Router Policy Draft

## Scope

- Skill set: `openspec-explore`
- Policy objective: route exploration-mode requests to a stance-driven skill without confusing it with implementation
- Default routing depth: `static-first`

## Classification Rules

| Request Shape | Candidate Skills | Routing Mode | Notes |
|---------------|------------------|--------------|-------|
| Think through an idea before implementation | `openspec-explore` | `static` | Strong exploration intent |
| Clarify requirements during a change | `openspec-explore` | `static` | Change-context exploration still belongs here |
| Explore codebase implications without editing code | `openspec-explore` | `static` | Behavioral boundary is key |
| Implement the change now | none | `abstain` | Out of scope for this skill |

## Priority Rules

1. Route to `openspec-explore` when the user wants thinking, framing, comparison, or investigation without implementation.
2. Do not route to `openspec-explore` for direct implementation requests.
3. If the user wants artifact capture, keep capture optional unless explicitly requested.

## Tie-Break Rules

| Conflict Region | Preferred Skill | Why | Fallback |
|-----------------|-----------------|-----|----------|
| "Investigate this problem" with no implementation request | `openspec-explore` | Investigation is valid if framed as exploration | Ask whether the user wants analysis or implementation |
| "Update the design based on this discussion" | `openspec-explore` first | Discussion precedes capture | Offer artifact update after exploration |

## Composition Rules

| Request Pattern | Policy | Execution Shape |
|-----------------|--------|-----------------|
| Explore then propose | Route to `openspec-explore` first | `chain` |
| Explore then update design/tasks | Route to `openspec-explore` first | `chain` |

## Parallel Fan-Out Rules

| Multi-Part Request | Skills | Synthesis Rule |
|--------------------|--------|----------------|
| None required | N/A | This is a single mode skill |

## Abstain And Fallback

| Condition | Action |
|-----------|--------|
| User asks for implementation | Decline implementation in explore mode and suggest switching modes |
| User asks for automatic artifact changes without discussion | Confirm they want capture rather than exploration |

## Rollout Notes

1. Preserve broad exploration coverage, but tighten behavioral boundaries.
2. Prefer negative triggers over procedural rules, because this skill is defined by stance.
3. Evaluate trigger quality with thin-context "don't code yet" requests.
