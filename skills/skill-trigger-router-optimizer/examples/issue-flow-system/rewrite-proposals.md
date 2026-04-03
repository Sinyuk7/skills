# Rewrite Proposals

## Skill: `issue-flow-core`

### Current Risk

- Could be misread as a candidate skill because it contains workflows and product docs

### Proposed Name

`issue-flow-core`

### Proposed Description

```yaml
description: |
  Shared runtime and design-time core for the issue-flow skill set.
  Not a user-facing skill and not a routing target.
  Read only when implementing, auditing, or maintaining issue-flow stage skills.
```

### Trigger Additions

- Strong positive triggers: `shared core`, `runtime assets`, `issue-flow architecture`
- Weak cues: `bootstrap .issue-flow-core`, `readiness model`
- Negative triggers: `start investigating`, `build handoff`, `fix issue`, `sync Overmind`
- Prerequisites: maintenance or architecture work on the issue-flow system
- Use proactively: no

### Structural Recommendation

- `keep`

## Skill: `issue-collect`

### Current Risk

- Slight overlap with handoff when users say "analyze this issue" but no case exists yet

### Proposed Name

`issue-collect`

### Proposed Description

```yaml
description: |
  Start or update an issue-flow case from raw issue materials such as logs,
  screenshots, archives, and notes. Use when a user is opening a fresh issue,
  adding new source material, or no curated case exists yet. Do not use for
  synthesizing an existing curated case into handoff artifacts or for fixing a
  case that already has `handoff.xml`.
```

### Trigger Additions

- Strong positive triggers: `start investigating`, `new issue`, `logs`, `screenshots`, `archives`, `add more evidence`
- Weak cues: `look at this bug`, `intake this problem`
- Negative triggers: `build handoff`, `write investigation`, `fix it`, `verify it`
- Prerequisites: at least one non-repo issue input, or an existing case that needs more collection
- Use proactively: yes, when a user provides raw issue materials without a case

### Structural Recommendation

- `keep`

## Skill: `issue-handoff`

### Current Risk

- "analysis" wording is good, but prerequisite on curated case can be even sharper

### Proposed Name

`issue-handoff`

### Proposed Description

```yaml
description: |
  Build investigation and handoff artifacts from an existing issue-flow case
  with curated evidence. Use when a case already exists and the user wants
  synthesis, root-cause analysis, or a traceable handoff for another engineer
  or later session. Do not use for fresh issue intake, adding raw materials,
  or implementing a fix from a completed handoff.
```

### Trigger Additions

- Strong positive triggers: `investigate this case`, `build handoff`, `root cause`, `summarize findings`
- Weak cues: `continue analysis`, `prepare for another engineer`
- Negative triggers: `new issue`, `collect logs`, `fix it now`, `sync to Overmind`
- Prerequisites: existing case workspace with curated evidence
- Use proactively: yes, when the user asks for synthesis on a curated case

### Structural Recommendation

- `keep`

## Skill: `issue-resolve`

### Current Risk

- Can under-specify that `handoff.xml` is a hard prerequisite and that repository changes require approval

### Proposed Name

`issue-resolve`

### Proposed Description

```yaml
description: |
  Continue an issue-flow case from an existing handoff into implementation,
  verification, or a final non-code disposition. Use when `handoff.xml`
  already exists and the user wants to fix, verify, or close the case.
  Do not use for fresh issue intake, investigation-only synthesis, or
  external tracker sync after resolution is already complete.
```

### Trigger Additions

- Strong positive triggers: `fix this case`, `verify the fix`, `close the case`, `implement resolution`
- Weak cues: `continue from handoff`, `take this to a fix`
- Negative triggers: `collect evidence`, `write handoff`, `sync overmind only`
- Prerequisites: existing `analysis/handoff.xml`
- Use proactively: yes, when the user asks for a fix or closure on a handed-off case

### Structural Recommendation

- `keep`

## Skill: `issue-overmind-sync`

### Current Risk

- Low, but should remain clearly post-resolve and plugin-like

### Proposed Name

`issue-overmind-sync`

### Proposed Description

```yaml
description: |
  Sync resolved issue-flow artifacts to Overmind via MCP after issue-resolve
  is complete. Use when a case already has resolve artifacts, when retrying a
  failed Overmind update, or when filling remaining bug fields from completed
  case outputs. Do not use for investigation, case collection, or performing
  the fix itself.
```

### Trigger Additions

- Strong positive triggers: `sync Overmind`, `fill bug fields`, `retry Overmind update`
- Weak cues: `submit this bug`, `write the reply`
- Negative triggers: `investigate issue`, `fix issue`, `build handoff`
- Prerequisites: completed resolve artifacts and explicit issue key
- Use proactively: no

### Structural Recommendation

- `keep`
