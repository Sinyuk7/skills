# Rewrite Proposals

## Skill: `mcp-builder`

### Current Risk

- Primary trigger is strong for "build an MCP server"
- Secondary supported intents are underexposed in metadata
- Long monolithic body makes internal routing harder to infer early

### Proposed Name

`mcp-builder`

### Proposed Description

```yaml
description: |
  Design, build, review, and evaluate MCP (Model Context Protocol) servers for
  external APIs and services. Use when creating a new MCP server, choosing a
  Python or TypeScript implementation path, reviewing tool design against MCP
  best practices, or generating read-only evaluations for an existing MCP
  server. Do not use for generic API client generation unrelated to MCP or for
  non-MCP evaluation design.
```

### Trigger Additions

- Strong positive triggers: `build MCP server`, `FastMCP`, `TypeScript MCP SDK`, `MCP tools`, `MCP evals`, `review MCP server`
- Weak cues: `tool annotations`, `pagination design`, `readOnlyHint`, `generate evaluation questions`
- Negative triggers: `generic SDK wrapper`, `non-MCP API client`, `general coding evals`
- Prerequisites: target service or API is known, or an existing MCP server already exists
- Use proactively: yes, when a user is building or auditing an MCP server

### Structural Recommendation

- `keep`, but add internal intent dispatch near the top

## Target: `reference/*` and `scripts/*`

### Current Risk

- None for user-facing routing, but they could be mistaken for separate skill units during package analysis

### Proposed Description

```yaml
description: |
  Bundled references and helper scripts for the mcp-builder skill.
  Not user-facing routing targets.
```

### Trigger Additions

- Strong positive triggers: `reference`, `implementation guide`, `helper script`
- Weak cues: `best practices doc`, `evaluation guide`
- Negative triggers: `build server`, `review my MCP`, `generate evals`
- Prerequisites: only load when the mcp-builder workflow requests them
- Use proactively: no

### Structural Recommendation

- `keep`
