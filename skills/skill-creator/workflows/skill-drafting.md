# Skill Drafting Workflow

Use this workflow when the user wants to create a new skill, capture an existing workflow as a skill, or edit a skill before evaluation.

## Step 1: Understand the request

Start by understanding what the skill should do. If the conversation already contains the workflow to capture, extract as much as you can from context first:

- tools used
- step ordering
- corrections the user made
- expected inputs and outputs

Fill any remaining gaps with targeted questions. Confirm before moving on when the intent is still fuzzy.

Core questions:

1. What should this skill enable Claude to do?
2. When should this skill trigger?
3. What output format should it produce?
4. Should we create test cases now?

Default recommendation:

- Use test cases for objectively checkable skills such as file transforms, data extraction, code generation, or fixed workflows.
- Skip or defer formal test cases for highly subjective skills unless the user wants them.

## Step 2: Interview and research

Proactively ask about:

- edge cases
- example files
- success criteria
- dependencies
- failure modes

If outside context would help, research in parallel when the environment supports it so the user does not need to provide everything manually.

Before writing, load:

- `knowledge/skill-anatomy.md`
- `templates/skill-template.md`

## Step 3: Draft or update the skill

Write the skill based on the interview.

Frontmatter:

- `name`: stable skill identifier
- `description`: what it does and when to use it
- `compatibility`: only if genuinely needed

Description guidance:

- Put triggering guidance in the description, not buried in the body.
- Be slightly "pushy" to counter under-triggering.
- Mention adjacent phrasings and situations where the skill should still be used even if the user does not name it explicitly.

Body guidance:

- Prefer imperative instructions.
- Explain why important steps matter instead of relying on rigid wording.
- Keep the skill generalizable rather than tuned only for one example.
- Reference bundled resources clearly and tell the model when to read them.

## Step 4: Create test prompts

After drafting, create 2-3 realistic prompts that a real user might say.

Share the prompts with the user for a quick sanity check when appropriate.

Before writing eval files, load:

- `templates/evals-template.json`
- `references/schemas.md`

Save prompts to `evals/evals.json`. Do not write assertions yet unless the skill already has a solid existing eval set.

## Step 5: Set up files

Create or update the skill directory and write:

- `SKILL.md`
- `evals/evals.json` when using test prompts

Preserve the original name when updating an existing installed skill.

If the skill lives in a read-only location, follow the writable-copy guidance in `knowledge/environment-notes.md`.

## Next Move

Once the draft is ready, load `workflows/evaluation-loop.md` to run the test, review, and iteration cycle.
