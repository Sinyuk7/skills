# Rewrite Proposals

## Skill: `openspec-explore`

### Current Risk

- Broad exploration wording can overlap with many upstream thinking or debugging requests
- Mode-switch nature is clearer in the body than in the top metadata
- Strongest boundary is behavioral, not procedural

### Proposed Name

`openspec-explore`

### Proposed Description

```yaml
description: |
  Enter explore mode for OpenSpec work: think through ideas, investigate
  problems, map codebase context, and clarify requirements before or during a
  change. Use when the user wants collaborative exploration, tradeoff analysis,
  or problem framing rather than implementation. Do not use for implementing
  features, editing production code, or forcing proposal/spec updates unless
  the user explicitly asks to capture the outcome.
```

### Trigger Additions

- Strong positive triggers: `explore this`, `think this through`, `clarify requirements`, `tradeoff analysis`, `before implementing`
- Weak cues: `mode switch`, `don't code yet`, `help me reason about this`
- Negative triggers: `implement this`, `write the code`, `apply the change now`
- Prerequisites: user wants discussion, investigation, or framing rather than execution
- Use proactively: yes, when the user clearly wants exploration before implementation

### Structural Recommendation

- `keep`, but surface the mode-switch nature earlier
