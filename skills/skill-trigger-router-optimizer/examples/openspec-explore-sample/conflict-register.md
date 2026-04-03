# Conflict Register

## Active Conflicts

| Conflict ID | Intent Region | Skills | Symptom | Arbitration Rule | Status |
|-------------|---------------|--------|---------|------------------|--------|
| `osex-001` | General exploration vs implementation | `openspec-explore` and execution-oriented skills | Broad investigation language may blur the boundary | If the user wants thinking without code changes, prefer `openspec-explore` | `active` |
| `osex-002` | Exploration vs artifact drafting | `openspec-explore` and drafting-style skills | Artifact capture may be mistaken as required output | Keep capture optional and user-directed | `active` |

## Unresolved Risks

| Risk | Impact | Proposed Fix | Owner | Next Check |
|------|--------|--------------|-------|------------|
| Mode-switch nature is body-heavy | Under-trigger when users ask indirectly for non-implementation discussion | Move mode-switch cues into top metadata | openspec-explore maintainers | next metadata pass |
| Workflowless skill may be mis-scored by generic routers | Router may infer it is underspecified | Treat stance-driven skills as valid route targets | router optimizer | next sample run |

## Recently Resolved

| Conflict ID | Resolution | Evidence |
|-------------|------------|----------|
| None yet | N/A | Sample audit only |
