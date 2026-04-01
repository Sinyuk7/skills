# Evidence Chain Design

## Core Flow

```
Load → Proof → Answer
```

## Proof Format

Single line, minimal tokens:

```markdown
<proof file="X.md" lines="N-M" preview="First 20 chars..." />
```

| Field | Purpose |
|-------|---------|
| `file` | Which file was read |
| `lines` | Which lines are relevant |
| `preview` | First ~20 chars to prove read (not full content) |

## Document Isolation

SKILL.md: paths only, no content descriptions.

## Evaluation Checklist

| Has This? | Needs Transform |
|-----------|-----------------|
| `knowledge/` dir | Yes |
| Content in Quick Ref | Yes |
| No `<proof>` tags | Yes |
| No `<final>` tags | Yes |

## State Machine

```
[Load] → [Proof] → [Final]
```

No proof = cannot proceed.
