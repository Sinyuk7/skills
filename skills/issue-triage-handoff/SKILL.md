---
name: issue-triage-handoff
description: Compress raw troubleshooting materials into a standardized handoff package for downstream RCA/fix agents. Use when you have scattered issue content, comments, chat logs, log directories/archives, and a codebase that need to be organized into a structured, evidence-backed, boundary-clear handoff. Also use for "triage this issue", "prepare handoff", "organize debugging materials", or "what do we know about this bug".
---

# Issue Triage Handoff

A skill for transforming chaotic troubleshooting materials into clean, structured handoff packages.

This skill does NOT:
- Confirm root cause
- Generate code patches
- Output complete fix solutions
- Replace observability platforms

It DOES:
- Compress context noise
- Filter high-value evidence from large log directories
- Map code locations based on evidence
- Produce stable, traceable handoff packages

## Intent Dispatch

Identify the user's intent, then load the corresponding workflow.

| User Intent | Load |
|-------------|------|
| Create a new handoff from raw materials | `workflows/new-triage-handoff.md` |
| Refine an existing handoff with new evidence | `workflows/handoff-refinement.md` |
| Evaluate whether a handoff is ready for downstream agents | `workflows/handoff-evaluation.md` |

If the user is moving through multiple stages in one session, start with the workflow that matches their immediate need, then load the next one when ready.

## Quick Reference

- For handoff output structure, load `knowledge/handoff-schema.md`
- For evidence referencing rules, load `knowledge/evidence-protocol.md`
- For core triage principles, load `knowledge/triage-principles.md`
- For output template, load `templates/handoff-template.json`

## Execution Rules

1. Use this file as a router, not as the full procedure
2. Load the relevant workflow before executing detailed steps
3. Pull in knowledge, templates, references only when the workflow requires them
4. Always distinguish facts from inferences from open questions
5. Evidence from logs/code/traces has higher weight than human narrative

## Fallback

If the user's intent is ambiguous, clarify whether they want to:

1. Create a new handoff from raw materials
2. Update an existing handoff with new information
3. Evaluate handoff quality and completeness

## Directory Guide

```text
issue-triage-handoff/
├── SKILL.md
├── workflows/
│   ├── new-triage-handoff.md
│   ├── handoff-refinement.md
│   └── handoff-evaluation.md
├── knowledge/
│   ├── handoff-schema.md
│   ├── evidence-protocol.md
│   └── triage-principles.md
├── templates/
│   └── handoff-template.json
├── references/
├── scripts/
├── assets/
└── evals/
```
