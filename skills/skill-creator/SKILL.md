---
name: skill-creator
description: Create new skills, modify and improve existing skills, and measure skill performance. Use when users want to create a skill from scratch, edit, or optimize an existing skill, run evals to test a skill, benchmark skill performance with variance analysis, or optimize a skill's description for better triggering accuracy.
---

# Skill Creator

A skill for creating new skills and iteratively improving them.

At a high level, the process of creating a skill goes like this:

- Decide what you want the skill to do and roughly how it should do it.
- Write a draft of the skill.
- Create a few test prompts and run Claude-with-access-to-the-skill on them.
- Help the user evaluate the results both qualitatively and quantitatively.
- Rewrite the skill based on feedback from the user's evaluation of the results.
- Repeat until you're satisfied.
- After the skill is in good shape, optimize the description for better triggering accuracy if useful.

Your job is to figure out where the user is in that process and jump in at the right stage. Be flexible: if the user wants a lightweight, collaborative pass instead of a full eval loop, adapt.

## Intent Dispatch

Identify the user's intent, then load the corresponding workflow.

| User Intent | Load |
|-------------|------|
| Create a new skill or modify an existing skill | `workflows/skill-drafting.md` |
| Run tests, review outputs, benchmark, or iterate on a draft | `workflows/evaluation-loop.md` |
| Optimize a skill description for triggering accuracy | `workflows/description-optimization.md` |

If the user is moving through multiple stages in one session, start with the workflow that matches their immediate need, then load the next one when they are ready.

## Communication Style

Adapt to the user's technical level.

- "Evaluation" and "benchmark" are usually fine.
- For terms like "JSON" and "assertion", look for cues that the user is comfortable with them before using them without explanation.
- Briefly explain technical terms when in doubt.

## Execution Rules

1. Use this file as a router, not as the full procedure.
2. Load the relevant workflow before executing detailed steps.
3. Pull in additional knowledge, templates, references, agents, or scripts only when the workflow says they are needed.
4. Preserve official bundled dependencies as the source of truth unless the user explicitly asks to change them.

## Fallback

If the user's intent is ambiguous, clarify whether they want to:

1. Create or edit a skill.
2. Run an evaluation and improvement loop.
3. Optimize a description for triggering.

## Directory Guide

```text
skill-creator/
├── SKILL.md
├── workflows/
├── knowledge/
├── templates/
├── agents/
├── references/
├── scripts/
├── eval-viewer/
└── assets/
```

## Quick Reference

- For skill writing guidance, load `knowledge/skill-anatomy.md`.
- For iteration and revision guidance, load `knowledge/improvement-guide.md`.
- For environment-specific adaptations, load `knowledge/environment-notes.md`.
- For grading instructions, load `agents/grader.md`.
- For blind comparisons, load `agents/comparator.md` and `agents/analyzer.md`.
- For JSON schemas, prefer `references/schemas.md`. `templates/schemas.md` is a convenience pointer.
