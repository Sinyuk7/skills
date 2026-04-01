# Conversion Rules

Rules for classifying and converting SKILL steps to machine instructions.

---

## Core Principle

```
简单 IO → 隐式（LLM handles）
复杂流程 → 显式（workflow/script）
推理任务 → LLM
机械操作 → tool/script
```

---

## Classification Criteria

### Deterministic ✅

```
Given input I → Always produces output O (no reasoning required)
```

**Indicators:**
- File read/write/list
- String matching (exact)
- Template filling
- Conditional routing (explicit)
- Data format conversion

**Keywords:** read, load, check, find, list, create, copy, move, delete, replace, validate

### LLM Reasoning ❌

```
Output depends on understanding, judgment, or creativity
```

**Indicators:**
- Semantic understanding
- Logical deduction
- Creative generation
- Fuzzy interpretation
- Context-dependent decisions

**Keywords:** analyze, understand, infer, suggest, explain, evaluate, summarize, judge

### Hybrid 🟡

Split into: deterministic (collect) → LLM (process)

**Pattern:** "Read X then analyze" → 
1. Collect content (deterministic)
2. LLM analyzes (reasoning)

---

## How to Write Tool Calls

### ❌ Wrong: Pseudo Code

```python
files = list_files_recursive("./")
source_files = filter(files, "*.ts")
for f in source_files:
    content = read_file(f)
```

LLM won't execute this. It adds tokens and confusion.

### ✅ Correct: Natural Language + Tool Name

**Option 1: Explicit tool reference**
```markdown
Use tool: list_files_recursive
Input: "./"
```

**Option 2: Natural instruction (for simple IO)**
```markdown
List all files recursively in the project directory.
Filter for: *.ts, *.controller.*, *.routes.*
```

### Complexity Rule

| Complexity | Approach |
|------------|----------|
| Single-step IO | Natural language, LLM handles implicitly |
| Multi-step pipeline | Explicit workflow steps or script |
| Reasoning | LLM instruction |
| Mechanical batch | Script/tool |

---

## Data Flow Pattern

### ❌ Wrong: Mixed grep + LLM parse

```markdown
Step 3: grep for @Get, @Post decorators
Step 4: LLM extracts endpoint info from grep results
```

Boundary unclear: LLM confused about what data to use.

### ✅ Correct: Collect → Parse

```markdown
Step 3 (Deterministic): Collect file contents
  Read all controller files found in Step 2.

Step 4 (LLM): Parse endpoints
  From the file contents, extract:
  - HTTP method
  - Path
  - Parameters
  - Description
```

---

## Ideal Step Structure

Minimize LLM context switches:

```
D: Collect files
D: Collect contents
L: Parse/Extract (single LLM pass)
D: Validate
L: Generate output (single LLM pass)
D: Write files
```

Not:
```
D-D-D-L-D-L-D-L-D  (too fragmented)
```

---

## Script Generation Guidelines

### When to Create Scripts

| Condition | Action |
|-----------|--------|
| Single file read/write | Natural language, no script |
| Find + filter + read multiple files | Generate `scripts/collect-*.sh` |
| Complex validation rules | Generate `schemas/*.json` |
| Reusable transformation | Generate `tools/*.ts` or `tools/*.py` |
| Batch operations with loops | Generate script |

### Script Naming Convention

```
scripts/
├── collect-{resource}.sh      # File collection
├── validate-{type}.py         # Validation logic
├── transform-{format}.py      # Data transformation
└── generate-{output}.sh       # Output generation

tools/
├── {action}-{target}.ts       # Reusable tools

schemas/
└── {entity}.schema.json       # Validation schemas
```

### How to Reference Scripts in SKILL.md

```markdown
### Step N: {Name} (Deterministic)

Run script: ./scripts/collect-source-files.sh
Input: project root directory
Output: list of source files matching patterns

Then read each file from the output list.
```

### Script Template (Shell)

```bash
#!/bin/bash
# scripts/collect-source-files.sh
# Purpose: Collect TypeScript source files

find "$1" -type f \( -name "*.ts" -o -name "*.controller.ts" \) \
  | grep -v node_modules \
  | sort
```

### Script Template (Python)

```python
#!/usr/bin/env python3
# scripts/validate-endpoints.py

import sys
import json

def validate(endpoints):
    errors = []
    for ep in endpoints:
        if not ep.get("method"):
            errors.append(f"Missing method: {ep}")
        if not ep.get("path", "").startswith("/"):
            errors.append(f"Invalid path: {ep}")
    return {"valid": len(errors) == 0, "errors": errors}

if __name__ == "__main__":
    data = json.load(sys.stdin)
    print(json.dumps(validate(data)))
```

---

## Anti-Patterns

### Implicit File Reference

```markdown
# ❌ Wrong
If needed, see docs/guide.md

# ✅ Correct
Read the guide document: docs/guide.md
```

### Shell Commands (Risky)

```markdown
# ❌ Risky
run_terminal_cmd("mkdir -p ./docs")

# ✅ Safer
Ensure directory exists: ./docs
Create directory if missing: ./docs
```

### Process Description (not Execution)

```markdown
# ❌ Wrong
1. First check input
2. Then validate
3. Finally output

# ✅ Correct
Step 1 (Deterministic): Validate input format
  Check that input contains required fields.

Step 2 (Deterministic): Write output
  Save result to output.json
```