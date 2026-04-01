---
name: skill-evidence-transformer
description: |
  Transform SKILLs into evidence-chain execution mode.
  Trigger: "evidence chain", "add proof tags", "证据链化", "refine skill for grounding".
---

# Skill Evidence Transformer

Transform SKILL execution from `Answer → Evidence` to `Evidence → Answer`.

## Intent Dispatch

| Intent | Workflow |
|--------|----------|
| Analyze if SKILL needs transformation | `workflows/analysis.md` |
| Execute transformation | `workflows/transformation.md` |

## Execution

1. Identify intent from user request
2. Load corresponding workflow via `read_file`
3. Execute workflow steps

## Resources

- `knowledge/evidence-chain-design.md` - Core principles
- `templates/evidence-structure.md` - XML tag templates
```