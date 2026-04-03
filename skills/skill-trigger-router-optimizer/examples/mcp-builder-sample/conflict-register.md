# Conflict Register

## Active Conflicts

| Conflict ID | Intent Region | Skills | Symptom | Arbitration Rule | Status |
|-------------|---------------|--------|---------|------------------|--------|
| `mcp-001` | Build MCP server vs create MCP evals | `mcp-builder` internal intents | Eval requests may under-trigger because description is build-heavy | Keep one skill, strengthen eval trigger surface | `active` |
| `mcp-002` | Build MCP server vs review MCP design | `mcp-builder` internal intents | Audit/review requests may not map cleanly to "builder" wording | Add review/audit cues to metadata | `active` |

## Unresolved Risks

| Risk | Impact | Proposed Fix | Owner | Next Check |
|------|--------|--------------|-------|------------|
| Monolithic skill body hides phase-level entrypoints | Under-trigger for secondary intents | Add top-level intent dispatch section | mcp-builder maintainers | next metadata pass |
| Bundled references may be mistaken for route targets by package-level analyzers | Noisy audit output | Preserve explicit non-routable role classification | router optimizer | next sample run |

## Recently Resolved

| Conflict ID | Resolution | Evidence |
|-------------|------------|----------|
| None yet | N/A | Sample audit only |
