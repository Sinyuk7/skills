# Refactor Workflow

Complete procedure for refactoring a SKILL to machine instruction form.

---

## Step 1: Load Target SKILL

```
target_path = user_specified_path OR ask_user("Which SKILL to refactor?")
skill_content = read_file("{target_path}/SKILL.md")
```

If SKILL.md doesn't exist, inform user and abort.

---

## Step 2: Load Conversion Rules

<action tool="read_file">
knowledge/conversion-rules.md
</action>

---

## Step 3: Classify Each Step

For each step in the target SKILL, apply classification rules.

Output as structured JSON (do NOT generate human report):

<action tool="read_file">
templates/analysis-schema.json
</action>

```json
{
  "steps": [
    {"id": 1, "classification": "deterministic|llm|hybrid", "description": "..."},
    ...
  ]
}
```

**Classification only, no conversion yet.**

---

## Step 4: Refactor Based on Classification

For each classified step:

| Classification | Action |
|----------------|--------|
| `deterministic` | Convert to tool call, code block, OR generate script |
| `llm` | Keep as reasoning instruction, ensure context is provided |
| `hybrid` | Split into deterministic (first) + llm (second) |

### When to Generate Scripts

| Scenario | Approach |
|----------|----------|
| Single-step simple IO | Natural language (LLM handles implicitly) |
| Multi-step mechanical pipeline | Generate script to `scripts/` |
| Complex filtering/iteration | Generate script to `scripts/` |
| Data validation logic | Generate schema to `schemas/` |
| Reusable utility | Generate tool to `tools/` |

### Script Generation Criteria

Generate an independent script file when the step involves:
- Multiple sub-operations (e.g., find files → filter → read each)
- Loop/iteration logic
- Complex data transformation
- Validation that can be formalized

### Directory Convention

```
{skill}/
├── scripts/      # Shell/Python for batch operations
├── tools/        # Reusable tool implementations  
└── schemas/      # JSON schemas for validation
```

### Conversion Examples

**Simple IO → Natural language:**
```markdown
Read the configuration file: ./config.json
```

**Multi-step pipeline → Generate script:**
```markdown
Run script: ./scripts/collect-source-files.sh
Input: project root directory
Output: list of controller and route files
```

**Validation → Generate schema:**
```markdown
Validate endpoints against: ./schemas/endpoint.schema.json
```

---

## Step 5: Generate Refactored SKILL

<action tool="read_file">
templates/refactored-skill.md
</action>

Output the refactored SKILL.md following the template structure.

Key requirements:
- Mark each step: `(Deterministic)` or `(LLM)`
- Use code blocks for all deterministic operations
- All file paths must be explicit
- Keep SKILL.md under 100 lines (router style) or 500 lines (execution style)

---

## Step 6: Present to User

Show:
1. Summary of changes (counts by classification)
2. Refactored SKILL.md content

Ask if adjustments needed.
