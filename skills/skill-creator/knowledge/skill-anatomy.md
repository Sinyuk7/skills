# Skill Anatomy

Use this note when drafting or restructuring a skill.

## Directory structure

```text
skill-name/
├── SKILL.md
└── Bundled resources
    ├── scripts/
    ├── references/
    └── assets/
```

Router-style skills may also add intermediate layers such as:

- `knowledge/`
- `workflows/`
- `templates/`

Use extra structure when it keeps the main `SKILL.md` readable and makes follow-up loading more targeted.

## Progressive disclosure

Skills naturally operate in layers:

1. Metadata in frontmatter
2. `SKILL.md` body when the skill triggers
3. Bundled resources loaded only when needed

Guidelines:

- Keep `SKILL.md` reasonably compact.
- If the body is getting too long, split it and provide clear routing instructions.
- Reference bundled files explicitly and explain when to open them.
- For very large references, add lightweight navigation.

## Frontmatter guidance

Required fields:

- `name`
- `description`

Description guidance:

- Say what the skill does.
- Say when it should trigger.
- Include adjacent situations where it should still be used.
- Be slightly assertive so the skill does not under-trigger.

## Writing patterns

Prefer imperative instructions.

Use examples when they clarify intent.

Define output formats explicitly when structure matters.

Explain why a step matters instead of relying on rigid phrasing whenever possible.

## Safety

Follow the principle of lack of surprise:

- do not create misleading or malicious skills
- do not hide behavior the user would not expect from the description
- do not facilitate unauthorized access, exfiltration, or abuse
