# Transformation Workflow

Execute evidence-chain transformation on a SKILL.

---

## Step 1: Load Templates

<action tool="read_file">
templates/evidence-structure.md
</action>

<proof file="evidence-structure.md">
[Quote the tag templates]
</proof>

---

## Step 2: Plan Changes

Based on analysis report, list modifications:

```
Files to modify:
- SKILL.md: [specific changes]
- workflows/X.md: [specific changes]
```

Present plan to user. Wait for confirmation.

---

## Step 3: Transform SKILL.md

### 3.1 Apply Content Isolation

Replace content-describing references with path-only:

Before:
```markdown
- `file.md` - Contains X, Y, Z
```

After:
```markdown
- `file.md` - Load when needed
```

### 3.2 No PUA Headers

Do NOT add:
- Warning blocks
- Priority declarations  
- Mandatory rules lists

The structure is the constraint.

---

## Step 4: Transform Workflows

For each workflow that reads documents:

### 4.1 Add Proof Requirement

After every `<action tool="read_file">`:

```markdown
<proof file="[path]" lines="X-Y">
[verbatim quote]
</proof>
```

### 4.2 Add Final Tag

Wrap output in:

```markdown
<final>
[response grounded in proof]
</final>
```

---

## Step 5: Apply Changes

Execute modifications using edit_file.

---

## Step 6: Verify

Check transformed SKILL has:
- [ ] Path-only references
- [ ] `<proof>` after each document read
- [ ] `<final>` for outputs
- [ ] No PUA text

<final>

## Transformation Complete

Files modified:
- [list]

Structure added:
- `<proof>` tags: [count]
- `<final>` tags: [count]

</final>
