---
name: skill-machine-instruction-analysis
description: |
  Refactor SKILLs by converting descriptive tasks to machine instructions. 
  Identifies deterministic operations vs LLM reasoning tasks and restructures accordingly.
  Use when: "refactor this skill", "convert to machine instructions", "which steps can be scripted",
  "optimize skill execution", "analyze skill determinism".
---

# SKILL Machine Instruction Refactorer

Convert descriptive tasks into executable instructions.

```
Uncertain → LLM
Certain → Code / Script / Tool
```

## Procedure

Load and execute the refactor workflow:

<action tool="read_file">
workflows/refactor-workflow.md
</action>

## Quick Reference

- **Conversion rules**: `knowledge/conversion-rules.md`
- **Analysis format**: `templates/analysis-schema.json`
- **Output structure**: `templates/refactored-skill.md`
