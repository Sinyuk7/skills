# skill-trigger-router-optimizer

Meta-skill for auditing and redesigning skill routing.

It focuses on:

- when a skill should trigger
- when a component should not be routable at all
- where boundaries overlap or leave gaps
- whether supported intents are buried too deep to trigger reliably
- how to turn routing decisions into policies and evals

## Sample Coverage

The `examples/` directory captures three different routing failure modes that shaped this skill.

### 1. `issue-flow-system`

Validated that the optimizer can distinguish:

- user-facing stage skills
- shared core packages
- plugin skills
- chain relationships between stages

Main lesson:
`issue-flow-core` must stay a shared core, not a routed skill.

### 2. `mcp-builder-sample`

Validated that the optimizer can detect:

- one routed skill with many bundled references
- hidden secondary intents inside a long skill body
- under-trigger risk caused by build-heavy metadata

Main lesson:
`mcp-builder` supports review and eval intents, but they were too buried in the route surface.

### 3. `openspec-explore-sample`

Validated that the optimizer can recognize:

- stance-driven or mode-switch skills
- behavioral boundaries as routing boundaries
- legitimate skills that do not look workflow-heavy

Main lesson:
`openspec-explore` is a real routed skill, but its core product is exploration mode, not a fixed workflow.

## Regression Baseline

Use [evals/evals.json](/Users/shenyeke01/Documents/Workspace/skills/skills/skill-trigger-router-optimizer/evals/evals.json) as the regression set for:

- shared-core vs routable classification
- hidden secondary intent detection
- stance-driven skill recognition

## Directory Map

```text
skill-trigger-router-optimizer/
├── SKILL.md
├── README.md
├── workflows/
├── knowledge/
├── templates/
├── evals/
└── examples/
```
