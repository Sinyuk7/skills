# Analysis Workflow

Evaluate if a SKILL needs evidence-chain transformation.

---

## Step 1: Load Target

<action tool="read_file">
[target SKILL.md path]
</action>

<action tool="list_files_recursive">
[target SKILL directory]
</action>

---

## Step 2: Load Evaluation Criteria

<action tool="read_file">
knowledge/evidence-chain-design.md
</action>

<proof file="evidence-chain-design.md">
[Quote the Evaluation Checklist section]
</proof>

---

## Step 3: Evaluate

Check each item:

| Check | Result | Evidence |
|-------|--------|----------|
| Has document directories | [Yes/No] | [list dirs found] |
| Quick Reference leaks content | [Yes/No] | [quote if found] |
| No `<proof>` tags | [Yes/No] | [confirm absence] |
| No structural constraints | [Yes/No] | [describe] |

---

## Step 4: Report

<final>

## Evaluation: [SKILL name]

**Needs transformation**: [Yes/No/Partial]

### Issues Found
1. [issue]
2. [issue]

### Files to Modify
- `SKILL.md`: [changes]
- `workflows/X.md`: [changes]

</final>

---

## Step 5: Next Action

Ask user: Proceed with transformation?

If yes:
<action tool="read_file">
workflows/transformation.md
</action>
