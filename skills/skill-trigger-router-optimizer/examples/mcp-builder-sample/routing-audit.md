# Routing Audit Report

## Scope

- Target: `mcp-builder` package
- Inputs reviewed:
  - `skills/mcp-builder/SKILL.md`
  - `skills/mcp-builder/reference/mcp_best_practices.md`
  - `skills/mcp-builder/reference/evaluation.md`
  - `skills/mcp-builder/reference/node_mcp_server.md`
  - `skills/mcp-builder/reference/python_mcp_server.md`
  - `skills/mcp-builder/scripts/example_evaluation.xml`
- Audit depth: `standard`

## Routing Surface Summary

| Skill | Routing Role | Primary Intents | Boundary Risk | Suggested Mode |
|-------|--------------|-----------------|---------------|----------------|
| `mcp-builder` | `routable_skill` | Build MCP servers, choose Python vs TypeScript implementation path, design tools | Medium | `static` |
| `reference/mcp_best_practices.md` | `non_routable_reference` | Naming, transport, pagination, annotations | Low | `non-routable` |
| `reference/evaluation.md` | `non_routable_reference` | MCP evaluation design | Low | `non-routable` |
| `reference/node_mcp_server.md` | `non_routable_reference` | TypeScript implementation details | Low | `non-routable` |
| `reference/python_mcp_server.md` | `non_routable_reference` | Python implementation details | Low | `non-routable` |
| `scripts/*` | `non_routable_reference` | Helper scripts for evaluation and connections | Low | `non-routable` |

## Key Findings

`mcp-builder` is correctly a user-facing routable skill.

The main routing risk is not overlap with neighboring skills inside this package.
The main risk is that the metadata strongly signals "build an MCP server" but
only weakly signals two real secondary intents already supported by the skill:

1. review an existing MCP server design against best practices
2. create evaluations for an existing MCP server

That means the skill may under-trigger for requests like:

- "generate evals for this MCP server"
- "review my MCP tool naming and pagination design"
- "help me add evaluation questions to my MCP server"

## Overlap Findings

| Intent Region | Skills | Problem | Recommendation |
|---------------|--------|---------|----------------|
| "Build an MCP server" vs "evaluate an MCP server" | internal to `mcp-builder` | Multiple real intents live in one large skill, but metadata mostly highlights build flow | Add explicit internal intent dispatch or strengthen metadata with eval/review triggers |
| "Pick Python or TypeScript path" | internal to `mcp-builder` | Language fork exists, but is expressed inside the body rather than the route surface | Keep single skill, but mention language choice in trigger examples |

## Gap Findings

| Missing Intent | Impact | Recommendation |
|----------------|--------|----------------|
| "Create or improve evals for an existing MCP server" | Likely under-trigger even though Phase 4 supports it | Add eval-specific trigger words to description and examples |
| "Review my MCP server for best-practice compliance" | Users may not discover this skill for audits or design review | Add review/audit wording and best-practice cues to metadata |

## Chain And Parallel Opportunities

| Request Pattern | Relation | Recommendation |
|-----------------|----------|----------------|
| API research -> implementation -> evaluation | `chain` | Keep as one skill with internal phase dispatch |
| TypeScript guide vs Python guide | `exclusive branch` | Route by language choice after skill selection |
| Best-practices review plus eval creation | `chain` | Review first, then create evals |

## Priority Fixes

1. Expand `mcp-builder` metadata so "review MCP server" and "create MCP evals" are first-class triggers.
2. Make the internal intent dispatch visible near the top of the skill, instead of burying phases deep in the body.
3. Keep `reference/` and `scripts/` explicitly non-routable so the package is not mistaken for a multi-skill system.
