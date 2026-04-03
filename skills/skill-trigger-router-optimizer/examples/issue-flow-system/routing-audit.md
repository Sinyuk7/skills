# Routing Audit Report

## Scope

- Target: `issue-flow` skill set
- Inputs reviewed:
  - `skills/issue-flow-core/README.md`
  - `skills/issue-flow-core/PRD.md`
  - `skills/issue-collect/SKILL.md`
  - `skills/issue-handoff/SKILL.md`
  - `skills/issue-resolve/SKILL.md`
  - `skills/issue-overmind-sync/SKILL.md`
- Audit depth: `standard`

## Routing Surface Summary

| Skill | Primary Intents | Boundary Risk | Suggested Mode |
|-------|-----------------|---------------|----------------|
| `issue-flow-core` | Shared workflow source, templates, readiness model | High if treated as routable skill | `non-routable shared core` |
| `issue-collect` | Start or update a case from raw issue materials | Medium | `static` |
| `issue-handoff` | Synthesize curated evidence into investigation and handoff artifacts | Medium | `static` |
| `issue-resolve` | Continue from handoff into implementation, verification, or final disposition | Medium | `static` |
| `issue-overmind-sync` | Sync resolved case artifacts into Overmind | Low | `static` |

## Key Finding

`issue-flow-core` should not participate in user-facing routing.
It is correctly modeled as a shared core package, not as a trigger target.
The routable surface belongs to the thin entry skills and optional plugin skills.

## Overlap Findings

| Intent Region | Skills | Problem | Recommendation |
|---------------|--------|---------|----------------|
| "Analyze this bug / look at these logs" | `issue-collect`, `issue-handoff` | User wording may ask for analysis before a case exists | Tie-break on prerequisites first: if there is no existing curated case, route to `issue-collect` |
| "Continue this issue" | `issue-handoff`, `issue-resolve` | "Continue" is too vague without artifact state or desired action | Tie-break on artifact + verb: `handoff.xml` required for `issue-resolve`; "fix/verify/close" favors resolve |
| "Finish the bug and sync it" | `issue-resolve`, `issue-overmind-sync` | This is a chain, not a true overlap | Model as `chain`: resolve first, then optional sync |

## Gap Findings

| Missing Intent | Impact | Recommendation |
|----------------|--------|----------------|
| "I don't know which issue-flow stage I need" | User may choose the wrong stage skill manually | Add a lightweight stage-router policy based on case state and requested action |
| "Resume the next recommended step for this case" | Existing skills assume the user already picked the stage | Route by `status.yaml`, readiness markers, and verb cues |

## Chain And Parallel Opportunities

| Request Pattern | Relation | Recommendation |
|-----------------|----------|----------------|
| Fresh issue materials -> curated case -> handoff | `chain` | `issue-collect` then `issue-handoff` |
| Existing handoff -> fix/verify -> tracker sync | `chain` | `issue-resolve` then `issue-overmind-sync` |
| Investigation plus external sync in one request | `chain`, not `parallel` | Keep sync post-resolve; do not fan out in parallel |

## Priority Fixes

1. Preserve `issue-flow-core` as a non-routable shared core and do not add a `SKILL.md` entrypoint there.
2. Strengthen prerequisite language in `issue-handoff` and `issue-resolve` so stage selection can be made from metadata alone.
3. Add explicit negative triggers for cross-stage requests such as "start a fresh issue" vs "fix an existing handoff".
