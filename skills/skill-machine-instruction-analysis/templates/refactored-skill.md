# Refactored SKILL Template

Use this structure for output stability.

---

## Frontmatter

```yaml
---
name: {skill-name}
description: |
  {What the skill does and when to use it.}
---
```

## Body Structure

```markdown
# {Skill Name}

{Brief overview - 1-2 sentences max}

## Procedure

### Step 1: {Name} (Deterministic)

{Simple IO: natural language}

Example:
  Read the configuration file: ./config/api-docs.json
  If not found, use default settings.

### Step 2: {Name} (Deterministic)

{Multi-step pipeline: reference script}

Example:
  Run script: ./scripts/collect-source-files.sh
  Input: project root directory
  Output: list of controller and route files

  Then read each file from the output list.

### Step 3: {Name} (LLM)

{Reasoning task with clear context and expected output}

Example:
  From the collected file contents, extract endpoint information:
  - HTTP method
  - Route path
  - Parameters
  - Description from JSDoc

  Output as structured JSON.

### Step 4: {Name} (Deterministic)

{Validation: reference schema}

Example:
  Validate extracted endpoints against: ./schemas/endpoint.schema.json

### Step 5: {Name} (Deterministic)

{Write/output operation}

Example:
  Ensure directory exists: ./docs
  Write output to: ./docs/api-reference.md

## Quick Reference

- **{Resource}**: `{path}`
```

## Generated Files Structure

When refactoring produces scripts/schemas:

```
{skill}/
├── SKILL.md
├── scripts/
│   └── collect-source-files.sh
├── schemas/
│   └── endpoint.schema.json
└── tools/
    └── (if reusable tools needed)
```

## Rules

### Step Labeling
- Mark every step: `(Deterministic)` or `(LLM)`

### Deterministic Steps
- Use natural language for simple IO
- No pseudo code, no variable assignments
- LLM will handle implicitly

### LLM Steps
- Specify input context clearly
- Define expected output format
- One reasoning task per step

### File Operations
- All paths explicit and relative
- No shell commands, use abstract operations

### Size Limits
- Router-style: <100 lines
- Execution-style: <500 lines

---

## Ideal Flow Pattern

```
D: Collect files/data
D: Collect contents
L: Parse/Extract (single pass)
D: Validate (if needed)
L: Generate output (single pass)
D: Write output
```

Minimize LLM context switches.