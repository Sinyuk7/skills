# Router Policy Draft

## Scope

- Skill set: `mcp-builder`
- Policy objective: route MCP-related build, review, and evaluation requests to one skill while keeping bundled docs non-routable
- Default routing depth: `static-first`

## Classification Rules

| Request Shape | Candidate Skills | Routing Mode | Notes |
|---------------|------------------|--------------|-------|
| Build a new MCP server | `mcp-builder` | `static` | Strong MCP creation intent |
| Review an MCP server against best practices | `mcp-builder` | `static` | Requires better metadata coverage |
| Generate evaluations for an MCP server | `mcp-builder` | `static` | Secondary intent already supported internally |
| Need TypeScript implementation path | `mcp-builder` | `static` | Branch internally to node guide |
| Need Python implementation path | `mcp-builder` | `static` | Branch internally to python guide |
| Open bundled references or scripts directly | none | `non-routable` | Load only after `mcp-builder` is selected |

## Priority Rules

1. Route user-facing MCP build, review, and eval requests to `mcp-builder`.
2. Never route directly to files under `reference/` or `scripts/`.
3. Use language choice as an internal branch after skill selection, not as a separate route.

## Tie-Break Rules

| Conflict Region | Preferred Skill | Why | Fallback |
|-----------------|-----------------|-----|----------|
| "Create evals for this MCP server" | `mcp-builder` | Eval creation is a supported phase of the same skill | Strengthen metadata if under-trigger persists |
| "Review my tool naming and annotations" | `mcp-builder` | Best-practices audit is supported through bundled references | Add audit wording to top-level description |

## Composition Rules

| Request Pattern | Policy | Execution Shape |
|-----------------|--------|-----------------|
| Design then implement | Route to `mcp-builder` | `internal chain` |
| Review then create evals | Route to `mcp-builder` | `internal chain` |
| Choose language then scaffold | Route to `mcp-builder` | `internal branch` |

## Parallel Fan-Out Rules

| Multi-Part Request | Skills | Synthesis Rule |
|--------------------|--------|----------------|
| None required | N/A | This package is a single routed skill |

## Abstain And Fallback

| Condition | Action |
|-----------|--------|
| Request is about a generic SDK wrapper with no MCP context | Abstain from `mcp-builder` |
| Request is about non-MCP evaluation design | Abstain from `mcp-builder` |
| MCP context is clear but language is unspecified | Route to `mcp-builder`, then decide language internally |

## Rollout Notes

1. Fix metadata first before splitting the skill.
2. Only consider splitting into `mcp-builder` and `mcp-evals` if eval requests remain hard to trigger after metadata rewrite.
3. Keep references and scripts as implementation resources, not route targets.
