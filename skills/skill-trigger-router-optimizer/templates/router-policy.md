# Router Policy Draft

## Scope

- Skill set:
- Policy objective:
- Default routing depth: `static-first|hybrid-first|llm-first`

## Classification Rules

| Request Shape | Candidate Skills | Routing Mode | Notes |
|---------------|------------------|--------------|-------|
|               |                  |              |       |

## Priority Rules

1. Prefer the skill with explicit primary-intent ownership.
2. If multiple skills match, prefer the one with the strongest positive trigger coverage.
3. If ambiguity remains, apply the tie-break rules below.

## Tie-Break Rules

| Conflict Region | Preferred Skill | Why | Fallback |
|-----------------|-----------------|-----|----------|
|                 |                 |     |          |

## Composition Rules

| Request Pattern | Policy | Execution Shape |
|-----------------|--------|-----------------|
|                 |        |                 |

## Parallel Fan-Out Rules

| Multi-Part Request | Skills | Synthesis Rule |
|--------------------|--------|----------------|
|                    |        |                |

## Abstain And Fallback

| Condition | Action |
|-----------|--------|
|           |        |

## Rollout Notes

1. Fix highest-cost overlap first.
2. Update metadata before router logic when possible.
3. Add eval coverage for each new arbitration rule.
