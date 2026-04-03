# Router Policy Draft

## Scope

- Skill set: `issue-collect`, `issue-handoff`, `issue-resolve`, `issue-overmind-sync`
- Policy objective: select the correct issue-flow stage skill from user intent plus case readiness
- Default routing depth: `static-first`

## Classification Rules

| Request Shape | Candidate Skills | Routing Mode | Notes |
|---------------|------------------|--------------|-------|
| Fresh issue materials, no case yet | `issue-collect` | `static` | Trigger on raw material words and missing case state |
| Existing curated case, needs synthesis or analysis | `issue-handoff` | `static` | Require curated case signals |
| Existing handoff, wants fix, verification, or closure | `issue-resolve` | `static` | Require `handoff.xml` or explicit handoff state |
| Resolved case, wants tracker sync only | `issue-overmind-sync` | `static` | Require resolve artifacts and Overmind intent |
| User asks to resume but does not name a stage | `issue-collect`, `issue-handoff`, `issue-resolve` | `hybrid` | Use case state first, then verb cues |

## Priority Rules

1. Never route to `issue-flow-core` for user execution.
2. Prefer artifact prerequisites over loose intent wording.
3. Prefer stage ownership over generic verbs such as "continue" or "analyze".

## Tie-Break Rules

| Conflict Region | Preferred Skill | Why | Fallback |
|-----------------|-----------------|-----|----------|
| "Analyze this bug" without case | `issue-collect` | No curated case means intake still owns the work | Ask whether a case already exists |
| "Continue this case" with curated evidence but no handoff | `issue-handoff` | Synthesis stage owns progression into handoff | Ask for case path if not provided |
| "Finish and sync this bug" with handoff but no resolve artifacts | `issue-resolve` | Sync is post-resolve | Chain to `issue-overmind-sync` after resolve |

## Composition Rules

| Request Pattern | Policy | Execution Shape |
|-----------------|--------|-----------------|
| Collect then analyze | Route to `issue-collect` first | `chain` |
| Handoff then fix | Route to `issue-handoff` first if no handoff exists | `chain` |
| Resolve then sync Overmind | Route to `issue-resolve` then `issue-overmind-sync` | `chain` |

## Parallel Fan-Out Rules

| Multi-Part Request | Skills | Synthesis Rule |
|--------------------|--------|----------------|
| None recommended in v1 | N/A | Issue-flow stages are stateful and sequential |

## Abstain And Fallback

| Condition | Action |
|-----------|--------|
| Missing case path and ambiguous target case | Ask user which case should receive the write |
| User intent is "resume" but stage markers are absent | Inspect `status.yaml` and readiness artifacts before routing |
| Prerequisite artifact is missing for the requested stage | Route back to the prior owning stage |

## Rollout Notes

1. Tighten metadata for stage prerequisites before introducing a new top-level router.
2. If a top-level router is added later, make it inspect readiness markers instead of guessing from verbs alone.
3. Add eval cases for every cross-stage ambiguity named above.
