# Routing Audit Report

## Scope

- Target: `openspec-explore`
- Inputs reviewed:
  - `/Users/shenyeke01/.claude/skills/openspec-explore/SKILL.md`
- Audit depth: `standard`

## Routing Surface Summary

| Skill | Routing Role | Primary Intents | Boundary Risk | Suggested Mode |
|-------|--------------|-----------------|---------------|----------------|
| `openspec-explore` | `routable_skill` | Explore ideas, investigate problems, clarify requirements before or during a change | Medium | `static` |

## Key Findings

`openspec-explore` is a user-facing routable skill, but it is not a normal
workflow skill. It is a stance or mode-switch skill:

- no fixed procedure
- no mandatory artifact output
- collaboration style is part of the product surface
- strongest boundary is behavioral: think deeply, do not implement

The main routing risk is not missing resources or package confusion.
The main risk is that the description is broad enough to overlap with:

- general brainstorming
- architecture investigation
- mid-change debugging or design discussion

That broadness is intentional, but it means boundary language matters a lot.

## Overlap Findings

| Intent Region | Skills | Problem | Recommendation |
|---------------|--------|---------|----------------|
| "Help me think this through" | external neighboring exploration/planning skills | Could overlap with other ideation or review skills | Keep focus on pre-implementation exploration and requirement clarification |
| "Investigate the codebase" | implementation or debugging skills | Investigation wording alone may route to execution-oriented skills | Preserve explicit "thinking, not implementing" boundary |
| "Update OpenSpec artifacts based on exploration" | proposal/design/spec skills | It may look like a drafting skill even though artifact capture is optional | Tie-break on user intent: capture only when the user asks |

## Gap Findings

| Missing Intent | Impact | Recommendation |
|----------------|--------|----------------|
| "Mode-switch into collaborative exploration" | Users may not realize this is a behavioral mode, not just a topic-specific helper | Add wording like `enter explore mode` and `switch to thinking mode` to trigger surface |
| "I want discussion, not implementation" | May under-trigger if the user phrases this negatively instead of naming explore mode | Add negative implementation cues to examples or description |

## Chain And Parallel Opportunities

| Request Pattern | Relation | Recommendation |
|-----------------|----------|----------------|
| Explore -> crystallize -> create proposal | `chain` | Keep exploration first, formalize later only if requested |
| Explore mid-change -> update design/tasks | `chain` | Exploration can precede artifact capture, but should not auto-capture |
| Explore while implementation is requested | `exclusive` | Stay in explore mode and refuse implementation until the mode changes |

## Priority Fixes

1. Make "mode switch" language more explicit near the top-level route surface.
2. Preserve the negative boundary against implementation, since that is the strongest arbitration rule.
3. Teach the router optimizer that some skills are stance-driven and should not be penalized for lacking workflows or bundled resources.
